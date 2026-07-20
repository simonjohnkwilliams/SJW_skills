"""Unit/behaviour tests for recommendation dependency graph."""
from __future__ import annotations

from tests.conftest import FIXTURES

from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.recommend.graph import build_recommendations


def test_recommendations_only_for_user_owned_findings():
    audit = analyze(LocalRepoFS(FIXTURES / "vr3_demo"), tool_version="0.1.0")
    graph = build_recommendations(audit.findings)
    assert graph.nodes
    assert all(n.owner == "user" for n in graph.nodes)


def test_roadmap_not_priority_only_when_dup_and_order():
    audit = analyze(LocalRepoFS(FIXTURES / "vr3_demo"), tool_version="0.1.0")
    graph = build_recommendations(audit.findings)
    rule_order = [n.rule_id for n in graph.roadmap]
    # If both present, DUP should appear before ORDER in roadmap when edged
    if "DUP001" in rule_order and "ORDER001" in rule_order:
        assert rule_order.index("DUP001") < rule_order.index("ORDER001") or any(
            e.relation == "enables" and e.src_rule == "DUP001" and e.dst_rule == "ORDER001"
            for e in graph.edges
        )


def test_cycles_reported():
    from psa.findings import Finding
    from psa.model.types import Evidence
    from psa.recommend.graph import DependencyGraph, RecEdge, Recommendation, _topo

    nodes = (
        Recommendation("a", "ORDER001", "do a", "user"),
        Recommendation("b", "DUP001", "do b", "user"),
    )
    edges = (
        RecEdge("a", "b", "enables", "a before b", "ORDER001", "DUP001"),
        RecEdge("b", "a", "enables", "b before a", "DUP001", "ORDER001"),
    )
    order, cycles = _topo(nodes, edges)
    assert cycles
    assert len(cycles[0]) >= 2
