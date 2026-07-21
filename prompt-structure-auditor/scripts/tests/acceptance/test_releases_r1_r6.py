"""Release acceptance R1–R6 against fixtures + live IdeaProjects repos.

Every present target (fixtures always; live when on disk) is exercised so the
public audit format stays identical across repository runs. Later releases may
append behaviour but must not reshape the frozen R1 audit report.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.patch.generate import preview_patch
from psa.patch.validate import validate_patch
from psa.report.audit_view import render_audit
from tests.conftest import (
    ALL_TARGETS,
    FIXTURES,
    LIVE_VR1,
    LIVE_VR2,
    LIVE_VR3,
    present_targets,
)
from tests.contract import assert_frozen_audit_structure, normalized_audit_structure

SCRIPTS = Path(__file__).resolve().parents[2]
FABRICATED = ("score", "hit_rate", "latency", "cost", "token_saving", "token_savings", "cache_score")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PSA_ADVISE_CMD", None)
    env.pop("PSA_ADVISE_JUDGMENT", None)
    env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
    env["PSA_NONINTERACTIVE"] = "1"
    return env


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "psa", *args],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        env=_env(),
        check=False,
    )


def _rule_ids(audit) -> set[str]:
    return {f.rule_id for f in audit.findings}


@pytest.fixture(params=present_targets(), ids=lambda t: t[0])
def target(request) -> tuple[str, Path, bool]:
    return request.param


# ---------------------------------------------------------------------------
# Cross-target format lock (all releases depend on this)
# ---------------------------------------------------------------------------


class TestFormatConsistency:
    def test_all_present_targets_share_identical_audit_structure(self):
        present = present_targets()
        assert any(not live for _, _, live in present), "fixtures must be present"
        structures: dict[str, str] = {}
        for name, path, _ in present:
            text = render_audit(
                analyze(LocalRepoFS(path), tool_version="0.1.0"),
                repo_name=path.name,
            )
            assert_frozen_audit_structure(text, name)
            structures[name] = normalized_audit_structure(text)
        canonical = next(iter(structures.values()))
        for name, block in structures.items():
            assert block == canonical, (
                f"{name} audit structure diverged from suite canonical form:\n{block}"
            )

    def test_cli_audit_matches_render_contract(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("audit", str(path))
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        assert_frozen_audit_structure(proc.stdout, name)
        assert proc.stdout.encode("ascii")


# ---------------------------------------------------------------------------
# R1 — Audit
# ---------------------------------------------------------------------------


class TestRelease1Audit:
    def test_r1_doctor_cli(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("doctor", str(path))
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        assert "Doctor" in proc.stdout
        assert "Instruction Sources" in proc.stdout

    def test_r1_audit_text_frozen(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        text = render_audit(analyze(LocalRepoFS(path), tool_version="0.1.0"), repo_name=name)
        assert_frozen_audit_structure(text, name)

    def test_r1_audit_json_shape_no_fabricated(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("audit", str(path), "--format", "json")
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        data = json.loads(proc.stdout)
        for key in ("meta", "inventory", "findings", "dependency_graph", "guidance"):
            assert key in data, f"{name} missing {key}"

        def _walk_keys(obj) -> set[str]:
            keys: set[str] = set()
            if isinstance(obj, dict):
                keys.update(obj.keys())
                for v in obj.values():
                    keys |= _walk_keys(v)
            elif isinstance(obj, list):
                for v in obj:
                    keys |= _walk_keys(v)
            return keys

        keys_lower = {k.lower() for k in _walk_keys(data)}
        for bad in FABRICATED:
            assert bad not in keys_lower, f"{name} leaked fabricated metric key: {bad}"

    def test_r1_vr1_honest_empty(self):
        for name, path in (("VR1_fixture", FIXTURES / "vr1_empty"), ("VR1_live", LIVE_VR1)):
            if not path.is_dir():
                continue
            audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
            assert audit.findings == (), f"{name} must not fabricate findings"
            assert "ORDER001" not in _rule_ids(audit)

    def test_r1_vr2_activation_surface(self):
        for name, path in (("VR2_fixture", FIXTURES / "vr2_latetrain"), ("VR2_live", LIVE_VR2)):
            if not path.is_dir():
                continue
            ids = _rule_ids(analyze(LocalRepoFS(path), tool_version="0.1.0"))
            assert "ACT001" in ids, name
            assert "ACT002" in ids, name
            assert "ORDER001" not in ids, name

    def test_r1_vr3_fixture_order_style_dup(self):
        path = FIXTURES / "vr3_demo"
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        ids = _rule_ids(audit)
        assert "ORDER001" in ids and "STYLE001" in ids and "DUP001" in ids
        order_titles = [f.title for f in audit.findings if f.rule_id == "ORDER001"]
        assert any("Current Focus" in t for t in order_titles)
        assert not any(
            "On Hold" in t or "Debugging" in t or "Known Issue" in t for t in order_titles
        )

    def test_r1_vr3_live_finance_tracker_healthy(self):
        if not LIVE_VR3.is_dir():
            pytest.skip("VR3 live missing")
        audit = analyze(LocalRepoFS(LIVE_VR3), tool_version="0.1.0")
        text = render_audit(audit, repo_name=LIVE_VR3.name)
        assert_frozen_audit_structure(text, "VR3_live")
        assert audit.findings == ()
        assert "Healthy" in text


# ---------------------------------------------------------------------------
# R2 — Prioritise (must not break R1 audit format)
# ---------------------------------------------------------------------------


class TestRelease2Plan:
    def test_r2_audit_stays_factual(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        text = render_audit(analyze(LocalRepoFS(path), tool_version="0.1.0"), repo_name=name)
        assert_frozen_audit_structure(text, name)
        assert "Recommended Plan" not in text
        assert "Recommendation Details" not in text

    def test_r2_plan_cli_frozen_contract(self, target: tuple[str, Path, bool]):
        from tests.contract_plan import assert_frozen_plan_structure

        name, path, _ = target
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        proc = _cli("plan", str(path))
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        assert_frozen_plan_structure(proc.stdout, name)
        if not audit.findings:
            assert "No action needed" in proc.stdout, name
            assert "Already Healthy" in proc.stdout, name
        else:
            assert "Plan ready" in proc.stdout, name
            assert "Why now" in proc.stdout, name
            assert "Expected end state" in proc.stdout, name
            assert "Unblocks" not in proc.stdout, name

    def test_r2_plan_json(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("plan", str(path), "--format", "json")
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        data = json.loads(proc.stdout)
        assert "plan" in data
        assert "findings_considered" in data
        for step in data["plan"]:
            for key in (
                "why_now",
                "unblocks",
                "remaining_after",
                "estimated_effort",
                "depends_on",
                "findings",
            ):
                assert key in step, f"{name} plan step missing {key}"

    def test_r2_vr3_dependencies_order_in_plan(self):
        path = FIXTURES / "vr3_demo"
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        plan_rules = [p.rule_ids[0] for p in audit.dependency_graph.plan]
        assert "ORDER001" in plan_rules
        assert plan_rules.index("ORDER001") > min(
            i for i, r in enumerate(plan_rules) if r in {"DUP001", "STYLE001"}
        )


# ---------------------------------------------------------------------------
# R3 — Semantic Preview (implementation plans; no diffs)
# ---------------------------------------------------------------------------


class TestRelease3Preview:
    def test_r3_preview_matrix(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("preview", str(path))
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        assert "Prompt Structure Preview" in proc.stdout
        assert "Implementation Plan" in proc.stdout
        assert "Repository Impact" in proc.stdout
        assert "@@" not in proc.stdout
        assert "--- a/" not in proc.stdout

    def test_r3_preview_no_writes(self):
        path = FIXTURES / "vr3_demo"
        agents = path / "AGENTS.md"
        before = agents.read_text(encoding="utf-8")
        assert _cli("preview", str(path)).returncode == 0
        assert _cli("preview", "--step", "1", str(path)).returncode == 0
        assert agents.read_text(encoding="utf-8") == before

    def test_r3_preview_step_matches_plan_count(self):
        path = FIXTURES / "vr3_demo"
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        n = len(audit.dependency_graph.plan)
        assert n >= 1
        for i in range(1, n + 1):
            proc = _cli("preview", "--step", str(i), str(path))
            assert proc.returncode == 0, proc.stderr
            assert "Intent" in proc.stdout
            assert "Implementation" in proc.stdout
            assert "@@" not in proc.stdout
        bad = _cli("preview", "--step", str(n + 1), str(path))
        assert bad.returncode == 2
        assert "Invalid step" in bad.stderr

    def test_r3_patch_preview_deprecated(self):
        path = FIXTURES / "vr3_demo"
        proc = _cli("patch", "preview", "ORDER001", str(path))
        assert proc.returncode == 2
        assert "deprecated" in proc.stderr.lower()
        assert "psa preview" in proc.stderr


# ---------------------------------------------------------------------------
# R4/R5 — Apply engine (validate internal; psa apply user-facing)
# ---------------------------------------------------------------------------


class TestRelease4And5Apply:
    def test_r4_patch_validate_deprecated(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("patch", "validate", "ORDER001", str(path))
        assert proc.returncode == 2, f"{name}: patch validate must be deprecated"
        assert "deprecated" in proc.stderr.lower()
        assert "psa apply" in proc.stderr

    def test_r5_patch_apply_deprecated(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("patch", "apply", "ORDER001", str(path), "--yes")
        assert proc.returncode == 2, f"{name}: patch apply must be deprecated"
        assert "psa apply" in proc.stderr

    def test_r5_apply_non_tty_requires_flags(self, tmp_path: Path):
        src = FIXTURES / "order_apply"
        demo = tmp_path / "nty"
        shutil.copytree(src, demo)
        subprocess.run(["git", "init"], cwd=demo, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=demo, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
            cwd=demo,
            check=True,
            capture_output=True,
        )
        proc = _cli("apply", str(demo))
        assert proc.returncode == 2
        assert "--step" in proc.stderr or "--dangerous" in proc.stderr

    def test_r5_apply_order001_on_temp_git(self, tmp_path: Path):
        src = FIXTURES / "order_apply"
        demo = tmp_path / "apply-demo"
        shutil.copytree(src, demo)
        subprocess.run(["git", "init"], cwd=demo, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=demo, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
            cwd=demo,
            check=True,
            capture_output=True,
        )
        proc = _cli("apply", "--step", "1", str(demo))
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "Prompt Structure Apply" in proc.stdout
        assert "Status: Success" in proc.stdout
        assert "Repository Changed: Yes" in proc.stdout
        assert "Repository re-analysed successfully." in proc.stdout
        assert "Optimisations Applied This Run: 1" in proc.stdout
        assert "Repository Status" in proc.stdout
        assert "Next Recommendation" in proc.stdout
        assert "Next Steps" in proc.stdout
        assert "Health:" not in proc.stdout
        assert "Completed Optimisations:" not in proc.stdout
        assert "Optimisation Progress" not in proc.stdout
        assert "Move volatile sections below stable guidance" in proc.stdout
        assert "run psa advise" not in proc.stdout  # no bridge → no Advise line
        assert (demo / ".psa" / "state.json").is_file()
        assert (demo / "PSA_STATUS.md").is_file()
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=demo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert branch == "psa/optimise"

    def test_r4_internal_validate_still_works(self):
        path = FIXTURES / "order_apply"
        fs = LocalRepoFS(path)
        audit = analyze(fs, tool_version="0.1.0")
        patch = preview_patch(fs, audit, "ORDER001")
        result = validate_patch(fs, audit, patch, tool_version="0.1.0")
        assert result.ok is True, result.failures


# ---------------------------------------------------------------------------
# R5 — Advise (embedded AI scout; fixture judgment)
# ---------------------------------------------------------------------------


class TestRelease5Advise:
    def test_advise_requires_bridge(self, tmp_path: Path):
        demo = tmp_path / "empty-advise"
        demo.mkdir()
        (demo / "AGENTS.md").write_text("# Role\n", encoding="utf-8")
        env = dict(os.environ)
        env.pop("PSA_ADVISE_CMD", None)
        env.pop("PSA_ADVISE_JUDGMENT", None)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        env["PSA_NONINTERACTIVE"] = "1"
        proc = subprocess.run(
            [sys.executable, "-m", "psa", "advise", str(demo)],
            cwd=str(SCRIPTS),
            capture_output=True,
            text=True,
            check=False,
            env=env,
            stdin=subprocess.DEVNULL,
        )
        assert proc.returncode == 2
        assert "embedded AI" in proc.stderr.lower() or "Advise requires" in proc.stderr

    def test_advise_with_judgment_fixture(self, tmp_path: Path):
        src = FIXTURES / "order_apply"
        demo = tmp_path / "advise-demo"
        shutil.copytree(src, demo)
        judgment = FIXTURES / "advise_judgment.json"
        proc = _cli("advise", str(demo), "--judgment", str(judgment))
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "Prompt Structure Advise" in proc.stdout
        assert "Advisory Recommendations" in proc.stdout
        assert "Investigation Points" in proc.stdout
        assert "conflict" in proc.stdout
        assert (demo / ".psa" / "advise.json").is_file()
        status = (demo / "PSA_STATUS.md").read_text(encoding="utf-8")
        assert "Advise Backlog" in status

    def test_advise_brief_only(self, tmp_path: Path):
        demo = tmp_path / "brief"
        demo.mkdir()
        (demo / "AGENTS.md").write_text("# Role\n", encoding="utf-8")
        proc = _cli("advise", str(demo), "--brief-only")
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["schema"] == "psa.advise.brief.v1"
        assert "rule_catalog" in data

    def test_apply_one_liner_when_bridge_set(self, tmp_path: Path):
        src = FIXTURES / "order_apply"
        demo = tmp_path / "apply-advise"
        shutil.copytree(src, demo)
        subprocess.run(["git", "init"], cwd=demo, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=demo, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
            cwd=demo,
            check=True,
            capture_output=True,
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        env["PSA_NONINTERACTIVE"] = "1"
        env["PSA_ADVISE_JUDGMENT"] = str(FIXTURES / "advise_judgment.json")
        proc = subprocess.run(
            [sys.executable, "-m", "psa", "apply", "--step", "1", str(demo)],
            cwd=str(SCRIPTS),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert "run psa advise" in proc.stdout
        assert "activation clarity" in proc.stdout.lower() or "Possible missing" in proc.stdout


# ---------------------------------------------------------------------------
# R6 — Continuous (baseline / diff) on every present target
# ---------------------------------------------------------------------------


class TestRelease6Continuous:
    def test_r6_baseline_and_diff_format(self, target: tuple[str, Path, bool], tmp_path: Path):
        name, path, _ = target
        base = tmp_path / f"{name}-baseline.json"
        save = _cli("baseline", "save", str(path), "--out", str(base))
        assert save.returncode == 0, f"{name}: {save.stderr}"
        assert base.is_file()
        data = json.loads(base.read_text(encoding="utf-8"))
        assert "findings" in data and "meta" in data

        # Diff against self → no introductions
        diff = _cli("diff", str(path), "--baseline", str(base))
        assert diff.returncode == 0, f"{name}: {diff.stderr}"
        assert "Audit Diff" in diff.stdout
        assert "Resolved:" in diff.stdout
        assert "Introduced:" in diff.stdout
        assert "Unchanged:" in diff.stdout

        fail = _cli("diff", str(path), "--baseline", str(base), "--fail-on-introduced")
        assert fail.returncode == 0, f"{name}: self-diff must not fail-on-introduced"

    def test_r6_fail_on_introduced_across_empty_to_issues(self, tmp_path: Path):
        empty = FIXTURES / "empty_repo"
        issues = FIXTURES / "vr3_demo"
        base = tmp_path / "empty.json"
        assert _cli("baseline", "save", str(empty), "--out", str(base)).returncode == 0
        diff = _cli("diff", str(issues), "--baseline", str(base), "--fail-on-introduced")
        assert diff.returncode == 1
        assert "Introduced:" in diff.stdout

    def test_r6_audit_format_still_frozen_after_lifecycle(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        text = render_audit(analyze(LocalRepoFS(path), tool_version="0.1.0"), repo_name=name)
        assert_frozen_audit_structure(text, name)


# ---------------------------------------------------------------------------
# Release matrix summary (fixtures + live)
# ---------------------------------------------------------------------------


def test_r1_to_r6_matrix_summary(capsys, tmp_path: Path):
    """Print a concise release matrix for human feedback when pytest -s."""
    rows: list[str] = []
    for name, path, live in ALL_TARGETS:
        if not path.is_dir():
            rows.append(f"{name}: SKIP (missing)")
            continue
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        ids = sorted(_rule_ids(audit))
        text = render_audit(audit, repo_name=path.name)
        try:
            assert_frozen_audit_structure(text, name)
            r1 = "OK"
        except AssertionError:
            r1 = "FAIL"

        if not audit.findings:
            plan_out = _cli("plan", str(path)).stdout
            r2 = "OK" if "No action needed" in plan_out and "Recommended Plan" in plan_out else "FAIL"
        else:
            plan_out = _cli("plan", str(path)).stdout
            r2 = (
                "OK"
                if "Plan ready" in plan_out
                and "Why now" in plan_out
                and "Expected end state" in plan_out
                and "Recommended Plan" not in text
                else "FAIL"
            )

        r3 = r4 = "n/a"
        prev = _cli("preview", str(path))
        r3 = (
            "OK"
            if prev.returncode == 0
            and "Prompt Structure Preview" in prev.stdout
            and "Repository Impact" in prev.stdout
            and "@@" not in prev.stdout
            else "FAIL"
        )
        dep_val = _cli("patch", "validate", "ORDER001", str(path))
        r4 = (
            "OK"
            if dep_val.returncode == 2 and "psa apply" in dep_val.stderr
            else "FAIL"
        )

        # Non-interactive apply without --step/--dangerous must refuse
        refuse = _cli("apply", str(path))
        r5 = (
            "OK"
            if refuse.returncode == 2
            and ("--step" in refuse.stderr or "--dangerous" in refuse.stderr or "git" in refuse.stderr)
            else "FAIL"
        )

        base = tmp_path / f"{name}.json"
        save = _cli("baseline", "save", str(path), "--out", str(base))
        diff = _cli("diff", str(path), "--baseline", str(base)) if save.returncode == 0 else None
        r6 = "OK" if save.returncode == 0 and diff and diff.returncode == 0 and "Audit Diff" in diff.stdout else "FAIL"

        kind = "live" if live else "fixture"
        rows.append(
            f"{name} ({kind}): findings={len(audit.findings)} rules={ids} "
            f"R1={r1} R2={r2} R3={r3} R4={r4} R5={r5} R6={r6}"
        )

    report = "\n".join(rows)
    print("\n=== R1–R6 release matrix (fixtures + live) ===\n" + report + "\n")
    assert any(r.startswith("VR3_fixture ") and "R4=OK" in r for r in rows)
    assert any(r.startswith("VR1_fixture ") and "findings=0" in r for r in rows)
    # Live targets: if present, must be green on format + R5 refuse + R6
    for name, path, live in present_targets():
        if not live:
            continue
        matching = [r for r in rows if r.startswith(f"{name} ")]
        assert matching, name
        assert "R1=OK" in matching[0], matching[0]
        assert "R5=OK" in matching[0], matching[0]
        assert "R6=OK" in matching[0], matching[0]
