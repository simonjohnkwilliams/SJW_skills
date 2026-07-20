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


def test_cli_discover_exit_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "discover", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert "Discovery Summary" in proc.stdout
    assert "Reason:" in proc.stdout


def test_cli_inventory_exit_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "psa", "inventory", str(VR3)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        check=False,
        env=_env(),
    )
    assert proc.returncode == 0, proc.stderr
    assert "AGENTS" in proc.stdout or "Prompt Surface" in proc.stdout


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
