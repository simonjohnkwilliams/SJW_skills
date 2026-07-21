"""Apply engine tests — ORDER001 executor + skip unsupported."""
from __future__ import annotations

import subprocess
from pathlib import Path

from psa.apply.engine import run_apply
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.executors import has_executor
from psa.optimise.state import OPTIMISE_BRANCH, load_state
from tests.conftest import FIXTURES


def _git_init(demo: Path) -> None:
    subprocess.run(["git", "init"], cwd=demo, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=demo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
        cwd=demo,
        check=True,
        capture_output=True,
    )


def test_executor_registry_order001_only():
    assert has_executor("opt:ORDER001")
    assert not has_executor("opt:DUP001")


def test_apply_step_order001(tmp_path: Path):
    src = FIXTURES / "order_apply"
    demo = tmp_path / "order-apply"
    import shutil

    shutil.copytree(src, demo)
    _git_init(demo)

    audit = analyze(LocalRepoFS(demo), tool_version="0.1.0")
    plan = audit.dependency_graph.plan
    assert len(plan) == 1
    assert plan[0].optimisation_id == "opt:ORDER001"

    session = run_apply(demo, step=1, dangerous=False, tool_version="0.1.0")
    assert session.exit_code == 0, session.report
    assert any(i.outcome == "applied" for i in session.iterations)
    assert "Status: Success" in session.report
    assert "Repository Changed: Yes" in session.report
    assert "Repository re-analysed successfully." in session.report
    assert "Optimisations Applied This Run: 1" in session.report
    assert "Repository Status" in session.report
    assert "Next Recommendation" in session.report
    assert "Health:" not in session.report
    assert "Completed Optimisations:" not in session.report
    assert "Optimisation Progress" not in session.report
    assert (demo / ".psa" / "state.json").is_file()
    assert (demo / "PSA_STATUS.md").is_file()
    state = load_state(demo)
    assert state is not None
    assert "opt:ORDER001" in state.completed_ids()

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=demo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert branch == OPTIMISE_BRANCH

    after = analyze(LocalRepoFS(demo), tool_version="0.1.0")
    assert not any(f.rule_id == "ORDER001" for f in after.findings)


def test_apply_skips_unsupported(tmp_path: Path):
    src = FIXTURES / "vr2_latetrain"
    demo = tmp_path / "skip-demo"
    import shutil

    shutil.copytree(src, demo)
    _git_init(demo)
    audit = analyze(LocalRepoFS(demo), tool_version="0.1.0")
    # First step is typically DUP001 — no executor
    session = run_apply(demo, step=1, tool_version="0.1.0")
    assert session.exit_code == 0
    assert any(i.outcome == "skipped" for i in session.iterations)
    assert "Skipped" in session.report or "No deterministic executor" in session.report
