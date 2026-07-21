"""Frozen Release 3 preview report — public UX contract for `psa preview`.

Overview (every repo, every run):

1. Prompt Structure Preview
2. Summary
3. Implementation Plan
4. Repository Impact

Step detail (`psa preview --step N`):

1. Prompt Structure Preview
2. Recommendation
3. Summary
4. Overview
5. Intent
6. Implementation Plan   (per file: Purpose + Actions)
7. Result
8. Repository Changes

Read-only. Never emits patches, diffs, or validation output.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from psa.preview.model import ImplementationPreview, PreviewSet, build_preview_set, get_step_preview

if TYPE_CHECKING:
    from psa.core.pipeline import Audit

REPORT_TITLE = "Prompt Structure Preview"
SUMMARY_HEADING = "Summary"
IMPL_SUMMARY_HEADING = "Implementation Plan"
IMPACT_HEADING = "Repository Impact"

RECOMMENDATION_HEADING = "Recommendation"
OVERVIEW_HEADING = "Overview"
INTENT_HEADING = "Intent"
IMPLEMENTATION_HEADING = "Implementation Plan"
RESULT_HEADING = "Result"
FILES_HEADING = "Repository Changes"
PURPOSE_HEADING = "Purpose"
ACTIONS_HEADING = "Actions"

SUMMARY_FIELDS = (
    "Repository",
    "Recommendations",
    "Unique files affected",
    "Files added",
    "Files modified",
    "Files removed",
    "Expected status",
)

STEP_SUMMARY_FIELDS = (
    "Effort",
    "Unique files affected",
    "Primary change",
)

IMPL_COLUMNS = ("Step", "Recommendation", "Files", "Primary Change")

FILE_SEP = "--------------------------------"
EMPTY_IMPL = "No remediation steps required"
EMPTY_IMPACT = "No implementation changes are planned."


def render_preview(audit: Audit, *, repo_name: str | None = None) -> str:
    """Repository-level implementation overview (Level 1)."""
    name = _ascii(repo_name or "repository")
    preview = build_preview_set(audit)
    return _render_overview(preview, repo_name=name)


def render_preview_step(
    audit: Audit,
    step: int,
    *,
    repo_name: str | None = None,
) -> str:
    """Single-recommendation implementation specification (Level 2)."""
    detail = get_step_preview(audit, step)
    return _render_step(detail)


def _render_overview(preview: PreviewSet, *, repo_name: str) -> str:
    n_recs = len(preview.steps)
    summary_values = {
        "Repository": repo_name,
        "Recommendations": str(n_recs),
        "Unique files affected": str(preview.files_affected),
        "Files added": str(len(preview.files_added)),
        "Files modified": str(len(preview.files_modified)),
        "Files removed": str(len(preview.files_removed)),
        "Expected status": preview.expected_status,
    }

    lines: list[str] = [
        REPORT_TITLE,
        "",
        SUMMARY_HEADING,
        "",
        "| Field | Result |",
        "| --- | --- |",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"| {field} | {summary_values[field]} |")

    lines.extend(
        [
            "",
            IMPL_SUMMARY_HEADING,
            "",
            "| " + " | ".join(IMPL_COLUMNS) + " |",
            "| --- | --- | --- | --- |",
        ]
    )

    if not preview.steps:
        lines.append(f"| - | {EMPTY_IMPL} | - | - |")
    else:
        for s in preview.steps:
            title = _ascii(s.title).replace("|", "/")
            if len(title) > 40:
                title = title[:37].rstrip() + "..."
            change = _ascii(s.primary_change).replace("|", "/")
            if len(change) > 36:
                change = change[:33].rstrip() + "..."
            lines.append(
                f"| {s.step} | {title} | {s.files_affected} | {change} |"
            )

    lines.extend(["", IMPACT_HEADING, ""])
    for bullet in preview.repository_impact:
        lines.append(f"* {_ascii(bullet)}")
    lines.append("")
    return "\n".join(lines)


def _render_step(detail: ImplementationPreview) -> str:
    lines: list[str] = [
        REPORT_TITLE,
        "",
        RECOMMENDATION_HEADING,
        "",
        _ascii(detail.title),
        "",
        SUMMARY_HEADING,
        "",
        "| Field | Result |",
        "| --- | --- |",
        f"| Effort | {detail.effort} |",
        f"| Unique files affected | {detail.files_affected} |",
        f"| Primary change | {_ascii(detail.primary_change)} |",
        "",
        OVERVIEW_HEADING,
        "",
        _ascii(detail.overview),
        "",
        INTENT_HEADING,
        "",
        _ascii(detail.intent),
        "",
        IMPLEMENTATION_HEADING,
        "",
    ]

    for i, fa in enumerate(detail.file_actions):
        lines.extend(_render_file_plan(fa))
        if i < len(detail.file_actions) - 1:
            lines.extend(["", FILE_SEP, ""])
        else:
            lines.append("")

    lines.extend([RESULT_HEADING, ""])
    for item in detail.result:
        lines.append(f"* {_ascii(item)}")

    lines.extend(["", FILES_HEADING, "", "Modified", ""])
    if detail.files_modified:
        for p in detail.files_modified:
            lines.append(f"* {_ascii(p)}")
    else:
        lines.append("None")

    lines.extend(["", "Added", ""])
    if detail.files_added:
        for p in detail.files_added:
            lines.append(f"* {_ascii(p)}")
    else:
        lines.append("None")

    lines.extend(["", "Removed", ""])
    if detail.files_removed:
        for p in detail.files_removed:
            lines.append(f"* {_ascii(p)}")
    else:
        lines.append("None")

    lines.append("")
    return "\n".join(lines)


def _render_file_plan(fa) -> list[str]:
    lines = [
        _ascii(fa.path),
        "",
        PURPOSE_HEADING,
        "",
        _ascii(fa.purpose),
        "",
        ACTIONS_HEADING,
        "",
    ]
    for group in fa.groups:
        if group.label:
            lines.append(_ascii(group.label))
            lines.append("")
        for item in group.items:
            lines.append(f"* {_ascii(item)}")
    return lines


def _ascii(value: str) -> str:
    return value.encode("ascii", errors="replace").decode("ascii")
