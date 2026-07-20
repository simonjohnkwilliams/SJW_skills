"""CLI for Prompt Structure Auditor."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from psa.core.canon import dumps
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.report.inventory import render_human, render_inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="psa", description="Prompt Structure Auditor")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inv = sub.add_parser("inventory", help="Show prompt surface inventory")
    p_inv.add_argument("path", nargs="?", default=".", help="Repository path")

    p_audit = sub.add_parser("audit", help="Run full audit")
    p_audit.add_argument("path", nargs="?", default=".", help="Repository path")
    p_audit.add_argument("--format", choices=("text", "json"), default="text")
    p_audit.add_argument("--out", default=None, help="Write output to file")

    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"path not found: {root}", file=sys.stderr)
        return 2

    fs = LocalRepoFS(root)
    audit = analyze(fs)

    if args.cmd == "inventory":
        text = render_inventory(audit.inventory)
        print(text, end="")
        return 0

    if args.cmd == "audit":
        if args.format == "json":
            out = dumps(audit.to_dict())
        else:
            out = render_human(audit)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out, end="")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
