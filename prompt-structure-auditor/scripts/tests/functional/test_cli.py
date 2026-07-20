"""CLI smoke tests."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.conftest import VR3

SCRIPTS = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
    return env


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
