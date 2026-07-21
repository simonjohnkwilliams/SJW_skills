"""Advise judgment schema — structured output from the embedded AI caller."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

KIND_ADVISE = "advise"
KIND_CONFLICT = "conflict"
VALID_KINDS = frozenset({KIND_ADVISE, KIND_CONFLICT})


@dataclass(frozen=True)
class AdviseItem:
    id: str
    kind: str  # advise | conflict
    title: str
    reason: str
    paths: tuple[str, ...] = ()
    effort: str = "Medium"
    rule_seed_id: str = ""
    rule_seed_idea: str = ""
    conflicts_with: tuple[str, ...] = ()  # rule ids or finding ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "reason": self.reason,
            "paths": list(self.paths),
            "effort": self.effort,
            "rule_seed_id": self.rule_seed_id,
            "rule_seed_idea": self.rule_seed_idea,
            "conflicts_with": list(self.conflicts_with),
        }

    @staticmethod
    def from_dict(d: dict[str, Any], *, index: int) -> AdviseItem:
        kind = str(d.get("kind", KIND_ADVISE)).strip().lower()
        if kind in {"investigate", "investigation"}:
            kind = KIND_CONFLICT
        if kind not in VALID_KINDS:
            kind = KIND_ADVISE
        raw_id = str(d.get("id") or "").strip()
        item_id = raw_id or f"ADV{index:03d}"
        paths = d.get("paths") or d.get("path") or []
        if isinstance(paths, str):
            path_tuple = (paths,)
        else:
            path_tuple = tuple(str(p) for p in paths if str(p).strip())
        conflicts = d.get("conflicts_with") or []
        if isinstance(conflicts, str):
            conflict_tuple = (conflicts,)
        else:
            conflict_tuple = tuple(str(c) for c in conflicts if str(c).strip())
        return AdviseItem(
            id=item_id,
            kind=kind,
            title=str(d.get("title") or d.get("recommendation") or "Untitled").strip(),
            reason=str(d.get("reason") or d.get("rationale") or "").strip(),
            paths=path_tuple,
            effort=str(d.get("effort") or d.get("estimated_effort") or "Medium").strip()
            or "Medium",
            rule_seed_id=str(d.get("rule_seed_id") or "").strip(),
            rule_seed_idea=str(
                d.get("rule_seed_idea") or d.get("detection_idea") or ""
            ).strip(),
            conflicts_with=conflict_tuple,
        )


@dataclass(frozen=True)
class AdviseJudgment:
    items: tuple[AdviseItem, ...] = ()
    summary_theme: str = ""
    notes: str = ""

    def advise_items(self) -> tuple[AdviseItem, ...]:
        return tuple(i for i in self.items if i.kind == KIND_ADVISE)

    def conflict_items(self) -> tuple[AdviseItem, ...]:
        return tuple(i for i in self.items if i.kind == KIND_CONFLICT)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_theme": self.summary_theme,
            "notes": self.notes,
            "items": [i.to_dict() for i in self.items],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> AdviseJudgment:
        raw_items = d.get("items") or d.get("recommendations") or []
        items: list[AdviseItem] = []
        for idx, raw in enumerate(raw_items, 1):
            if isinstance(raw, dict):
                items.append(AdviseItem.from_dict(raw, index=idx))
        theme = str(d.get("summary_theme") or d.get("theme") or "").strip()
        if not theme and items:
            theme = items[0].title
        return AdviseJudgment(
            items=tuple(items),
            summary_theme=theme,
            notes=str(d.get("notes") or "").strip(),
        )


def empty_judgment() -> AdviseJudgment:
    return AdviseJudgment()
