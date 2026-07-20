"""Release 1 frozen audit UX contract tests."""
from __future__ import annotations

import re

from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS, MemoryRepoFS
from psa.report.audit_view import (
    FINDINGS_COLUMNS,
    FINDINGS_HEADING,
    SUMMARY_FIELDS,
    SUMMARY_HEADING,
    render_audit,
)
from tests.conftest import VR1, VR2, VR3


_FORBIDDEN_IN_AUDIT = (
    "Honesty note",
    "psa doctor",
    "Ignored (default",
    "data file",
    "Parser Failures",
    "Discovery Summary",
    "Prompt Surface Inventory",
)


def _section_order(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        if line in (SUMMARY_HEADING, FINDINGS_HEADING):
            headings.append(line)
    return headings


def test_contract_identical_structure_healthy_and_issues():
    healthy = render_audit(analyze(LocalRepoFS(VR1), tool_version="0.1.0"), repo_name="vr1")
    issues = render_audit(analyze(LocalRepoFS(VR3), tool_version="0.1.0"), repo_name="vr3")
    assert _section_order(healthy) == [SUMMARY_HEADING, FINDINGS_HEADING]
    assert _section_order(issues) == [SUMMARY_HEADING, FINDINGS_HEADING]
    for text in (healthy, issues):
        for field in SUMMARY_FIELDS:
            assert f"| {field} |" in text
        assert "| " + " | ".join(FINDINGS_COLUMNS) + " |" in text
        for bad in _FORBIDDEN_IN_AUDIT:
            assert bad not in text


def test_contract_empty_findings_placeholder_row():
    text = render_audit(analyze(LocalRepoFS(VR1), tool_version="0.1.0"), repo_name="vr1")
    assert "| Findings | None |" in text
    assert "✅ Healthy" in text
    assert "No prompt architecture issues detected" in text


def test_contract_issues_status_and_breakdown():
    text = render_audit(analyze(LocalRepoFS(VR2), tool_version="0.1.0"), repo_name="lateTrainQueries")
    assert "⚠ Needs Attention" in text
    assert re.search(r"\| Findings \| \d+ \(", text)
    assert "| High | ACT" in text or "| High | ACT001 |" in text


def test_contract_documentation_counted():
    fs = MemoryRepoFS(
        {
            "AGENTS.md": "# A\nStable.\n",
            "docs/prompt-engineering.md": "# Prompts\n",
            "docs/coding-standards.md": "# Standards\n",
            ".serena/project.yml": "x: 1\n",
        }
    )
    audit = analyze(fs, tool_version="0.1.0")
    assert len(audit.documentation) >= 2
    text = render_audit(audit, repo_name="demo")
    assert "| Documentation |" in text
    assert "2 files" in text or re.search(r"\| Documentation \| \d+ files? \|", text)


def test_contract_docs_not_promoted_to_findings():
    fs = MemoryRepoFS(
        {
            "docs/AI-GUIDANCE.md": "## Current Focus: X\nVolatile worklog style.\n",
        }
    )
    audit = analyze(fs, tool_version="0.1.0")
    assert audit.documentation
    assert audit.findings == ()
    text = render_audit(audit, repo_name="docs-only")
    assert "✅ Healthy" in text
