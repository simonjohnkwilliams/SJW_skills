"""Minimal config view — defaults only for v0.1."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from psa.core.canon import dumps
from psa.core.ids import content_id


@dataclass(frozen=True)
class ConfigView:
    enabled_packs: tuple[str, ...] = (
        "ORDERING",
        "VOLATILITY",
        "DUPLICATION",
        "ACTIVATION",
        "STYLE",
        "OWNERSHIP",
        "CONTRADICTION",
    )
    extra: Mapping[str, object] = field(default_factory=dict)

    def hash(self) -> str:
        return content_id(dumps({"enabled_packs": list(self.enabled_packs), "extra": dict(self.extra)}))


DEFAULT_CONFIG = ConfigView()
