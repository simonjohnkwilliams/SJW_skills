"""Persist Advise results to .psa/advise.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psa import __version__
from psa.advise.schema import AdviseItem, AdviseJudgment
from psa.optimise.state import STATE_DIR

ADVISE_FILE = "advise.json"


def advise_path(repo_root: Path) -> Path:
    return repo_root / STATE_DIR / ADVISE_FILE


@dataclass
class AdviseSnapshot:
    schema_version: str = "1.0.0"
    psa_version: str = __version__
    repository: str = ""
    created_at: str = ""
    summary_theme: str = ""
    notes: str = ""
    items: list[AdviseItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "psa_version": self.psa_version,
            "repository": self.repository,
            "created_at": self.created_at,
            "summary_theme": self.summary_theme,
            "notes": self.notes,
            "items": [i.to_dict() for i in self.items],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> AdviseSnapshot:
        items = [
            AdviseItem.from_dict(raw, index=i)
            for i, raw in enumerate(d.get("items") or [], 1)
            if isinstance(raw, dict)
        ]
        return AdviseSnapshot(
            schema_version=str(d.get("schema_version", "1.0.0")),
            psa_version=str(d.get("psa_version", "")),
            repository=str(d.get("repository", "")),
            created_at=str(d.get("created_at", "")),
            summary_theme=str(d.get("summary_theme", "")),
            notes=str(d.get("notes", "")),
            items=items,
        )

    def judgment(self) -> AdviseJudgment:
        return AdviseJudgment(
            items=tuple(self.items),
            summary_theme=self.summary_theme,
            notes=self.notes,
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save_advise(
    repo_root: Path,
    judgment: AdviseJudgment,
    *,
    repo_name: str,
) -> Path:
    root = repo_root.resolve()
    (root / STATE_DIR).mkdir(parents=True, exist_ok=True)
    snap = AdviseSnapshot(
        psa_version=__version__,
        repository=repo_name,
        created_at=utc_now(),
        summary_theme=judgment.summary_theme,
        notes=judgment.notes,
        items=list(judgment.items),
    )
    path = advise_path(root)
    path.write_text(json.dumps(snap.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_advise(repo_root: Path) -> AdviseSnapshot | None:
    path = advise_path(repo_root.resolve())
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return AdviseSnapshot.from_dict(data)
