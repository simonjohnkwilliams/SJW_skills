"""Human-readable PSA_STATUS.md optimisation dashboard."""
from __future__ import annotations

from pathlib import Path

from psa.optimise.state import OptimisationState

STATUS_FILE = "PSA_STATUS.md"


def status_path(repo_root: Path) -> Path:
    return repo_root / STATUS_FILE


def render_status_md(
    state: OptimisationState,
    *,
    repo_name: str,
    health: str,
    findings_count: int,
    repo_root: Path | None = None,
) -> str:
    lines = [
        "# PSA Status",
        "",
        "## Repository Status",
        "",
        f"- Repository: {repo_name}",
        f"- Current health: {health}",
        f"- Findings: {findings_count}",
        f"- Optimisation status: {state.status}",
        "",
        "## Completed Optimisations",
        "",
    ]
    if state.completed:
        for c in state.completed:
            lines.append(f"- `{c.optimisation_id}` — {c.title} ({c.completed_at})")
    else:
        lines.append("- None")

    lines.extend(["", "## Outstanding Recommendations", ""])
    if state.outstanding:
        for o in state.outstanding:
            lines.append(f"- `{o.optimisation_id}` — {o.title}")
    else:
        lines.append("- None")

    lines.extend(["", "## Advise Backlog", ""])
    snap = None
    if repo_root is not None:
        from psa.advise.persist import load_advise

        snap = load_advise(repo_root)
    if snap and snap.items:
        if snap.summary_theme:
            lines.append(f"- Theme: {snap.summary_theme}")
        lines.append(f"- Last run: {snap.created_at or '-'}")
        for item in snap.items:
            seed = f" → seed `{item.rule_seed_id}`" if item.rule_seed_id else ""
            lines.append(f"- `{item.id}` [{item.kind}] {item.title}{seed}")
    else:
        lines.append("- None (run `psa advise` with an embedded AI caller)")

    lines.extend(["", "## Optimisation History", ""])
    if state.completed:
        for c in state.completed:
            lines.append(f"- {c.completed_at}: completed `{c.optimisation_id}`")
    else:
        lines.append("- No optimisations applied yet.")

    if state.last_block_reason:
        lines.extend(
            [
                "",
                "## Last Block",
                "",
                state.last_block_reason,
            ]
        )

    lines.extend(
        [
            "",
            "## Timestamps",
            "",
            f"- Last analysed: {state.last_audit_at or '-'}",
            f"- Last planned: {state.last_plan_at or '-'}",
            f"- Last optimised: {state.last_apply_at or '-'}",
            "",
            "## Repository Summary",
            "",
            "PSA tracks optimisation progress in `.psa/state.json`. "
            "Advise backlog lives in `.psa/advise.json` (promotable; never auto-applied). "
            "Git records commits on `psa/optimise`. "
            "Audit always analyses the repository from scratch.",
            "",
        ]
    )
    return "\n".join(lines)


def write_status_md(
    repo_root: Path,
    state: OptimisationState,
    *,
    repo_name: str,
    health: str,
    findings_count: int,
) -> Path:
    path = status_path(repo_root)
    path.write_text(
        render_status_md(
            state,
            repo_name=repo_name,
            health=health,
            findings_count=findings_count,
            repo_root=repo_root,
        ),
        encoding="utf-8",
    )
    return path
