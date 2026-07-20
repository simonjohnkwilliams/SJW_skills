"""User-facing audit report — answers: is prompt architecture healthy?"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psa.core.pipeline import Audit


_PRIORITY_ORDER = ("High value", "Medium value", "Low value", "Informational")
_PRIORITY_LABEL = {
    "High value": "High",
    "Medium value": "Medium",
    "Low value": "Low",
    "Informational": "Informational",
}


def render_audit(audit: Audit, *, repo_name: str | None = None) -> str:
    """Quiet day-to-day audit output (CLI default text)."""
    inv = audit.inventory
    n_instr = sum(1 for r in inv.rows if r.status == "present")
    n_config = sum(1 for r in inv.rows if r.status == "config")
    n_ignored = sum(1 for r in inv.rows if r.status == "ignored")
    n_data = sum(1 for r in inv.rows if r.status == "out_of_scope")

    name = repo_name or "repository"
    lines: list[str] = [
        "Repository",
        f"  {name}",
        "",
        "Prompt Sources",
        f"  {n_instr} instruction source{'s' if n_instr != 1 else ''}",
        f"  {n_config} configuration file{'s' if n_config != 1 else ''}",
        f"  {n_ignored} ignored path{'s' if n_ignored != 1 else ''}",
        f"  {n_data} data file{'s' if n_data != 1 else ''} excluded",
        "",
        "Status",
    ]

    if not audit.findings:
        if n_instr == 0:
            lines.append("  No prompt instruction surface found")
            lines.append("  Honest empty result: nothing to structurally audit.")
        else:
            lines.append("  Healthy")
            lines.append("")
            lines.append("Findings")
            lines.append("  No prompt architecture issues detected.")
    else:
        lines.append("  Issues found")
        lines.append("")
        lines.append(f"Findings")
        lines.append(f"  {len(audit.findings)} finding{'s' if len(audit.findings) != 1 else ''}")
        lines.append("")
        by_pri: dict[str, list] = {p: [] for p in _PRIORITY_ORDER}
        for f in audit.findings:
            by_pri.setdefault(f.priority, []).append(f)
        for band in _PRIORITY_ORDER:
            group = by_pri.get(band) or []
            if not group:
                continue
            lines.append(_PRIORITY_LABEL.get(band, band))
            for f in group:
                lines.append(f"  [{f.rule_id}] {f.title}")
                lines.append(
                    f"    {f.priority} · {f.verification} · owner: {f.ownership}"
                )
                if f.evidence:
                    e0 = f.evidence[0]
                    span = f"{e0.span[0]}-{e0.span[1]}" if e0.span else "?"
                    lines.append(f"    Evidence: {e0.path}:{span}")
                lines.append(f"    Recommendation: {f.recommendation}")
                lines.append("")

    lines.append("Honesty note")
    lines.append(
        "  This audit reports structure observable from repository contents. "
        "It does not measure or predict cache hit rate, cost, or latency."
    )
    lines.append("")
    lines.append("Run `psa doctor` for discovery details.")
    lines.append("")
    return "\n".join(lines)


def repo_display_name(root: str | Path) -> str:
    return Path(root).resolve().name
