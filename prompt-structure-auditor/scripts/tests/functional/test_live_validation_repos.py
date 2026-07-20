"""Optional smoke against full validation repositories (skips if absent)."""
from __future__ import annotations

from pathlib import Path

import pytest

from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.report.inventory import render_inventory

VR1 = Path(r"C:\Users\simon\IdeaProjects\ai-context-benchmark")
VR2 = Path(r"C:\Users\simon\IdeaProjects\lateTrainQueries")
VR3 = Path(r"C:\Users\simon\OneDrive\demo\demo")


@pytest.mark.skipif(not VR1.is_dir(), reason="VR1 not present on this machine")
def test_live_vr1_no_instruction_findings_required():
    audit = analyze(LocalRepoFS(VR1), tool_version="0.1.0")
    text = render_inventory(audit.inventory)
    assert "Not found" in text or "[ ]" in text
    # May still have STYLE/others only if instruction sources appear; VR1 has none.
    assert not any(f.rule_id == "ORDER001" for f in audit.findings)


@pytest.mark.skipif(not VR2.is_dir(), reason="VR2 not present on this machine")
def test_live_vr2_activation_findings():
    audit = analyze(LocalRepoFS(VR2), tool_version="0.1.0")
    act = [f for f in audit.findings if f.rule_id in {"ACT001", "ACT002"}]
    assert len(act) >= 1


@pytest.mark.skipif(not VR3.is_dir(), reason="VR3 not present on this machine")
def test_live_vr3_order_and_style():
    audit = analyze(LocalRepoFS(VR3), tool_version="0.1.0")
    assert any(f.rule_id == "ORDER001" for f in audit.findings)
    assert any(f.rule_id == "STYLE001" for f in audit.findings)
