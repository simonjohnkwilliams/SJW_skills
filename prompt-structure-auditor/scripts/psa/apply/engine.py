"""Optimisation apply engine — internal validation + pluggable executors."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from psa.apply.gitops import (
    commit_paths,
    ensure_git_repo,
    ensure_optimise_branch,
    write_patch_files,
)
from psa.apply.report import render_apply_report
from psa.core.config import ConfigView, DEFAULT_CONFIG
from psa.core.pipeline import Audit, analyze
from psa.core.ports import LocalRepoFS
from psa.executors import executor_for_recommendation, has_executor
from psa.optimise.state import (
    OPTIMISE_BRANCH,
    CompletedOptimisation,
    OptimisationState,
    OutstandingOptimisation,
    compute_fingerprint,
    load_state,
    save_state,
    utc_now,
)
from psa.optimise.status import write_status_md
from psa.patch.validate import validate_patch
from psa.recommend.graph import PlanRecommendation
from psa.report.audit_view import STATUS_HEALTHY, STATUS_NEEDS_ATTENTION, repo_display_name


ConfirmFn = Callable[[str], bool]


@dataclass(frozen=True)
class IterationResult:
    outcome: str  # applied | skipped | blocked | idle
    step: int | None
    optimisation_id: str
    title: str
    detail: str
    commit: str = ""


@dataclass
class ApplySessionResult:
    iterations: list[IterationResult] = field(default_factory=list)
    final_audit: Audit | None = None
    state: OptimisationState | None = None
    report: str = ""
    exit_code: int = 0
    mode: str = "Interactive"  # Interactive | Continuous | Dangerous
    duration_seconds: float | None = None
    health_improved: bool = False
    advise_one_liner: str = ""


def run_apply(
    repo_root: Path,
    *,
    step: int | None = None,
    dangerous: bool = False,
    config: ConfigView | None = None,
    confirm: ConfirmFn | None = None,
    tool_version: str | None = None,
) -> ApplySessionResult:
    """Run the optimisation apply loop."""
    cfg = config or DEFAULT_CONFIG
    root = repo_root.resolve()
    ensure_git_repo(root)
    fs = LocalRepoFS(root)
    started = time.perf_counter()
    if step is not None:
        mode = "Interactive"
    elif dangerous:
        mode = "Dangerous"
    else:
        mode = "Continuous"

    result = ApplySessionResult(mode=mode)

    state = load_state(root) or OptimisationState()
    now = utc_now()
    fingerprint = compute_fingerprint(fs)
    state.fingerprint = fingerprint
    state.status = "in_progress"
    state.last_block_reason = ""

    audit = analyze(fs, config=cfg, tool_version=tool_version)
    findings_before = len(audit.findings)
    state.last_audit_at = now
    state.last_plan_at = now
    _sync_outstanding(state, audit)

    plan = getattr(audit.dependency_graph, "plan", ()) or ()
    if not plan:
        state.status = "complete"
        state.outstanding = []
        _persist(root, state, audit)
        result.state = state
        result.final_audit = audit
        result.iterations.append(
            IterationResult(
                outcome="idle",
                step=None,
                optimisation_id="",
                title="",
                detail="No recommendations remaining.",
            )
        )
        result.duration_seconds = time.perf_counter() - started
        _finalize_report(result, root, cfg, tool_version)
        return result

    if step is not None:
        if step < 1 or step > len(plan):
            result.exit_code = 2
            result.iterations.append(
                IterationResult(
                    outcome="blocked",
                    step=step,
                    optimisation_id="",
                    title="",
                    detail=f"Invalid step {step}: plan has {len(plan)} recommendation(s).",
                )
            )
            result.final_audit = audit
            result.state = state
            result.duration_seconds = time.perf_counter() - started
            result.report = render_apply_report(result, repo_name=repo_display_name(root))
            return result
        queue = [(step, plan[step - 1])]
    else:
        queue = [(i, rec) for i, rec in enumerate(plan, 1)]

    idx = 0
    while idx < len(queue):
        step_n, rec = queue[idx]

        if step is None and not dangerous and confirm is not None:
            if not confirm(f"Apply Step {step_n} ({rec.title})?"):
                state.status = "idle"
                _persist(root, state, audit)
                break

        itr = _apply_one(root, fs, audit, state, step_n, rec, cfg, tool_version)
        result.iterations.append(itr)

        if itr.outcome == "blocked":
            state.status = "blocked"
            state.last_block_reason = itr.detail
            _persist(root, state, audit)
            result.exit_code = 1
            break

        if itr.outcome == "applied":
            fs = LocalRepoFS(root)
            audit = analyze(fs, config=cfg, tool_version=tool_version)
            state.last_audit_at = utc_now()
            state.last_plan_at = state.last_audit_at
            state.last_apply_at = state.last_audit_at
            state.fingerprint = compute_fingerprint(fs)
            _sync_outstanding(state, audit)
            _persist(root, state, audit)

            if step is not None:
                break

            plan = getattr(audit.dependency_graph, "plan", ()) or ()
            if not plan:
                state.status = "complete"
                _persist(root, state, audit)
                break

            queue = [(i, r) for i, r in enumerate(plan, 1)]
            idx = 0
            continue

        if step is not None:
            break
        idx += 1
        if idx >= len(queue):
            plan = getattr(audit.dependency_graph, "plan", ()) or ()
            if not plan:
                state.status = "complete"
            else:
                state.status = "idle"
                state.last_block_reason = (
                    "Remaining recommendations have no deterministic executor."
                )
            _persist(root, state, audit)
            break

    if state.status == "in_progress":
        state.status = "idle"
        _persist(root, state, audit)

    result.final_audit = audit
    result.state = state
    result.health_improved = findings_before > 0 and not audit.findings
    result.duration_seconds = time.perf_counter() - started
    _finalize_report(result, root, cfg, tool_version)
    return result


def _finalize_report(
    result: ApplySessionResult,
    root: Path,
    cfg: ConfigView,
    tool_version: str | None,
) -> None:
    if result.exit_code == 0:
        try:
            from psa.advise.engine import try_post_apply_one_liner

            result.advise_one_liner = try_post_apply_one_liner(
                root, config=cfg, tool_version=tool_version
            )
        except Exception:  # noqa: BLE001
            result.advise_one_liner = ""
    result.report = render_apply_report(result, repo_name=repo_display_name(root))


def _apply_one(
    root: Path,
    fs: LocalRepoFS,
    audit: Audit,
    state: OptimisationState,
    step_n: int,
    rec: PlanRecommendation,
    cfg: ConfigView,
    tool_version: str | None,
) -> IterationResult:
    oid = rec.optimisation_id
    title = rec.title

    plan = getattr(audit.dependency_graph, "plan", ()) or ()
    id_to_step = {p.id: i for i, p in enumerate(plan, 1)}
    for dep in rec.depends_on:
        dep_step = id_to_step.get(dep)
        if dep_step is not None and dep_step < step_n:
            return IterationResult(
                outcome="blocked",
                step=step_n,
                optimisation_id=oid,
                title=title,
                detail=(
                    f"Dependency {dep} (Step {dep_step}) is still outstanding; "
                    f"apply it before Step {step_n}."
                ),
            )

    if not has_executor(oid):
        return IterationResult(
            outcome="skipped",
            step=step_n,
            optimisation_id=oid,
            title=title,
            detail=f"No deterministic executor for {oid}.",
        )

    executor = executor_for_recommendation(rec)
    if executor is None or not executor.can_apply(rec, audit):
        return IterationResult(
            outcome="skipped",
            step=step_n,
            optimisation_id=oid,
            title=title,
            detail=f"Executor for {oid} cannot apply this recommendation.",
        )

    for fid in rec.addresses:
        finding = next((f for f in audit.findings if f.id == fid), None)
        if finding is None:
            return IterationResult(
                outcome="blocked",
                step=step_n,
                optimisation_id=oid,
                title=title,
                detail=f"Finding {fid} no longer present in audit.",
            )
        for ev in finding.evidence:
            if ev.path and not (root / ev.path.replace("\\", "/")).is_file():
                return IterationResult(
                    outcome="blocked",
                    step=step_n,
                    optimisation_id=oid,
                    title=title,
                    detail=f"Required file missing: {ev.path}",
                )

    try:
        patches = executor.build(fs, audit, rec)
    except ValueError as exc:
        return IterationResult(
            outcome="blocked",
            step=step_n,
            optimisation_id=oid,
            title=title,
            detail=f"Executor preflight failed: {exc}",
        )

    for patch in patches:
        validation = validate_patch(fs, audit, patch, tool_version=tool_version or "0.1.0")
        if not validation.ok:
            reason = "; ".join(validation.failures) or "validation failed"
            return IterationResult(
                outcome="blocked",
                step=step_n,
                optimisation_id=oid,
                title=title,
                detail=f"Internal validation failed: {reason}",
            )

    try:
        ensure_optimise_branch(root)
        written = write_patch_files(root, patches)
        if oid not in state.completed_ids():
            state.completed.append(
                CompletedOptimisation(
                    optimisation_id=oid,
                    title=title,
                    completed_at=utc_now(),
                )
            )
        state.last_apply_at = utc_now()
        _sync_outstanding(state, audit)
        _persist(root, state, audit)
        paths = written + [".psa/state.json", "PSA_STATUS.md"]
        msg = f"psa: apply {oid} — {title}"
        commit = commit_paths(root, paths, message=msg)
    except Exception as exc:  # noqa: BLE001
        return IterationResult(
            outcome="blocked",
            step=step_n,
            optimisation_id=oid,
            title=title,
            detail=f"Git apply failed: {exc}",
        )

    return IterationResult(
        outcome="applied",
        step=step_n,
        optimisation_id=oid,
        title=title,
        detail=f"Applied on branch {OPTIMISE_BRANCH}.",
        commit=commit,
    )


def _sync_outstanding(state: OptimisationState, audit: Audit) -> None:
    plan = getattr(audit.dependency_graph, "plan", ()) or ()
    state.outstanding = [
        OutstandingOptimisation(
            optimisation_id=p.optimisation_id,
            title=p.title,
        )
        for p in plan
    ]


def _persist(root: Path, state: OptimisationState, audit: Audit) -> None:
    save_state(root, state)
    health = STATUS_HEALTHY if not audit.findings else STATUS_NEEDS_ATTENTION
    write_status_md(
        root,
        state,
        repo_name=repo_display_name(root),
        health=health,
        findings_count=len(audit.findings),
    )
