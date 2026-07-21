"""PSA Advise — AI-assisted advisory scout (Release 5).

Judgment comes from an embedded AI bridge (see BRIDGE.md). PSA builds the
deterministic brief, renders the Plan-shaped report, and persists backlog.
"""
from __future__ import annotations

from psa.advise.brief import build_advise_brief
from psa.advise.bridge import (
    BRIDGE_MISSING_MSG,
    BridgeUnavailableError,
    bridge_available,
)
from psa.advise.persist import load_advise, save_advise
from psa.advise.schema import AdviseJudgment, AdviseItem

__all__ = [
    "AdviseItem",
    "AdviseJudgment",
    "BRIDGE_MISSING_MSG",
    "BridgeUnavailableError",
    "AdviseResult",
    "bridge_available",
    "build_advise_brief",
    "load_advise",
    "run_advise",
    "save_advise",
    "try_post_apply_one_liner",
]


def __getattr__(name: str):
    if name in {"AdviseResult", "run_advise", "try_post_apply_one_liner"}:
        from psa.advise import engine as _engine

        return getattr(_engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
