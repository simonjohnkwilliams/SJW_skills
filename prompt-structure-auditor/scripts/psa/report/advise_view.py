"""Plan-shaped Advise report — public UX for `psa advise`."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psa.advise.schema import AdviseItem, AdviseJudgment

REPORT_TITLE = "Prompt Structure Advise"
SUMMARY_HEADING = "Summary"
ADVISE_HEADING = "Advisory Recommendations"
CONFLICT_HEADING = "Investigation Points"
DETAILS_HEADING = "Recommendation Details"
FOOTER = (
    "These items are not applied by PSA. "
    "Promote promising ones into deterministic rules."
)

SUMMARY_FIELDS = (
    "Repository",
    "Advisory items",
    "Investigation points",
    "Status",
)

PLAN_COLUMNS = ("Step", "Kind", "Recommendation", "Effort", "Paths")


def render_advise(
    judgment: AdviseJudgment,
    *,
    repo_name: str,
) -> str:
    name = _ascii(repo_name)
    advise = judgment.advise_items()
    conflicts = judgment.conflict_items()
    n_advise = len(advise)
    n_conflict = len(conflicts)
    if n_advise == 0 and n_conflict == 0:
        status = "No additional concerns"
    elif n_conflict and not n_advise:
        status = "Investigation recommended"
    elif n_advise and not n_conflict:
        status = "Advise ready"
    else:
        status = "Advise ready (with conflicts)"

    summary_values = {
        "Repository": name,
        "Advisory items": str(n_advise),
        "Investigation points": str(n_conflict),
        "Status": status,
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
            ADVISE_HEADING,
            "",
            "| " + " | ".join(PLAN_COLUMNS) + " |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if not advise:
        lines.append("| - | advise | No advisory gaps beyond current rules | - | - |")
    else:
        for i, item in enumerate(advise, 1):
            lines.append(_table_row(i, item))

    lines.extend(
        [
            "",
            CONFLICT_HEADING,
            "",
            "| " + " | ".join(PLAN_COLUMNS) + " |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if not conflicts:
        lines.append("| - | conflict | No contradictions with deterministic rules | - | - |")
    else:
        for i, item in enumerate(conflicts, 1):
            lines.append(_table_row(i, item))

    all_items = list(advise) + list(conflicts)
    lines.extend(["", DETAILS_HEADING, ""])
    if not all_items:
        lines.append("No advisory items.")
    else:
        for i, item in enumerate(all_items, 1):
            lines.extend(_render_detail(i, item))
            lines.append("----------")

    lines.extend(["", FOOTER, ""])
    return "\n".join(lines)


def format_apply_advise_line(theme: str) -> str:
    theme = _ascii(theme).strip().rstrip(".")
    if not theme:
        return ""
    if "run psa advise" in theme.lower():
        return theme
    return f"{theme} - run psa advise"


def _table_row(step: int, item: AdviseItem) -> str:
    title = _ascii(item.title).replace("|", "/")
    if len(title) > 48:
        title = title[:45].rstrip() + "..."
    paths = ", ".join(_ascii(p) for p in item.paths[:3]) or "-"
    if len(item.paths) > 3:
        paths += ", …"
    paths = paths.replace("|", "/")
    if len(paths) > 36:
        paths = paths[:33].rstrip() + "..."
    return (
        f"| {step} | {item.kind} | {title} | "
        f"{_ascii(item.effort)} | {paths} |"
    )


def _render_detail(step: int, item: AdviseItem) -> list[str]:
    lines = [
        f"Step {step}: {_ascii(item.title)} [{item.kind}]",
        f"Why: {_ascii(item.reason) or '-'}",
        f"Paths: {', '.join(_ascii(p) for p in item.paths) or '-'}",
        f"Effort: {_ascii(item.effort)}",
    ]
    if item.conflicts_with:
        lines.append(
            "Conflicts with: " + ", ".join(_ascii(c) for c in item.conflicts_with)
        )
    if item.rule_seed_id or item.rule_seed_idea:
        seed = item.rule_seed_id or "(unspecified)"
        idea = item.rule_seed_idea or "-"
        lines.append(f"Rule seed: {_ascii(seed)} — {_ascii(idea)}")
    return lines


def _ascii(value: str) -> str:
    return value.encode("ascii", errors="replace").decode("ascii")
