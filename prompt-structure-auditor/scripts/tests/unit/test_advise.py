"""Unit tests for PSA Advise (Release 5)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from psa.advise.brief import build_advise_brief
from psa.advise.bridge import BRIDGE_MISSING_MSG, obtain_judgment
from psa.advise.engine import run_advise
from psa.advise.persist import load_advise
from psa.advise.schema import AdviseJudgment
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.report.advise_view import format_apply_advise_line, render_advise
from tests.conftest import FIXTURES


def test_brief_includes_catalog_and_principles():
    fs = LocalRepoFS(FIXTURES / "order_apply")
    audit = analyze(fs, tool_version="1.0.0")
    brief = build_advise_brief(audit, repo_name="order_apply", repo=fs)
    assert brief["schema"] == "psa.advise.brief.v1"
    assert any(p["id"] == "stable-before-volatile" for p in brief["principles"])
    ids = {r["id"] for r in brief["rule_catalog"]}
    assert "ORDER001" in ids
    assert "do_not_restate" in brief


def test_judgment_parses_conflict_alias():
    j = AdviseJudgment.from_dict(
        {
            "summary_theme": "Theme",
            "items": [
                {"kind": "investigate", "title": "Conflict case", "paths": ["AGENTS.md"]}
            ],
        }
    )
    assert len(j.conflict_items()) == 1
    assert j.conflict_items()[0].kind == "conflict"


def test_render_advise_plan_shape():
    judgment = AdviseJudgment.from_dict(
        json.loads((FIXTURES / "advise_judgment.json").read_text(encoding="utf-8"))
    )
    text = render_advise(judgment, repo_name="demo")
    assert text.startswith("Prompt Structure Advise")
    assert "Advisory Recommendations" in text
    assert "Investigation Points" in text
    assert "conflict" in text
    assert "Promote promising ones" in text


def test_format_apply_one_liner():
    line = format_apply_advise_line(
        "Possible missing activation clarity in .cursor/rules"
    )
    assert line.endswith("- run psa advise")
    assert "activation clarity" in line


def test_run_advise_requires_bridge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    demo = tmp_path / "repo"
    demo.mkdir()
    (demo / "AGENTS.md").write_text("# Role\nStable.\n", encoding="utf-8")
    monkeypatch.delenv("PSA_ADVISE_CMD", raising=False)
    monkeypatch.delenv("PSA_ADVISE_JUDGMENT", raising=False)
    # Force tty-like stdin so bridge is unavailable
    result = run_advise(demo, consider_stdin=False)
    assert result.exit_code == 2
    assert BRIDGE_MISSING_MSG in result.error


def test_run_advise_with_judgment_file(tmp_path: Path):
    src = FIXTURES / "order_apply"
    demo = tmp_path / "repo"
    import shutil

    shutil.copytree(src, demo)
    judgment = FIXTURES / "advise_judgment.json"
    result = run_advise(demo, judgment_path=judgment, consider_stdin=False)
    assert result.exit_code == 0
    assert "Prompt Structure Advise" in result.report
    assert "Clarify when Cursor rules" in result.report
    snap = load_advise(demo)
    assert snap is not None
    assert len(snap.items) == 2
    assert (demo / ".psa" / "advise.json").is_file()


def test_obtain_judgment_from_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    judgment = FIXTURES / "advise_judgment.json"
    monkeypatch.setenv("PSA_ADVISE_JUDGMENT", str(judgment))
    j = obtain_judgment({}, consider_stdin=False)
    assert j.summary_theme.startswith("Possible missing")


def test_brief_only(tmp_path: Path):
    demo = tmp_path / "repo"
    demo.mkdir()
    (demo / "AGENTS.md").write_text("# Role\n", encoding="utf-8")
    result = run_advise(demo, brief_only=True, consider_stdin=False)
    assert result.exit_code == 0
    assert result.brief["repository"]
    assert result.report == ""
