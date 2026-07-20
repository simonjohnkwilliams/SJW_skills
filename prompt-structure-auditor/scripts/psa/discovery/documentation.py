"""Documentation surface — AI-relevant docs that are not runtime instructions."""
from __future__ import annotations

import re

# Directory prefixes (repo-relative) treated as documentation trees.
_DOC_DIRS = ("docs/", "documentation/", "doc/")

# Filename / path tokens suggesting AI or assistant guidance.
_AI_GUIDANCE = re.compile(
    r"(prompt|agents?|claude|cursor|copilot|llm|ai[-_ ]?guid|"
    r"coding[-_ ]?standard|assistant|system[-_ ]?prompt)",
    re.IGNORECASE,
)

_DOC_EXTS = (".md", ".mdx", ".rst", ".adoc", ".txt")


def is_documentation_path(path: str, *, instruction_paths: set[str]) -> bool:
    """True if path looks like AI-relevant documentation (not a runtime instruction)."""
    norm = path.replace("\\", "/").lstrip("./")
    if norm in instruction_paths:
        return False
    lower = norm.lower()
    name = norm.rsplit("/", 1)[-1]
    if not any(lower.endswith(ext) for ext in _DOC_EXTS):
        return False
    # Skip lockfiles / obvious non-prose
    if name.lower() in {"license", "license.md", "changelog.md", "changelog"}:
        return False
    under_docs = any(
        lower == d.rstrip("/") or lower.startswith(d) for d in _DOC_DIRS
    )
    if under_docs:
        return True
    # Root or nested files whose names suggest AI guidance
    if _AI_GUIDANCE.search(name) or _AI_GUIDANCE.search(norm):
        # Avoid counting vendor/node trees already ignored elsewhere
        if any(seg in ("node_modules", ".git", "vendor") for seg in norm.split("/")):
            return False
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
        if norm in ignored:
            continue
        if is_documentation_path(norm, instruction_paths=instruction_paths):
            found.append(norm)
    return tuple(sorted(set(found)))
