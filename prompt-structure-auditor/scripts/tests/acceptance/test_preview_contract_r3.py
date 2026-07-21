"""Release 3 frozen psa preview UX contract tests."""
from __future__ import annotations

from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.report.preview_view import (
    IMPACT_HEADING,
    IMPL_COLUMNS,
    IMPL_SUMMARY_HEADING,
    REPORT_TITLE,
    SUMMARY_HEADING,
    render_preview,
    render_preview_step,
)
from tests.conftest import LIVE_VR1, LIVE_VR2, LIVE_VR3, VR1, VR3, present_targets
from tests.contract_preview import (
    assert_frozen_preview_step_structure,
    assert_frozen_preview_structure,
    normalized_preview_structure,
)


def _section_order(text: str) -> list[str]:
    return [
        line
        for line in text.splitlines()
        if line in (REPORT_TITLE, SUMMARY_HEADING, IMPL_SUMMARY_HEADING, IMPACT_HEADING)
    ]


def test_preview_contract_identical_structure_healthy_and_issues():
    healthy = render_preview(
        analyze(LocalRepoFS(VR1), tool_version="0.1.0"), repo_name="vr1"
    )
    issues = render_preview(
        analyze(LocalRepoFS(VR3), tool_version="0.1.0"), repo_name="vr3"
    )
    expected = [
        REPORT_TITLE,
        SUMMARY_HEADING,
        IMPL_SUMMARY_HEADING,
        IMPACT_HEADING,
    ]
    assert _section_order(healthy) == expected
    assert _section_order(issues) == expected
    for text in (healthy, issues):
        assert_frozen_preview_structure(text)
        assert "| " + " | ".join(IMPL_COLUMNS) + " |" in text


def test_preview_contract_empty_plan():
    text = render_preview(
        analyze(LocalRepoFS(VR1), tool_version="0.1.0"), repo_name="vr1"
    )
    assert "| Recommendations | 0 |" in text
    assert "| Expected status | Healthy |" in text
    assert "No remediation steps required" in text
    assert "No implementation changes are planned" in text


def test_preview_contract_issues_have_steps():
    text = render_preview(
        analyze(LocalRepoFS(VR3), tool_version="0.1.0"), repo_name="vr3"
    )
    assert "| Expected status | Healthy |" in text
    assert "Repository Impact" in text
    assert "No new instruction sources will be introduced" in text
    # No mechanical patch language
    assert "@@" not in text
    assert "--- a/" not in text


def test_preview_step_contract_detail():
    audit = analyze(LocalRepoFS(VR3), tool_version="0.1.0")
    assert audit.dependency_graph.plan
    text = render_preview_step(audit, 1, repo_name="vr3")
    assert_frozen_preview_step_structure(text)
    assert "Overview" in text
    assert "Intent" in text
    assert "Implementation Plan" in text
    assert "Purpose" in text
    assert "Actions" in text
    assert "Repository Changes" in text
    assert "if required" not in text.lower()
    assert "@@" not in text
    assert "--- a/" not in text


def test_preview_step_invalid_errors():
    audit = analyze(LocalRepoFS(VR3), tool_version="0.1.0")
    try:
        render_preview_step(audit, 999, repo_name="vr3")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Invalid step" in str(exc)


def test_preview_contract_all_present_targets_share_structure():
    structures: dict[str, str] = {}
    for name, path, _ in present_targets():
        text = render_preview(
            analyze(LocalRepoFS(path), tool_version="0.1.0"),
            repo_name=path.name,
        )
        assert_frozen_preview_structure(text, name)
        structures[name] = normalized_preview_structure(text)
    canonical = next(iter(structures.values()))
    for name, block in structures.items():
        assert block == canonical, f"{name} preview structure diverged:\n{block}"


def test_preview_live_repos_when_present():
    for label, path in (("VR1", LIVE_VR1), ("VR2", LIVE_VR2), ("VR3", LIVE_VR3)):
        if not path.is_dir():
            continue
        text = render_preview(
            analyze(LocalRepoFS(path), tool_version="0.1.0"),
            repo_name=path.name,
        )
        assert_frozen_preview_structure(text, label)


def test_preview_never_emits_diffs_or_validation():
    text = render_preview(
        analyze(LocalRepoFS(VR3), tool_version="0.1.0"), repo_name="vr3"
    )
    lower = text.lower()
    assert "unified diff" not in lower
    assert "patch validation" not in lower
    assert "introduced:" not in lower
