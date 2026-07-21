"""Persistent optimisation state (.psa/state.json).

Authoritative for execution progress only — never replaces Audit analysis.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psa import __version__
from psa.core.ports import RepoFS

STATE_DIR = ".psa"
STATE_FILE = "state.json"
SCHEMA_VERSION = "1.0.0"
OPTIMISE_BRANCH = "psa/optimise"


@dataclass(frozen=True)
class CompletedOptimisation:
    optimisation_id: str
    title: str
    completed_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "optimisation_id": self.optimisation_id,
            "title": self.title,
            "completed_at": self.completed_at,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> CompletedOptimisation:
        return CompletedOptimisation(
            optimisation_id=str(d["optimisation_id"]),
            title=str(d.get("title", "")),
            completed_at=str(d.get("completed_at", "")),
        )


@dataclass(frozen=True)
class OutstandingOptimisation:
    optimisation_id: str
    title: str

    def to_dict(self) -> dict[str, str]:
        return {
            "optimisation_id": self.optimisation_id,
            "title": self.title,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> OutstandingOptimisation:
        return OutstandingOptimisation(
            optimisation_id=str(d["optimisation_id"]),
            title=str(d.get("title", "")),
        )


@dataclass
class OptimisationState:
    schema_version: str = SCHEMA_VERSION
    psa_version: str = __version__
    fingerprint: str = ""
    completed: list[CompletedOptimisation] = field(default_factory=list)
    outstanding: list[OutstandingOptimisation] = field(default_factory=list)
    last_audit_at: str = ""
    last_plan_at: str = ""
    last_apply_at: str = ""
    status: str = "idle"  # idle | in_progress | blocked | complete
    last_block_reason: str = ""

    def completed_ids(self) -> set[str]:
        return {c.optimisation_id for c in self.completed}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "psa_version": self.psa_version,
            "fingerprint": self.fingerprint,
            "completed": [c.to_dict() for c in self.completed],
            "outstanding": [o.to_dict() for o in self.outstanding],
            "last_audit_at": self.last_audit_at,
            "last_plan_at": self.last_plan_at,
            "last_apply_at": self.last_apply_at,
            "status": self.status,
            "last_block_reason": self.last_block_reason,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> OptimisationState:
        return OptimisationState(
            schema_version=str(d.get("schema_version", SCHEMA_VERSION)),
            psa_version=str(d.get("psa_version", __version__)),
            fingerprint=str(d.get("fingerprint", "")),
            completed=[
                CompletedOptimisation.from_dict(c) for c in d.get("completed", [])
            ],
            outstanding=[
                OutstandingOptimisation.from_dict(o) for o in d.get("outstanding", [])
            ],
            last_audit_at=str(d.get("last_audit_at", "")),
            last_plan_at=str(d.get("last_plan_at", "")),
            last_apply_at=str(d.get("last_apply_at", "")),
            status=str(d.get("status", "idle")),
            last_block_reason=str(d.get("last_block_reason", "")),
        )


def state_path(repo_root: Path) -> Path:
    return repo_root / STATE_DIR / STATE_FILE


def load_state(repo_root: Path) -> OptimisationState | None:
    path = state_path(repo_root)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return OptimisationState.from_dict(data)


def save_state(repo_root: Path, state: OptimisationState) -> Path:
    path = state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_fingerprint(repo: RepoFS) -> str:
    """Hash instruction-ish files for 'repo changed under us' checks."""
    h = hashlib.sha256()
    paths = sorted(
        p.replace("\\", "/")
        for p in repo.list_files()
        if _fingerprint_path(p.replace("\\", "/"))
    )
    for path in paths:
        try:
            text = repo.read_text(path)
        except OSError:
            continue
        h.update(path.encode("utf-8"))
        h.update(b"\0")
        h.update(text.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:32]


def _fingerprint_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    if name in {"claude.md", "agents.md", "copilot-instructions.md"}:
        return True
    if path.startswith(".cursor/rules/") and path.endswith((".mdc", ".md")):
        return True
    if path.startswith(".claude/") and name.endswith(".md"):
        return True
    return False
