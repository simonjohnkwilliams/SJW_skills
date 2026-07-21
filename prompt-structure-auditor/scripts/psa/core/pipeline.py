"""Core Engine pipeline: discover → model → rules → findings → recommend → audit."""
from __future__ import annotations

from dataclasses import dataclass

from psa import __version__
from psa.core.config import DEFAULT_CONFIG, ConfigView
from psa.core.ports import RepoFS
from psa.discovery import discover
from psa.findings import Finding, normalize_findings
from psa.model.builder import build_model
from psa.recommend.graph import DependencyGraph, build_recommendations
from psa.report.inventory import PromptSurfaceInventory, build_inventory
from psa.rules import run_rules


@dataclass(frozen=True)
class RunMeta:
    tool_version: str
    schema_version: str
    config_hash: str

    def to_dict(self) -> dict:
        return {
            "tool_version": self.tool_version,
            "schema_version": self.schema_version,
            "config_hash": self.config_hash,
        }


@dataclass(frozen=True)
class Audit:
    meta: RunMeta
    findings: tuple[Finding, ...]
    inventory: PromptSurfaceInventory
    dependency_graph: DependencyGraph
    guidance: tuple[str, ...] = ()

    @property
    def documentation(self) -> tuple[str, ...]:
        """Legacy alias for guidance (Guidance Surface)."""
        return self.guidance

    def to_dict(self) -> dict:
        return {
            "meta": self.meta.to_dict(),
            "inventory": self.inventory.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "dependency_graph": self.dependency_graph.to_dict(),
            "guidance": list(self.guidance),
        }


def analyze(
    repo: RepoFS,
    config: ConfigView | None = None,
    tool_version: str | None = None,
) -> Audit:
    cfg = config or DEFAULT_CONFIG
    version = tool_version or __version__
    discovered = discover(repo, cfg)
    sources = discovered.sources
    model = build_model(sources)
    raw = run_rules(model, cfg)
    findings = normalize_findings(raw)
    findings = _annotate_regressions(repo, findings)
    inventory = build_inventory(sources, ignored=discovered.ignored)
    graph = build_recommendations(findings)
    return Audit(
        meta=RunMeta(
            tool_version=version,
            schema_version="0.1.0",
            config_hash=cfg.hash(),
        ),
        findings=findings,
        inventory=inventory,
        dependency_graph=graph,
        guidance=discovered.guidance,
    )


def _annotate_regressions(
    repo: RepoFS,
    findings: tuple[Finding, ...],
) -> tuple[Finding, ...]:
    """If optimisation state exists, mark findings that reintroduce completed work."""
    try:
        from pathlib import Path

        from psa.optimise.state import load_state
        from psa.recommend.graph import optimisation_id_for
    except ImportError:
        return findings

    try:
        root = Path(repo.root())
    except Exception:  # noqa: BLE001
        return findings
    state = load_state(root)
    if state is None or not state.completed:
        return findings
    done = state.completed_ids()
    out: list[Finding] = []
    for f in findings:
        oid = optimisation_id_for(f.rule_id)
        if oid not in done:
            out.append(f)
            continue
        note = (
            f"Regression detected. Previously completed optimisation {oid} "
            f"has been reintroduced. "
        )
        out.append(
            Finding(
                id=f.id,
                rule_id=f.rule_id,
                title=f.title,
                category=f.category,
                priority=f.priority,
                verification=f.verification,
                observability=f.observability,
                confidence=f.confidence,
                ownership=f.ownership,
                evidence=f.evidence,
                explanation=note + f.explanation,
                recommendation=f.recommendation,
                related=f.related,
                patchable=f.patchable,
            )
        )
    return tuple(out)
