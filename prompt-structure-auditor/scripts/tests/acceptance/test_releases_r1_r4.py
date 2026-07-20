"""Release acceptance automation for R1–R4 (Audit → Prioritise → Preview → Validate).

Runs against in-repo fixtures always, and against the three live validation
repos when present on this machine:

  VR1  ai-context-benchmark   (empty / honesty)
  VR2  lateTrainQueries       (activation + duplication)
  VR3  OneDrive demo          (ORDER + STYLE + DUP)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from psa.core.canon import dumps
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.patch.generate import preview_patch
from psa.patch.validate import validate_patch
from psa.report.inventory import render_human, render_inventory
from tests.conftest import FIXTURES, LIVE_VR1, LIVE_VR2, LIVE_VR3

SCRIPTS = Path(__file__).resolve().parents[2]
FABRICATED = ("score", "hit_rate", "latency", "cost", "token_saving", "token_savings", "cache_score")

# (label, path, live?)
TARGETS = [
    ("VR1_fixture", FIXTURES / "vr1_empty", False),
    ("VR2_fixture", FIXTURES / "vr2_latetrain", False),
    ("VR3_fixture", FIXTURES / "vr3_demo", False),
    ("VR1_live", LIVE_VR1, True),
    ("VR2_live", LIVE_VR2, True),
    ("VR3_live", LIVE_VR3, True),
]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
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


def _present(targets: list[tuple[str, Path, bool]]) -> list[tuple[str, Path, bool]]:
    return [(n, p, live) for n, p, live in targets if p.is_dir()]


def _rule_ids(audit) -> set[str]:
    return {f.rule_id for f in audit.findings}


# ---------------------------------------------------------------------------
# Parametrized target matrix
# ---------------------------------------------------------------------------


@pytest.fixture(params=_present(TARGETS), ids=lambda t: t[0])
def target(request) -> tuple[str, Path, bool]:
    return request.param


# ---------------------------------------------------------------------------
# R1 — Audit (read-only)
# ---------------------------------------------------------------------------


class TestRelease1Audit:
    def test_r1_inventory_cli(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("inventory", str(path))
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        assert "Prompt Surface Inventory" in proc.stdout

    def test_r1_audit_text_has_honesty(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        text = render_human(audit)
        assert "Honesty note" in text
        assert "hit rate" in text.lower() or "cache hit" in text.lower() or "does not measure" in text
        inv = render_inventory(audit.inventory)
        assert "Prompt Surface Inventory" in inv or "inventory" in inv.lower()

    def test_r1_audit_json_shape_no_fabricated(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        proc = _cli("audit", str(path), "--format", "json")
        assert proc.returncode == 0, f"{name}: {proc.stderr}"
        data = json.loads(proc.stdout)
        for key in ("meta", "inventory", "findings", "dependency_graph"):
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

    def test_r1_vr3_order_style_dup_not_noisy(self):
        for name, path in (("VR3_fixture", FIXTURES / "vr3_demo"), ("VR3_live", LIVE_VR3)):
            if not path.is_dir():
                continue
            audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
            ids = _rule_ids(audit)
            assert "ORDER001" in ids, name
            assert "STYLE001" in ids, name
            assert "DUP001" in ids, name
            order_titles = [f.title for f in audit.findings if f.rule_id == "ORDER001"]
            assert any("Current Focus" in t for t in order_titles), name
            assert not any(
                "On Hold" in t or "Debugging" in t or "Known Issue" in t for t in order_titles
            ), name


# ---------------------------------------------------------------------------
# R2 — Prioritise
# ---------------------------------------------------------------------------


class TestRelease2Prioritise:
    def test_r2_roadmap_when_findings(self, target: tuple[str, Path, bool]):
        name, path, _ = target
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        text = render_human(audit)
        if not audit.findings:
            assert "Fix these first" not in text
            assert audit.dependency_graph is None or not audit.dependency_graph.roadmap
            return
        assert "Fix these first (roadmap)" in text, name
        assert "Implementation Roadmap" in text, name
        assert audit.dependency_graph is not None
        assert audit.dependency_graph.roadmap
        # Unique rule headlines appear before the flat finding list is the only guide
        assert "[ORDER001]" in text or "[ACT001]" in text or "[STYLE001]" in text or "[DUP001]" in text

    def test_r2_vr3_dependencies_mention_order_after_style_or_dup(self):
        for name, path in (("VR3_fixture", FIXTURES / "vr3_demo"), ("VR3_live", LIVE_VR3)):
            if not path.is_dir():
                continue
            text = render_human(analyze(LocalRepoFS(path), tool_version="0.1.0"))
            assert "Dependencies" in text, name
            assert "ORDER001" in text and ("STYLE001" in text or "DUP001" in text), name


# ---------------------------------------------------------------------------
# R3 — Preview
# ---------------------------------------------------------------------------


class TestRelease3Preview:
    def test_r3_preview_order001_diff_no_writes(self, tmp_path: Path):
        for name, path in (("VR3_fixture", FIXTURES / "vr3_demo"), ("VR3_live", LIVE_VR3)):
            if not path.is_dir():
                continue
            # Snapshot mtimes of instruction files
            agents = path / "AGENTS.md"
            before = agents.read_text(encoding="utf-8") if agents.is_file() else None
            proc = _cli("patch", "preview", "ORDER001", str(path))
            assert proc.returncode == 0, f"{name}: {proc.stderr}"
            assert "---" in proc.stdout or "@@" in proc.stdout, name
            if before is not None:
                assert agents.read_text(encoding="utf-8") == before, f"{name} preview wrote files"

    def test_r3_preview_api_matches_cli(self):
        path = FIXTURES / "vr3_demo"
        fs = LocalRepoFS(path)
        audit = analyze(fs, tool_version="0.1.0")
        patch = preview_patch(fs, audit, "ORDER001")
        assert patch.rule_id == "ORDER001"
        assert patch.diff
        proc = _cli("patch", "preview", "ORDER001", str(path))
        assert proc.returncode == 0
        assert patch.diff.strip() == proc.stdout.strip() or patch.diff in proc.stdout

    def test_r3_preview_non_patchable_errors(self):
        path = FIXTURES / "vr3_demo"
        proc = _cli("patch", "preview", "STYLE001", str(path))
        assert proc.returncode != 0
        assert "STYLE001" in proc.stderr or "patchable" in proc.stderr.lower() or "not" in proc.stderr.lower()

    def test_r3_preview_absent_on_vr1(self):
        path = FIXTURES / "vr1_empty"
        proc = _cli("patch", "preview", "ORDER001", str(path))
        assert proc.returncode != 0


# ---------------------------------------------------------------------------
# R4 — Validate
# ---------------------------------------------------------------------------


class TestRelease4Validate:
    def test_r4_validate_order001_passes(self):
        for name, path in (("VR3_fixture", FIXTURES / "vr3_demo"), ("VR3_live", LIVE_VR3)):
            if not path.is_dir():
                continue
            agents = path / "AGENTS.md"
            before = agents.read_text(encoding="utf-8") if agents.is_file() else None
            proc = _cli("patch", "validate", "ORDER001", str(path))
            assert proc.returncode == 0, f"{name}: {proc.stderr}\n{proc.stdout}"
            assert "PASS" in proc.stdout, name
            assert "Introduced:" in proc.stdout
            # tolerant of spacing: "Introduced:   0"
            assert "Introduced:" in proc.stdout and "0" in proc.stdout.split("Introduced:")[1].splitlines()[0]
            if before is not None:
                assert agents.read_text(encoding="utf-8") == before, f"{name} validate wrote files"

    def test_r4_validate_json_ok(self):
        path = FIXTURES / "vr3_demo"
        proc = _cli("patch", "validate", "ORDER001", str(path), "--format", "json")
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert data["ok"] is True
        assert data["introduced"] == []

    def test_r4_validate_api_invariant(self):
        for name, path in (("VR3_fixture", FIXTURES / "vr3_demo"), ("VR3_live", LIVE_VR3)):
            if not path.is_dir():
                continue
            fs = LocalRepoFS(path)
            audit = analyze(fs, tool_version="0.1.0")
            patch = preview_patch(fs, audit, "ORDER001")
            result = validate_patch(fs, audit, patch, tool_version="0.1.0")
            assert result.ok is True, f"{name}: {result.failures}"
            assert patch.finding_id in result.resolved
            assert result.introduced == ()


# ---------------------------------------------------------------------------
# Cross-release smoke matrix (one shot per present repo)
# ---------------------------------------------------------------------------


def test_r1_to_r4_matrix_summary(capsys):
    """Print a concise release matrix for human feedback when pytest -s."""
    rows: list[str] = []
    for name, path, live in TARGETS:
        if not path.is_dir():
            rows.append(f"{name}: SKIP (missing)")
            continue
        audit = analyze(LocalRepoFS(path), tool_version="0.1.0")
        ids = sorted(_rule_ids(audit))
        r1 = "OK"
        r2 = "OK" if (not audit.findings or "Fix these first" in render_human(audit)) else "FAIL"
        r3 = r4 = "n/a"
        if "ORDER001" in ids:
            prev = _cli("patch", "preview", "ORDER001", str(path))
            val = _cli("patch", "validate", "ORDER001", str(path))
            r3 = "OK" if prev.returncode == 0 else "FAIL"
            r4 = "OK" if val.returncode == 0 and "PASS" in val.stdout else "FAIL"
        rows.append(
            f"{name}: findings={len(audit.findings)} rules={ids} "
            f"R1={r1} R2={r2} R3={r3} R4={r4}"
        )
    report = "\n".join(rows)
    print("\n=== R1–R4 release matrix ===\n" + report + "\n")
    # Always assert fixtures present and green for ORDER path
    assert any(r.startswith("VR3_fixture:") and "R4=OK" in r for r in rows)
    assert any(r.startswith("VR1_fixture:") and "findings=0" in r for r in rows)
