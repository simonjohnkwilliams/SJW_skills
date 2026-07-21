"""Frozen Apply completion report — lean optimisation cycle outcome."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psa.apply.engine import ApplySessionResult, IterationResult
    from psa.core.pipeline import Audit

REPORT_TITLE = "Prompt Structure Apply"


def render_apply_report(
    session: ApplySessionResult,
    *,
    repo_name: str,
) -> str:
    blocked = [i for i in session.iterations if i.outcome == "blocked"]
    if blocked and session.exit_code != 0:
        return _render_paused(blocked[0])

    applied = [i for i in session.iterations if i.outcome == "applied"]
    skipped = [i for i in session.iterations if i.outcome == "skipped"]
    idle = any(i.outcome == "idle" for i in session.iterations)
    audit = session.final_audit
    mode = session.mode or "Interactive"
    changed = "Yes" if applied else "No"
    reanalysed = bool(applied) or idle  # cycle ran audit/plan; idle = already clean

    if applied:
        status = "Success"
    elif skipped and not applied:
        status = "Skipped"
    else:
        status = "Success"

    lines: list[str] = [
        REPORT_TITLE,
        "",
        f"Status: {status}",
        "",
        f"Repository: {_ascii(repo_name)}",
        f"Mode: {mode}",
        "",
    ]

    if mode == "Interactive" or len(applied) <= 1:
        if applied:
            lines.append("Recommendation Applied:")
            lines.append(f"* {_ascii(applied[0].title)}")
            lines.append("")
        elif skipped:
            lines.append("Recommendation:")
            lines.append(f"* Skipped: {_ascii(skipped[0].title)}")
            lines.append(f"  {_ascii(skipped[0].detail)}")
            lines.append("")
        elif idle:
            lines.append("Recommendation Applied:")
            lines.append("* None")
            lines.append("")
    else:
        lines.append("Recommendations Applied")
        lines.append("")
        for itr in applied:
            lines.append(f"* {_ascii(itr.title)}")
        lines.append("")

    lines.append(f"Repository Changed: {changed}")
    if session.duration_seconds is not None:
        lines.append(f"Duration: {session.duration_seconds:.1f}s")
    lines.append("")

    if reanalysed and (applied or idle):
        lines.append("Repository re-analysed successfully.")
        lines.append("")

    # --- Repository Status (objective facts only) ---
    plan = ()
    if audit is not None:
        plan = getattr(audit.dependency_graph, "plan", ()) or ()
    n_outstanding = len(plan)
    n_this_run = len(applied)

    lines.extend(
        [
            "Repository Status",
            "",
            f"Optimisations Applied This Run: {n_this_run}",
            f"Outstanding Recommendations: {n_outstanding}",
            "",
        ]
    )

    # --- Next Recommendation ---
    lines.extend(["Next Recommendation", ""])
    if n_outstanding and plan:
        nxt = plan[0]
        lines.append(_ascii(nxt.title))
        lines.append("")
        lines.append("Run:")
        lines.append("")
        lines.append("psa preview --step 1")
        lines.append("")
    else:
        lines.extend(
            [
                "None",
                "",
                "Repository optimisation is complete.",
                "",
            ]
        )

    # --- Next Steps ---
    lines.extend(["Next Steps", ""])
    if n_outstanding:
        lines.extend(
            [
                "Review the updated implementation plan:",
                "",
                "psa preview",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Run your normal validation process:",
                "",
                "* Prompt evaluation",
                "* Repository tests",
                "* Manual review (if required)",
                "",
            ]
        )

    return "\n".join(lines)


def _render_paused(blocked: IterationResult) -> str:
    title = blocked.title or "Unknown recommendation"
    detail = blocked.detail or ""
    if "validation" in detail.lower() or "missing" in detail.lower():
        reason = "Repository no longer matches the reviewed implementation plan."
    else:
        reason = detail or "Apply paused."

    return "\n".join(
        [
            REPORT_TITLE,
            "",
            "Status: Paused",
            "",
            "Reason:",
            _ascii(reason),
            "",
            "Recommendation:",
            _ascii(title),
            "",
            "Action Required:",
            "",
            "The repository has been re-evaluated.",
            "",
            "Run:",
            "",
            "psa preview",
            "",
            "to review the updated implementation plan.",
            "",
        ]
    )


def _ascii(value: str) -> str:
    return value.encode("ascii", errors="replace").decode("ascii")
