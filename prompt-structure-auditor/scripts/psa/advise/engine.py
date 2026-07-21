"""Advise engine — brief → embedded AI judgment → report + persist."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from psa.advise.brief import build_advise_brief
from psa.advise.bridge import (
    BridgeUnavailableError,
    bridge_available,
    obtain_judgment,
)
from psa.advise.persist import load_advise, save_advise
from psa.advise.schema import AdviseJudgment
from psa.core.config import ConfigView, DEFAULT_CONFIG
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.optimise.state import load_state
from psa.report.advise_view import format_apply_advise_line, render_advise
from psa.report.audit_view import STATUS_HEALTHY, STATUS_NEEDS_ATTENTION, repo_display_name


@dataclass
class AdviseResult:
    brief: dict
    judgment: AdviseJudgment
    report: str
    exit_code: int = 0
    advise_path: Path | None = None
    apply_one_liner: str = ""
    error: str = ""


def run_advise(
    repo_root: Path,
    *,
    config: ConfigView | None = None,
    judgment_path: Path | None = None,
    brief_only: bool = False,
    consider_stdin: bool = True,
    tool_version: str | None = None,
    persist: bool = True,
) -> AdviseResult:
    """Run Advise. Requires an embedded AI judgment unless brief_only."""
    cfg = config or DEFAULT_CONFIG
    root = repo_root.resolve()
    fs = LocalRepoFS(root)
    name = repo_display_name(root)
    audit = analyze(fs, config=cfg, tool_version=tool_version)
    state = load_state(root)
    brief = build_advise_brief(
        audit,
        repo_name=name,
        repo=fs,
        repo_root=root,
        state=state,
    )

    if brief_only:
        return AdviseResult(
            brief=brief,
            judgment=AdviseJudgment(),
            report="",
            exit_code=0,
        )

    try:
        judgment = obtain_judgment(
            brief,
            judgment_path=judgment_path,
            consider_stdin=consider_stdin,
        )
    except BridgeUnavailableError as exc:
        return AdviseResult(
            brief=brief,
            judgment=AdviseJudgment(),
            report="",
            exit_code=2,
            error=str(exc),
        )
    except (OSError, ValueError, RuntimeError) as exc:
        return AdviseResult(
            brief=brief,
            judgment=AdviseJudgment(),
            report="",
            exit_code=2,
            error=f"Advise judgment failed: {exc}",
        )

    report = render_advise(judgment, repo_name=name)
    path: Path | None = None
    if persist:
        path = save_advise(root, judgment, repo_name=name)
        from psa.optimise.state import OptimisationState
        from psa.optimise.status import write_status_md

        status_state = state if state is not None else OptimisationState()
        health = STATUS_HEALTHY if not audit.findings else STATUS_NEEDS_ATTENTION
        write_status_md(
            root,
            status_state,
            repo_name=name,
            health=health,
            findings_count=len(audit.findings),
        )

    one_liner = format_apply_advise_line(judgment.summary_theme)
    return AdviseResult(
        brief=brief,
        judgment=judgment,
        report=report,
        exit_code=0,
        advise_path=path,
        apply_one_liner=one_liner,
    )


def try_post_apply_one_liner(
    repo_root: Path,
    *,
    config: ConfigView | None = None,
    tool_version: str | None = None,
) -> str:
    """Best-effort Advise one-liner after Apply. Never raises for missing bridge."""
    if not bridge_available(consider_stdin=False):
        # Reuse last persisted theme if present and bridge was used earlier.
        snap = load_advise(repo_root)
        # Without a live bridge, omit one-liner per product decision (1A).
        _ = snap
        return ""
    try:
        result = run_advise(
            repo_root,
            config=config,
            consider_stdin=False,
            tool_version=tool_version,
            persist=True,
        )
    except Exception:  # noqa: BLE001
        return ""
    if result.exit_code != 0:
        return ""
    return result.apply_one_liner
