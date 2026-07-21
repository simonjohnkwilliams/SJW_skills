"""Git operations for the optimisation apply engine.

Uses a single branch `psa/optimise` with one commit per successful recommendation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from psa.optimise.state import OPTIMISE_BRANCH


def ensure_git_repo(root: Path) -> None:
    if not (root / ".git").exists():
        raise ValueError(f"not a git repository: {root}")


def ensure_optimise_branch(root: Path) -> str:
    """Create or checkout psa/optimise. Returns branch name."""
    ensure_git_repo(root)
    listed = _run(root, ["git", "branch", "--list", OPTIMISE_BRANCH]).stdout
    names = {b.strip().lstrip("* ").strip() for b in listed.splitlines() if b.strip()}
    current = _run(root, ["git", "branch", "--show-current"]).stdout.strip()
    if OPTIMISE_BRANCH in names:
        if current != OPTIMISE_BRANCH:
            _run(root, ["git", "checkout", OPTIMISE_BRANCH])
    else:
        _run(root, ["git", "checkout", "-b", OPTIMISE_BRANCH])
    return OPTIMISE_BRANCH


def write_patch_files(root: Path, patches: tuple) -> list[str]:
    """Write patch new_text to disk. Returns relative paths written."""
    written: list[str] = []
    for patch in patches:
        rel = patch.path.replace("\\", "/")
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patch.new_text, encoding="utf-8")
        written.append(rel)
    return written


def commit_paths(root: Path, paths: list[str], *, message: str) -> str:
    """Stage paths and create one commit. Returns commit SHA."""
    ensure_optimise_branch(root)
    for rel in paths:
        _run(root, ["git", "add", "--", rel])
    # If nothing to commit (identical), still allow empty? Prefer fail clearly.
    status = _run(root, ["git", "status", "--porcelain"]).stdout.strip()
    if not status:
        raise ValueError("nothing to commit after applying transforms")
    _run(
        root,
        [
            "git",
            "-c",
            "user.email=psa@local",
            "-c",
            "user.name=psa",
            "commit",
            "-m",
            message,
        ],
    )
    return _run(root, ["git", "rev-parse", "HEAD"]).stdout.strip()


def _run(cwd: Path, cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
