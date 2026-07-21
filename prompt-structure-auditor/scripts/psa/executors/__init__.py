"""Pluggable optimisation executors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from psa.core.pipeline import Audit
from psa.core.ports import RepoFS
from psa.patch.generate import Patch, preview_patch
from psa.recommend.graph import PlanRecommendation, optimisation_id_for


class Executor(Protocol):
    optimisation_id: str

    def can_apply(self, rec: PlanRecommendation, audit: Audit) -> bool: ...

    def build(
        self, repo: RepoFS, audit: Audit, rec: PlanRecommendation
    ) -> tuple[Patch, ...]: ...


@dataclass(frozen=True)
class Order001Executor:
    optimisation_id: str = "opt:ORDER001"

    def can_apply(self, rec: PlanRecommendation, audit: Audit) -> bool:
        return "ORDER001" in rec.rule_ids and bool(rec.addresses)

    def build(
        self, repo: RepoFS, audit: Audit, rec: PlanRecommendation
    ) -> tuple[Patch, ...]:
        # One patch per addressed ORDER001 finding (usually one).
        patches: list[Patch] = []
        for fid in rec.addresses:
            finding = next((f for f in audit.findings if f.id == fid), None)
            if finding is None or finding.rule_id != "ORDER001":
                continue
            patches.append(preview_patch(repo, audit, fid))
        if not patches:
            raise ValueError("ORDER001 executor: no applicable findings")
        return tuple(patches)


_REGISTRY: dict[str, Executor] = {
    "opt:ORDER001": Order001Executor(),
}


def register_executor(executor: Executor) -> None:
    _REGISTRY[executor.optimisation_id] = executor


def get_executor(optimisation_id: str) -> Executor | None:
    return _REGISTRY.get(optimisation_id)


def has_executor(optimisation_id: str) -> bool:
    return optimisation_id in _REGISTRY


def executor_for_recommendation(rec: PlanRecommendation) -> Executor | None:
    oid = rec.optimisation_id or (
        optimisation_id_for(rec.rule_ids[0]) if rec.rule_ids else ""
    )
    return get_executor(oid) if oid else None


def registered_optimisation_ids() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY.keys()))
