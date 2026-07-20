"""Core Engine pipeline: discover → model → rules → findings → audit."""
from __future__ import annotations

from dataclasses import dataclass

from psa import __version__
from psa.core.config import DEFAULT_CONFIG, ConfigView
from psa.core.ports import RepoFS
from psa.discovery import discover
from psa.findings import Finding, normalize_findings
from psa.model.builder import build_model
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

    def to_dict(self) -> dict:
        return {
            "meta": self.meta.to_dict(),
            "inventory": self.inventory.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "dependency_graph": {"nodes": [], "edges": []},
        }


def analyze(
    repo: RepoFS,
    config: ConfigView | None = None,
    tool_version: str | None = None,
) -> Audit:
    cfg = config or DEFAULT_CONFIG
    version = tool_version or __version__
    sources = discover(repo)
    model = build_model(sources)
    raw = run_rules(model, cfg)
    findings = normalize_findings(raw)
    inventory = build_inventory(sources)
    return Audit(
        meta=RunMeta(
            tool_version=version,
            schema_version="0.1.0",
            config_hash=cfg.hash(),
        ),
        findings=findings,
        inventory=inventory,
    )
