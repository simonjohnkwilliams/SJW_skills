"""Hybrid embedded-AI bridge for Advise judgment.

Spike winner (see BRIDGE.md): --judgment, PSA_ADVISE_CMD, PSA_ADVISE_JUDGMENT, stdin.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from psa.advise.schema import AdviseJudgment
from psa.core.canon import dumps

ENV_CMD = "PSA_ADVISE_CMD"
ENV_JUDGMENT = "PSA_ADVISE_JUDGMENT"

BRIDGE_MISSING_MSG = "Advise requires an embedded AI caller."


class BridgeUnavailableError(RuntimeError):
    """No judgment source configured."""


def bridge_available(
    *,
    judgment_path: Path | None = None,
    consider_stdin: bool = True,
) -> bool:
    if judgment_path is not None:
        return True
    if os.environ.get(ENV_CMD, "").strip():
        return True
    if os.environ.get(ENV_JUDGMENT, "").strip():
        return True
    if consider_stdin and not sys.stdin.isatty():
        # May still be empty; obtain_judgment will validate.
        return True
    return False


def obtain_judgment(
    brief: dict[str, Any],
    *,
    judgment_path: Path | None = None,
    consider_stdin: bool = True,
) -> AdviseJudgment:
    """Resolve judgment from hybrid bridge sources (priority order)."""
    if judgment_path is not None:
        return _from_file(judgment_path)

    cmd = os.environ.get(ENV_CMD, "").strip()
    if cmd:
        return _from_command(cmd, brief)

    env_val = os.environ.get(ENV_JUDGMENT, "").strip()
    if env_val:
        return _from_env_value(env_val)

    if consider_stdin and not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            return _parse_judgment_json(raw)

    raise BridgeUnavailableError(BRIDGE_MISSING_MSG)


def _from_file(path: Path) -> AdviseJudgment:
    text = path.read_text(encoding="utf-8")
    return _parse_judgment_json(text)


def _from_env_value(value: str) -> AdviseJudgment:
    path = Path(value)
    if path.is_file():
        return _from_file(path)
    return _parse_judgment_json(value)


def _from_command(cmd: str, brief: dict[str, Any]) -> AdviseJudgment:
    proc = subprocess.run(
        cmd,
        input=dumps(brief),
        capture_output=True,
        text=True,
        shell=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        raise RuntimeError(f"PSA_ADVISE_CMD failed: {err}")
    return _parse_judgment_json(proc.stdout)


def _parse_judgment_json(raw: str) -> AdviseJudgment:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Advise judgment must be a JSON object")
    return AdviseJudgment.from_dict(data)
