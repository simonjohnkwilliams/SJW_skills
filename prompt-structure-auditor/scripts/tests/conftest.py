"""Shared paths for fixture repos and optional live validation repos."""
from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VR1 = FIXTURES / "vr1_empty"
VR2 = FIXTURES / "vr2_latetrain"
VR3 = FIXTURES / "vr3_demo"

LIVE_VR1 = Path(r"C:\Users\simon\IdeaProjects\ai-context-benchmark")
LIVE_VR2 = Path(r"C:\Users\simon\IdeaProjects\lateTrainQueries")
LIVE_VR3 = Path(r"C:\Users\simon\OneDrive\demo\demo")
