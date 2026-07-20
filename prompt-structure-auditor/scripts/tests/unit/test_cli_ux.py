"""Unit tests for quiet audit and doctor presentation."""
from __future__ import annotations

from psa.core.config import DEFAULT_CONFIG
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS, MemoryRepoFS
from psa.discovery import discover
from psa.report.audit_view import render_audit
from psa.report.doctor import render_doctor
from tests.conftest import VR1, VR3


def test_render_audit_healthy_empty_surface():
    audit = analyze(LocalRepoFS(VR1), tool_version="0.1.0")
    text = render_audit(audit, repo_name="vr1_empty")
    assert "Repository" in text
    assert "vr1_empty" in text
    assert "Prompt Sources" in text
    assert "Status" in text
    assert "Honesty note" in text
    assert "psa doctor" in text
    assert "Prompt Surface Inventory" not in text


def test_render_audit_findings_grouped():
    audit = analyze(LocalRepoFS(VR3), tool_version="0.1.0")
    text = render_audit(audit, repo_name="vr3_demo")
    assert "Issues found" in text
    assert "High" in text
    assert "ORDER001" in text
    assert "Recommendation:" in text
    assert "Ignored (default exclusion)" not in text


def test_render_doctor_verbose():
    fs = MemoryRepoFS(
        {
            "AGENTS.md": "# A\n",
            "tests/fixtures/AGENTS.md": "# ignore me\n",
        }
    )
    result = discover(fs, DEFAULT_CONFIG)
    text = render_doctor(result, DEFAULT_CONFIG)
    assert "Doctor" in text
    assert "Instruction Sources" in text
    assert "AGENTS.md" in text
    assert "Ignored" in text
    assert "Pattern matched" in text
    assert "Ignore Patterns" in text
    assert "--no-default-ignores" in text
