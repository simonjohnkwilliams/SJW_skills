"""Discovery: source adapters (RFC §5)."""
from __future__ import annotations

from dataclasses import dataclass

from psa.core.ports import RepoFS


@dataclass(frozen=True)
class Source:
    source_id: str
    adapter: str
    subtype: str  # instruction | config | data
    path: str
    text: str
    default_ownership: str
    order_hint: int


def _norm(path: str) -> str:
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def discover(repo: RepoFS) -> tuple[Source, ...]:
    files = [_norm(p) for p in repo.list_files()]
    found: list[Source] = []
    order = 0

    def add(adapter: str, subtype: str, path: str, ownership: str, text: str = "") -> None:
        nonlocal order
        found.append(
            Source(
                source_id=f"{adapter}:{path}",
                adapter=adapter,
                subtype=subtype,
                path=path,
                text=text,
                default_ownership=ownership,
                order_hint=order,
            )
        )
        order += 1

    for path in files:
        lower = path.lower()
        name = path.rsplit("/", 1)[-1]

        if name.upper() in {"CLAUDE.MD", "CLAUDE.LOCAL.MD"} or name == "CLAUDE.md":
            add("claude", "instruction", path, "user", repo.read_text(path))
            continue
        if name == "CLAUDE.local.md":
            add("claude", "instruction", path, "user", repo.read_text(path))
            continue
        if name == "AGENTS.md":
            add("agents", "instruction", path, "user", repo.read_text(path))
            continue
        if "/.cursor/rules/" in f"/{path}" or path.startswith(".cursor/rules/"):
            if path.endswith((".mdc", ".md")):
                add("cursor_rules", "instruction", path, "user", repo.read_text(path))
                continue
            # nested junk under rules → config
            add("cursor_rules", "config", path, "unknown", "")
            continue
        if path.endswith("copilot-instructions.md"):
            add("copilot", "instruction", path, "user", repo.read_text(path))
            continue
        if path.startswith(".serena/") or "/.serena/" in path:
            # only project yml files as config markers
            if path.endswith((".yml", ".yaml")):
                add("serena", "config", path, "tool", "")
            continue
        if path.startswith(".opencode/") or "/.opencode/" in path:
            if path.endswith((".json", ".yaml", ".yml")) and "package-lock" not in path:
                add("opencode", "config", path, "tool", "")
            continue
        if path.startswith(".claude/skills/") or "/.claude/skills/" in path:
            # Tool-owned skill trees — do not enumerate every asset as a source.
            continue
        if path.startswith(".claude/") and path.endswith(".json"):
            add("claude_settings", "config", path, "tool", "")
            continue
        if path.startswith(".agents/") or "/.agents/" in path:
            # Installed skills — ownership tool; skip bulk enumeration in v0.1
            continue
        if "/research/" in f"/{path}" and path.endswith((".json", ".log")):
            add("research_data", "data", path, "unknown", "")
            continue
        if "claude-stdout.json" in name or "claude_dot_json" in name:
            add("research_data", "data", path, "unknown", "")
            continue

    return tuple(sorted(found, key=lambda s: (s.order_hint, s.path)))
