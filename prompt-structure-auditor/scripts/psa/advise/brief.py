"""Deterministic Advise brief — input for the embedded AI caller."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from psa.advise.principles import principles_for_brief
from psa.core.pipeline import Audit
from psa.core.ports import RepoFS
from psa.optimise.state import OptimisationState, load_state
from psa.recommend.graph import deterministic_rule_catalog

# Soft cap per file excerpt so the brief stays usable in agent context.
_EXCERPT_CHARS = 1200
_MAX_INSTRUCTION_FILES = 40
_MAX_GUIDANCE_FILES = 30


def build_advise_brief(
    audit: Audit,
    *,
    repo_name: str,
    repo: RepoFS | None = None,
    repo_root: Path | None = None,
    state: OptimisationState | None = None,
) -> dict[str, Any]:
    """Build the deterministic brief the embedded AI must judge against."""
    opt_state = state
    if opt_state is None and repo_root is not None:
        opt_state = load_state(repo_root)

    rule_catalog = list(deterministic_rule_catalog())
    excluded_rule_ids = sorted({f.rule_id for f in audit.findings})
    plan = getattr(audit.dependency_graph, "plan", ()) or ()
    outstanding = [
        {
            "id": p.id,
            "optimisation_id": p.optimisation_id,
            "title": p.title,
            "rule_ids": list(p.rule_ids),
        }
        for p in plan
    ]
    completed: list[dict[str, str]] = []
    if opt_state is not None:
        completed = [
            {
                "optimisation_id": c.optimisation_id,
                "title": c.title,
                "completed_at": c.completed_at,
            }
            for c in opt_state.completed
        ]

    return {
        "schema": "psa.advise.brief.v1",
        "repository": repo_name,
        "tool_version": audit.meta.tool_version,
        "mission": (
            "Identify structural gaps in how AI instruction content is organised "
            "that are NOT already covered by the deterministic rule catalog or "
            "outstanding plan. Propose promotable future rules. If your advice "
            "contradicts a deterministic finding or rule, emit kind=conflict."
        ),
        "principles": principles_for_brief(),
        "rule_catalog": rule_catalog,
        "do_not_restate": {
            "rule_ids_with_open_findings": excluded_rule_ids,
            "outstanding_plan": outstanding,
            "instruction": (
                "Do not recommend fixes already expressed by these rules or plan "
                "steps. Look for gaps and contradictions only."
            ),
        },
        "completed_optimisations": completed,
        "instruction_assets": _instruction_entries(audit, repo),
        "guidance_surface": _guidance_entries(audit, repo),
        "output_contract": {
            "summary_theme": (
                "One short thematic phrase for post-Apply one-liner "
                "(e.g. 'Possible missing activation clarity in .cursor/rules')"
            ),
            "items": [
                {
                    "id": "ADV001",
                    "kind": "advise | conflict",
                    "title": "short recommendation title",
                    "reason": "why this matters",
                    "paths": ["relative/path"],
                    "effort": "Small | Medium | Large",
                    "rule_seed_id": "optional future rule id hint",
                    "rule_seed_idea": "how a deterministic detector could catch this",
                    "conflicts_with": ["ORDER001"],
                }
            ],
        },
    }


def _instruction_entries(audit: Audit, repo: RepoFS | None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in audit.inventory.rows:
        if row.status != "present":
            continue
        rel = row.label.replace("\\", "/")
        if "/" not in rel and not rel.endswith(".md"):
            # Absent-family placeholders use titles like "Claude instructions"
            continue
        if rel in seen:
            continue
        seen.add(rel)
        entries.append(_file_entry(rel, repo))
        if len(entries) >= _MAX_INSTRUCTION_FILES:
            break
    if entries:
        return entries
    for f in audit.findings:
        for ev in f.evidence:
            if not ev.path:
                continue
            rel = ev.path.replace("\\", "/")
            if rel in seen:
                continue
            seen.add(rel)
            entries.append(_file_entry(rel, repo))
            if len(entries) >= _MAX_INSTRUCTION_FILES:
                break
    return entries


def _guidance_entries(audit: Audit, repo: RepoFS | None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in audit.guidance[:_MAX_GUIDANCE_FILES]:
        rel = path.replace("\\", "/")
        entries.append(_file_entry(rel, repo, guidance=True))
    return entries


def _file_entry(
    rel: str, repo: RepoFS | None, *, guidance: bool = False
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": rel,
        "surface": "guidance" if guidance else "instruction",
    }
    if repo is None:
        return entry
    try:
        text = repo.read_text(rel)
    except (OSError, KeyError, ValueError, FileNotFoundError):
        entry["excerpt"] = ""
        entry["missing"] = True
        return entry
    excerpt = text[:_EXCERPT_CHARS]
    if len(text) > _EXCERPT_CHARS:
        excerpt += "\n… [truncated]"
    entry["excerpt"] = excerpt
    entry["chars"] = len(text)
    return entry
