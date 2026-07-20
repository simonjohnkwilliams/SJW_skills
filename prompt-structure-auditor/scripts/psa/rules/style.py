"""STYLE pack — instruction file used as worklog."""
from __future__ import annotations

import re
from typing import Iterable

from psa.core.config import ConfigView
from psa.core.ids import finding_id
from psa.findings import Finding
from psa.model.types import Evidence, PromptModel


_WORKLOG = re.compile(r"(?i)\b(decision:|debugging|known\s+issue|on\s+hold|current\s+focus)\b")


def check_style001(model: PromptModel, _config: ConfigView) -> Iterable[Finding]:
    by_path: dict[str, list] = {}
    for seg in model.segments:
        if seg.provenance.path.endswith((".md",)):
            by_path.setdefault(seg.provenance.path, []).append(seg)

    findings: list[Finding] = []
    for path, segs in sorted(by_path.items()):
        if not path.endswith("AGENTS.md") and "AGENTS" not in path.upper():
            # focus on instruction files; still allow CLAUDE.md
            if not path.upper().endswith("CLAUDE.MD"):
                continue
        volatileish = 0
        for seg in segs:
            blob = " ".join(seg.provenance.anchor) + "\n" + seg.text
            if _WORKLOG.search(blob) or seg.stability == "volatile":
                volatileish += 1
        if volatileish >= 2 and len(segs) >= 3:
            excerpt = "worklog/decision narrative dominates instruction file"
            fid = finding_id(
                rule_id="STYLE001",
                path=path,
                anchor=("document",),
                excerpt=excerpt,
            )
            findings.append(
                Finding(
                    id=fid,
                    rule_id="STYLE001",
                    title="Instruction file used as running worklog",
                    category="STYLE",
                    priority="High value",
                    verification="confirmed",
                    observability="observable",
                    confidence="high",
                    ownership="user",
                    evidence=(Evidence(path=path, span=None, excerpt=excerpt),),
                    explanation=(
                        "Session narrative and debugging history are volatile and erode "
                        "the stable prefix and maintainability of the instruction file."
                    ),
                    recommendation=(
                        "Split durable guidance from the volatile worklog; keep dynamic "
                        "status near the end or in a separate notes file."
                    ),
                    patchable=False,
                )
            )
    return findings
