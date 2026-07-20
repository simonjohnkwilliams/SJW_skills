"""Documentation surface — AI-relevant guidance, not all Markdown."""
from __future__ import annotations

import re

# Filename / path tokens suggesting AI or assistant / prompt guidance.
# Applied after tool-tree exclusions so ".cursor/skills/..." does not inflate counts.
_AI_GUIDANCE = re.compile(
    r"(prompt|agents?|claude|cursor|copilot|llm|"
    r"ai[-_ ]?(guid|workflow|coding|assistant|prompt)|"
    r"coding[-_ ]?standard|assistant|system[-_ ]?prompt|"
    r"prompt[-_ ]?engineer|llm[-_ ]?guid|ai[-_ ]?guid)",
    re.IGNORECASE,
)

_DOC_EXTS = (".md", ".mdx", ".rst", ".adoc", ".txt")

# Installed skills, slash-commands, and agent packs are not project documentation.
_EXCLUDE_PREFIXES = (
    ".cursor/skills/",
    ".claude/skills/",
    ".claude/commands/",
    ".agents/",
    ".agents/skills/",
    "node_modules/",
    "vendor/",
)

# General project docs that must never inflate the Documentation metric.
_EXCLUDE_NAMES = frozenset(
    {
        "license",
        "license.md",
        "license.txt",
        "licence",
        "licence.md",
        "changelog",
        "changelog.md",
        "changelog.rst",
        "changes.md",
        "history.md",
        "news.md",
        "releases.md",
        "release-notes.md",
        "releasenotes.md",
        "contributing.md",
        "contribute.md",
        "code_of_conduct.md",
        "security.md",
        "authors.md",
        "readme",
        "readme.md",
        "readme.rst",
        "readme.txt",
        "todo.md",
        "roadmap.md",
        "skill.md",
    }
)

_EXCLUDE_PATH = re.compile(
    r"(^|/)("
    r"changelog|change[-_ ]?log|release[-_ ]?notes?|releases?|"
    r"api[-_ ]?(doc|docs|reference)|openapi|swagger|"
    r"contributing|code_of_conduct|license|licence|"
    r"research/"  # benchmark / research dumps — not architecture guidance
    r")",
    re.IGNORECASE,
)


def is_documentation_path(path: str, *, instruction_paths: set[str]) -> bool:
    """True if path is AI-/prompt-relevant documentation (not a runtime instruction)."""
    norm = path.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    if norm in instruction_paths:
        return False
    lower = norm.lower()
    name = norm.rsplit("/", 1)[-1]
    name_lower = name.lower()
    if not any(lower.endswith(ext) for ext in _DOC_EXTS):
        return False
    if name_lower in _EXCLUDE_NAMES:
        return False
    if any(lower.startswith(p) or f"/{p}" in f"/{lower}" for p in _EXCLUDE_PREFIXES):
        return False
    if _EXCLUDE_PATH.search(lower):
        return False
    if any(seg in ("node_modules", ".git", "vendor") for seg in norm.split("/")):
        return False
    # Require an AI-/prompt-guidance signal on the filename (not tool-dir path noise).
    # Also allow a path match when the file lives under a docs tree.
    under_docs = any(
        lower == d or lower.startswith(d)
        for d in ("docs/", "documentation/", "doc/")
    )
    if _AI_GUIDANCE.search(name):
        return True
    if under_docs and _AI_GUIDANCE.search(norm):
        return True
    return False


def collect_documentation(
    files: list[str],
    *,
    instruction_paths: set[str],
    ignored_paths: set[str] | None = None,
) -> tuple[str, ...]:
    ignored = ignored_paths or set()
    found: list[str] = []
    for path in files:
        norm = path.replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        if norm in ignored:
            continue
        if is_documentation_path(norm, instruction_paths=instruction_paths):
            found.append(norm)
    return tuple(sorted(set(found)))
