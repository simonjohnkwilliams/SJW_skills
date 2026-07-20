"""Shared paths for fixture repos."""
from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VR1 = FIXTURES / "vr1_empty"
VR2 = FIXTURES / "vr2_latetrain"
VR3 = FIXTURES / "vr3_demo"
