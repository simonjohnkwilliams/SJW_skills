"""CLI for Prompt Structure Auditor."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from psa.core.canon import dumps
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.lifecycle.baseline import load_baseline, save_baseline
from psa.lifecycle.diff import diff_audits
from psa.patch.generate import preview_patch
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

    p_base = sub.add_parser("baseline", help="Baseline operations")
    base_sub = p_base.add_subparsers(dest="base_cmd", required=True)
    p_save = base_sub.add_parser("save", help="Save baseline audit JSON")
    p_save.add_argument("path", nargs="?", default=".", help="Repository path")
    p_save.add_argument("--out", required=True, help="Baseline output path")

    p_diff = sub.add_parser("diff", help="Diff current audit against a baseline")
    p_diff.add_argument("path", nargs="?", default=".", help="Repository path")
    p_diff.add_argument("--baseline", required=True, help="Baseline JSON path")
    p_diff.add_argument("--format", choices=("text", "json"), default="text")

    p_patch = sub.add_parser("patch", help="Patch operations (preview only in this release)")
    patch_sub = p_patch.add_subparsers(dest="patch_cmd", required=True)
    p_prev = patch_sub.add_parser("preview", help="Preview mechanical patch for a finding")
    p_prev.add_argument("finding_id", help="Finding id from audit JSON")
    p_prev.add_argument("path", nargs="?", default=".", help="Repository path")

    args = parser.parse_args(argv)

    if args.cmd == "baseline" and args.base_cmd == "save":
        root = Path(args.path).resolve()
        if not root.exists():
            print(f"path not found: {root}", file=sys.stderr)
            return 2
        audit = analyze(LocalRepoFS(root))
        save_baseline(audit, args.out)
        print(f"baseline saved: {args.out}")
        return 0

    if args.cmd == "patch" and args.patch_cmd == "preview":
        root = Path(args.path).resolve()
        if not root.exists():
            print(f"path not found: {root}", file=sys.stderr)
            return 2
        fs = LocalRepoFS(root)
        audit = analyze(fs)
        try:
            patch = preview_patch(fs, audit, args.finding_id)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(patch.diff, end="")
        return 0

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

    if args.cmd == "diff":
        baseline = load_baseline(args.baseline)
        d = diff_audits(current=audit, baseline=baseline)
        if args.format == "json":
            print(dumps(d.to_dict()), end="")
        else:
            print("Audit Diff")
            print(f"  Resolved:   {len(d.resolved)}")
            for i in d.resolved:
                print(f"    - {i}")
            print(f"  Introduced: {len(d.introduced)}")
            for i in d.introduced:
                print(f"    - {i}")
            print(f"  Unchanged:  {len(d.unchanged)}")
            if d.reprioritised:
                print(f"  Reprioritised: {len(d.reprioritised)}")
                for fid, old, new in d.reprioritised:
                    print(f"    - {fid}: {old} -> {new}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
