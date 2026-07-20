"""Recommendation dependency graph (RFC §9.7)."""
from __future__ import annotations

from dataclasses import dataclass

from psa.findings import Finding


@dataclass(frozen=True)
class Recommendation:
    finding_id: str
    rule_id: str
    action: str
    owner: str

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "action": self.action,
            "owner": self.owner,
        }


@dataclass(frozen=True)
class RecEdge:
    src: str  # finding_id
    dst: str
    relation: str  # enables | supersedes | conflicts
    reason: str
    src_rule: str = ""
    dst_rule: str = ""

    def to_dict(self) -> dict:
        return {
            "src": self.src,
            "dst": self.dst,
            "relation": self.relation,
            "reason": self.reason,
            "src_rule": self.src_rule,
            "dst_rule": self.dst_rule,
        }


@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[Recommendation, ...]
    edges: tuple[RecEdge, ...]
    roadmap: tuple[Recommendation, ...]
    cycles: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "roadmap": [n.to_dict() for n in self.roadmap],
            "cycles": [list(c) for c in self.cycles],
        }


# Prefer applying these rule families before ORDER when both exist.
_ENABLES: tuple[tuple[str, str, str], ...] = (
    ("DUP001", "ORDER001", "Consolidate duplicates before reordering once"),
    ("ACT001", "ORDER001", "Fix activation before judging ordering of rule body"),
    ("ACT002", "ORDER001", "Add frontmatter before ordering analysis of the rule"),
    ("STYLE001", "ORDER001", "Split worklog before reordering remaining durable content"),
)


def build_recommendations(findings: tuple[Finding, ...]) -> DependencyGraph:
    nodes: list[Recommendation] = []
    for f in findings:
        if f.ownership != "user":
            continue
        nodes.append(
            Recommendation(
                finding_id=f.id,
                rule_id=f.rule_id,
                action=f.recommendation,
                owner=f.ownership,
            )
        )
    by_rule: dict[str, list[Recommendation]] = {}
    for n in nodes:
        by_rule.setdefault(n.rule_id, []).append(n)

    edges: list[RecEdge] = []
    for src_rule, dst_rule, reason in _ENABLES:
        for src in by_rule.get(src_rule, []):
            for dst in by_rule.get(dst_rule, []):
                if src.finding_id == dst.finding_id:
                    continue
                edges.append(
                    RecEdge(
                        src=src.finding_id,
                        dst=dst.finding_id,
                        relation="enables",
                        reason=reason,
                        src_rule=src_rule,
                        dst_rule=dst_rule,
                    )
                )

    nodes_t = tuple(sorted(nodes, key=lambda n: (n.rule_id, n.finding_id)))
    edges_t = tuple(sorted(edges, key=lambda e: (e.src, e.dst, e.relation)))
    roadmap, cycles = _topo(nodes_t, edges_t)
    return DependencyGraph(nodes=nodes_t, edges=edges_t, roadmap=roadmap, cycles=cycles)


def _topo(
    nodes: tuple[Recommendation, ...],
    edges: tuple[RecEdge, ...],
) -> tuple[tuple[Recommendation, ...], tuple[tuple[str, ...], ...]]:
    ids = [n.finding_id for n in nodes]
    by_id = {n.finding_id: n for n in nodes}
    succ: dict[str, list[str]] = {i: [] for i in ids}
    indeg: dict[str, int] = {i: 0 for i in ids}
    for e in edges:
        if e.src not in indeg or e.dst not in indeg:
            continue
        succ[e.src].append(e.dst)
        indeg[e.dst] += 1

    # Kahn with deterministic tie-break on finding_id
    ready = sorted([i for i, d in indeg.items() if d == 0])
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m in sorted(succ[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
                ready.sort()

    remaining = [i for i in ids if i not in order]
    cycles: list[tuple[str, ...]] = []
    if remaining:
        # report one cycle component (deterministic sorted remaining as flagged set)
        cycles.append(tuple(sorted(remaining)))
        # still emit remaining after acyclic prefix, sorted
        order.extend(sorted(remaining))

    roadmap = tuple(by_id[i] for i in order if i in by_id)
    return roadmap, tuple(cycles)
