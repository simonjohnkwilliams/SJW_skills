"""Structural principles checklist embedded in the Advise brief."""
from __future__ import annotations

PRINCIPLES: tuple[dict[str, str], ...] = (
    {
        "id": "stable-before-volatile",
        "summary": "Keep durable standards and role guidance before session-dynamic content.",
    },
    {
        "id": "single-source-of-truth",
        "summary": "Avoid duplicated architectural guidance across instruction assets.",
    },
    {
        "id": "activation-clarity",
        "summary": "Rules and skills should make when-they-apply explicit (frontmatter / globs / description).",
    },
    {
        "id": "no-worklog-in-prefix",
        "summary": "Keep worklogs, status notes, and changelogs out of the reusable stable prefix.",
    },
    {
        "id": "instruction-vs-guidance",
        "summary": "Runtime Instruction Assets stay lean; narrative playbooks belong on the Guidance Surface.",
    },
    {
        "id": "evidence-backed",
        "summary": "Every advisory item must cite concrete paths the user can open.",
    },
)


def principles_for_brief() -> list[dict[str, str]]:
    return [dict(p) for p in PRINCIPLES]
