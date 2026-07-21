"""Frozen psa preview UX contract (Release 3+) — consistent across all repos."""
from __future__ import annotations

from psa.report.preview_view import (
    FILES_HEADING,
    IMPACT_HEADING,
    IMPL_COLUMNS,
    IMPL_SUMMARY_HEADING,
    IMPLEMENTATION_HEADING,
    INTENT_HEADING,
    OVERVIEW_HEADING,
    RECOMMENDATION_HEADING,
    REPORT_TITLE,
    RESULT_HEADING,
    SUMMARY_FIELDS,
    SUMMARY_HEADING,
)


def normalized_preview_structure(text: str) -> str:
    """Blank values; keep frozen overview headings through Repository Impact."""
    lines: list[str] = []
    mode = "head"  # head | skip_impl | skip_impact
    for line in text.splitlines():
        if line.startswith("| ") and line.count("|") == 3:
            field = line.split("|")[1].strip()
            if field in SUMMARY_FIELDS:
                lines.append(f"| {field} | <value> |")
                continue
        if line == "| --- | --- | --- | --- |":
            lines.append(line)
            lines.append("| <impl rows> |")
            mode = "skip_impl"
            continue
        if mode == "skip_impl":
            if line == IMPACT_HEADING:
                lines.append(line)
                lines.append("<impact>")
                mode = "skip_impact"
            continue
        if mode == "skip_impact":
            continue
        lines.append(line)
        if line == IMPACT_HEADING:
            lines.append("<impact>")
            mode = "skip_impact"
    return "\n".join(lines)


def assert_frozen_preview_structure(text: str, label: str = "preview") -> None:
    assert text.startswith(REPORT_TITLE), f"{label}: missing title"
    assert SUMMARY_HEADING in text, f"{label}: missing Summary"
    assert IMPL_SUMMARY_HEADING in text, f"{label}: missing Implementation Plan"
    assert IMPACT_HEADING in text, f"{label}: missing Repository Impact"
    for field in SUMMARY_FIELDS:
        assert f"| {field} |" in text, f"{label}: missing Summary field {field}"
    assert "| " + " | ".join(IMPL_COLUMNS) + " |" in text, f"{label}: impl columns"
    i_title = text.index(REPORT_TITLE)
    i_summary = text.index(SUMMARY_HEADING)
    i_impl = text.index(IMPL_SUMMARY_HEADING)
    i_impact = text.index(IMPACT_HEADING)
    assert i_title < i_summary < i_impl < i_impact, f"{label}: section order"
    assert text.encode("ascii"), f"{label}: not ASCII-safe"
    for bad in ("--- a/", "+++ b/", "@@ ", "unified diff", "patch apply"):
        assert bad not in text, f"{label}: leaked {bad!r}"


def assert_frozen_preview_step_structure(text: str, label: str = "preview-step") -> None:
    assert text.startswith(REPORT_TITLE), f"{label}: missing title"
    lines = text.splitlines()
    heading_lines = {
        RECOMMENDATION_HEADING,
        SUMMARY_HEADING,
        OVERVIEW_HEADING,
        INTENT_HEADING,
        IMPLEMENTATION_HEADING,
        RESULT_HEADING,
        FILES_HEADING,
    }
    positions = {h: lines.index(h) for h in heading_lines if h in lines}
    for h in heading_lines:
        assert h in positions, f"{label}: missing {h}"
    assert (
        positions[RECOMMENDATION_HEADING]
        < positions[SUMMARY_HEADING]
        < positions[OVERVIEW_HEADING]
        < positions[INTENT_HEADING]
        < positions[IMPLEMENTATION_HEADING]
        < positions[RESULT_HEADING]
        < positions[FILES_HEADING]
    ), f"{label}: section order"
    assert "Purpose" in text, f"{label}: missing Purpose"
    assert "Actions" in text, f"{label}: missing Actions"
    assert "Modified" in text and "Added" in text and "Removed" in text
    assert text.encode("ascii"), f"{label}: not ASCII-safe"
    lower = text.lower()
    for bad in (
        "--- a/",
        "+++ b/",
        "@@ ",
        "insert line",
        "delete line",
        "edit line",
        "if required",
    ):
        assert bad not in text and bad not in lower, f"{label}: leaked {bad!r}"
