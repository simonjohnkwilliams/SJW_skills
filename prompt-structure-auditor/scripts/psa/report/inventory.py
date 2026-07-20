"""Inventory and human/machine report rendering."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryRow:
    adapter: str
    label: str
    status: str  # present | absent | out_of_scope | config
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "adapter": self.adapter,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class PromptSurfaceInventory:
    rows: tuple[InventoryRow, ...]

    def to_dict(self) -> dict:
        return {"rows": [r.to_dict() for r in self.rows]}


def build_inventory(sources, *, known_absent_checks: bool = True) -> PromptSurfaceInventory:
    from psa.discovery import Source

    sources = tuple(sources)
    paths = {s.path.replace("\\", "/") for s in sources}
    adapters_present = {s.adapter for s in sources}

    rows: list[InventoryRow] = []

    def has_instruction(adapter: str) -> bool:
        return any(s.adapter == adapter and s.subtype == "instruction" for s in sources)

    checks = [
        ("claude", "CLAUDE.md", "Claude instructions"),
        ("agents", "AGENTS.md", "AGENTS.md"),
        ("cursor_rules", "Cursor rules", "Cursor Rules"),
        ("copilot", "Copilot instructions", "Copilot Instructions"),
    ]
    for adapter, label, title in checks:
        if has_instruction(adapter):
            detail_paths = [
                s.path for s in sources if s.adapter == adapter and s.subtype == "instruction"
            ]
            rows.append(
                InventoryRow(
                    adapter=adapter,
                    label=title,
                    status="present",
                    detail=f"{len(detail_paths)} file(s)",
                )
            )
        else:
            rows.append(InventoryRow(adapter=adapter, label=title, status="absent", detail=""))

    for s in sources:
        if s.subtype == "config":
            rows.append(
                InventoryRow(
                    adapter=s.adapter,
                    label=s.path,
                    status="config",
                    detail="config (not instruction)",
                )
            )
        elif s.subtype == "data":
            rows.append(
                InventoryRow(
                    adapter=s.adapter,
                    label=s.path,
                    status="out_of_scope",
                    detail="data (not audited)",
                )
            )

    # stable order
    status_rank = {"present": 0, "config": 1, "absent": 2, "out_of_scope": 3}
    rows.sort(key=lambda r: (status_rank.get(r.status, 9), r.adapter, r.label))
    return PromptSurfaceInventory(rows=tuple(rows))


def render_inventory(inv: PromptSurfaceInventory) -> str:
    lines = ["Prompt Surface Inventory", ""]
    groups = {
        "present": "Discovered (instruction)",
        "config": "Discovered (config, not instruction)",
        "absent": "Not found",
        "out_of_scope": "Out of scope (data)",
    }
    for status, title in groups.items():
        group = [r for r in inv.rows if r.status == status]
        if not group:
            continue
        lines.append(title)
        # ASCII marks for Windows console compatibility
        mark = {"present": "[x]", "config": "[c]", "absent": "[ ]", "out_of_scope": "[-]"}[status]
        for r in group:
            extra = f"  {r.detail}" if r.detail else ""
            lines.append(f"  {mark} {r.label}{extra}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_human(audit) -> str:
    lines: list[str] = []
    lines.append("Prompt Structure Audit")
    lines.append("")
    lines.append(render_inventory(audit.inventory).rstrip())
    lines.append("")

    instruction_present = any(r.status == "present" for r in audit.inventory.rows)
    lines.append("Executive Summary")
    if not instruction_present:
        lines.append(
            "  No prompt instruction surface found "
            "(no CLAUDE.md / AGENTS.md / Cursor rules / Copilot instructions)."
        )
        lines.append("  Honest empty result: nothing to structurally audit.")
    else:
        by_pri: dict[str, int] = {}
        for f in audit.findings:
            by_pri[f.priority] = by_pri.get(f.priority, 0) + 1
        lines.append(f"  Findings: {len(audit.findings)}")
        for band in ("High value", "Medium value", "Low value", "Informational"):
            if band in by_pri:
                lines.append(f"  {band}: {by_pri[band]}")

    graph = getattr(audit, "dependency_graph", None)
    if graph and graph.roadmap:
        lines.append("")
        lines.append("Fix these first (roadmap)")
        # Headline: first unique rule ids in roadmap order (usability)
        seen_rules: list[str] = []
        headlines: list = []
        for n in graph.roadmap:
            if n.rule_id in seen_rules:
                continue
            seen_rules.append(n.rule_id)
            headlines.append(n)
            if len(headlines) >= 3:
                break
        for i, n in enumerate(headlines, 1):
            lines.append(f"  {i}. [{n.rule_id}] {n.action[:140]}")
        remaining_rules = [n.rule_id for n in graph.roadmap if n.rule_id not in seen_rules[:3]]
        # count unique remaining rule ids after the headline set
        extra = []
        for rid in [n.rule_id for n in graph.roadmap]:
            if rid not in {h.rule_id for h in headlines} and rid not in extra:
                extra.append(rid)
        if extra:
            lines.append(
                f"  ... then {len(extra)} more rule(s) after the above "
                "(see Implementation Roadmap)."
            )
        if graph.edges:
            lines.append("  Dependencies")
            seen: set[tuple[str, str]] = set()
            for e in graph.edges:
                key = (e.src_rule, e.dst_rule)
                if key in seen or not e.src_rule:
                    continue
                seen.add(key)
                lines.append(
                    f"    - Do not apply [{e.dst_rule}] until [{e.src_rule}] "
                    f"({e.reason})."
                )
    lines.append("")

    lines.append("Findings")
    if not audit.findings:
        lines.append("  (none)")
    else:
        for f in audit.findings:
            lines.append(
                f"[{f.rule_id}] {f.priority} · {f.verification} · {f.observability} · owner: {f.ownership}"
            )
            lines.append(f.title)
            lines.append("Evidence")
            for e in f.evidence:
                span = f"{e.span[0]}-{e.span[1]}" if e.span else "?"
                lines.append(f"  {e.path}:{span}  {e.excerpt!r}")
            lines.append("Why it matters")
            lines.append(f"  {f.explanation}")
            lines.append("Recommendation")
            lines.append(f"  {f.recommendation}")
            lines.append("")
    lines.append("Honesty note")
    lines.append(
        "  This audit reports structure observable from repository contents. "
        "It does not measure or predict cache hit rate, cost, or latency."
    )
    if graph and graph.roadmap:
        lines.append("")
        lines.append("Implementation Roadmap")
        for i, n in enumerate(graph.roadmap, 1):
            lines.append(f"  {i}. [{n.rule_id}] {n.action[:120]}")
        if graph.cycles:
            lines.append("  Cycles detected (not silently broken):")
            for c in graph.cycles:
                lines.append(f"    {', '.join(c)}")
    return "\n".join(lines).rstrip() + "\n"
