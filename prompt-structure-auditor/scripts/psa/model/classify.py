"""Stability / content classification (RFC §6.4)."""
from __future__ import annotations

import re
from dataclasses import dataclass


_VOLATILE_HEADING = re.compile(
    r"(?i)\b(current\s+focus|current\s+sprint|current\s+task|today|timestamp|"
    r"session|known\s+issue|decision:|debugging|on\s+hold|status)\b"
)
_VOLATILE_BODY = re.compile(
    r"(?i)\b(current\s+sprint|build\s+#?\d+|ticket\s+#?\d+|session\s+counter)\b"
)
_REFERENCE_PATH = re.compile(r"(?i)_bmad-output/|planning-artifacts|implementation artefact")


@dataclass(frozen=True)
class ClassifyResult:
    stability: str
    content_kind: str
    volatility_signals: tuple[str, ...]
    confidence: str


def classify_section(heading: str, body: str) -> ClassifyResult:
    signals: list[str] = []
    # References to volatile *paths* do not make the instruction volatile.
    body_for_volatility = _REFERENCE_PATH.sub("", body)

    if _VOLATILE_HEADING.search(heading):
        signals.append(f"heading:{heading.strip()}")
    for m in _VOLATILE_BODY.finditer(body_for_volatility):
        signals.append(f"body:{m.group(0)}")

    # Worklog / decision narrative markers
    if re.search(r"(?i)\b(decision:|debugging|known\s+issue|on\s+hold)\b", heading):
        if f"heading:{heading.strip()}" not in signals:
            signals.append(f"heading:{heading.strip()}")

    if signals:
        return ClassifyResult(
            stability="volatile",
            content_kind="state",
            volatility_signals=tuple(signals),
            confidence="high",
        )

    # Stable defaults for standards / architecture / instructions
    kind = "instruction"
    if re.search(r"(?i)\b(format|standard|architecture|convention|csv)\b", heading):
        kind = "standard"
    return ClassifyResult(
        stability="stable",
        content_kind=kind,
        volatility_signals=(),
        confidence="high",
    )
