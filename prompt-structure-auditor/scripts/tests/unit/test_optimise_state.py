"""Unit tests for optimisation state persistence."""
from __future__ import annotations

from pathlib import Path

from psa.optimise.state import (
    CompletedOptimisation,
    OptimisationState,
    load_state,
    save_state,
)
from psa.optimise.status import render_status_md


def test_state_roundtrip(tmp_path: Path):
    state = OptimisationState(
        fingerprint="abc",
        completed=[
            CompletedOptimisation(
                optimisation_id="opt:ORDER001",
                title="Move volatile sections",
                completed_at="2026-01-01T00:00:00Z",
            )
        ],
        status="complete",
    )
    save_state(tmp_path, state)
    loaded = load_state(tmp_path)
    assert loaded is not None
    assert loaded.fingerprint == "abc"
    assert loaded.completed[0].optimisation_id == "opt:ORDER001"
    assert loaded.status == "complete"


def test_status_md_contains_sections():
    state = OptimisationState(status="idle")
    text = render_status_md(
        state, repo_name="demo", health="Healthy", findings_count=0
    )
    assert "# PSA Status" in text
    assert "Completed Optimisations" in text
    assert "Outstanding Recommendations" in text
