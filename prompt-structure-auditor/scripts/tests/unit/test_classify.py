"""Behaviour: VOL002 / classifier — references are not embeds."""
from __future__ import annotations

from psa.model.classify import classify_section


def test_reference_to_bmad_output_is_stable_not_volatile():
    text = (
        "Before changing code always:\n"
        "1. Read _bmad-output/planning-artifacts/briefs\n"
        "2. Read the implementation artefact for the current story\n"
    )
    result = classify_section("Instructions", text)
    assert result.stability == "stable"


def test_current_focus_heading_is_volatile():
    text = "Primary flow is now CSV upload for bank transactions.\n"
    result = classify_section("Current Focus: CSV Import", text)
    assert result.stability == "volatile"
    assert result.volatility_signals
