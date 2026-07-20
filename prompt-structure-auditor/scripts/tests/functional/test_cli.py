"""CLI smoke tests."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.conftest import FIXTURES, VR3

SCRIPTS = Path(__file__).resolve().parents[2]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def test_cli_doctor_exit_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "doctor", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert "Doctor" in proc.stdout
    assert "Instruction Sources" in proc.stdout
    assert "Pattern matched" in proc.stdout or "Ignored" in proc.stdout


def test_cli_inventory_removed():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "inventory", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode != 0


def test_cli_audit_quiet_health_view():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "audit", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert "Repository" in proc.stdout
    assert "Prompt Sources" in proc.stdout
    assert "Status" in proc.stdout
    assert "Findings" in proc.stdout
    assert "Honesty note" in proc.stdout
    assert "psa doctor" in proc.stdout
    # Quiet: no full inventory dump / per-ignore listing
    assert "Prompt Surface Inventory" not in proc.stdout
    assert "Ignored (default exclusion)" not in proc.stdout


def test_cli_audit_json_contains_findings_key():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "audit", str(VR3), "--format", "json"],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert '"findings"' in proc.stdout


def test_cli_patch_preview_order001():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "patch", "preview", "ORDER001", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert "@@" in proc.stdout or "---" in proc.stdout


def test_cli_patch_validate_order001():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "patch", "validate", "ORDER001", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert "PASS" in proc.stdout


def test_cli_patch_apply_refuses_without_yes():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "patch", "apply", "ORDER001", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 2
    assert "--yes" in proc.stderr


def test_cli_baseline_and_diff(tmp_path: Path):
    base = tmp_path / "base.json"
    empty = FIXTURES / "empty_repo"
    save = subprocess.run(
        [
            sys.executable,
            "-m",
            "psa",
            "baseline",
            "save",
            str(empty),
            "--out",
            str(base),
        ],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert save.returncode == 0, save.stderr
    diff = subprocess.run(
        [
            sys.executable,
            "-m",
            "psa",
            "diff",
            str(VR3),
            "--baseline",
            str(base),
            "--fail-on-introduced",
        ],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert "Introduced" in diff.stdout
    assert diff.returncode == 1
