"""CLI for Prompt Structure Auditor."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from psa.apply.engine import run_apply
from psa.advise.engine import run_advise
from psa.core.canon import dumps
from psa.core.config import DEFAULT_CONFIG, ConfigView
from psa.core.pipeline import analyze
from psa.core.ports import LocalRepoFS
from psa.discovery import discover
from psa.lifecycle.baseline import load_baseline, save_baseline
from psa.lifecycle.diff import diff_audits
from psa.report.audit_view import render_audit, repo_display_name
from psa.report.doctor import render_doctor
from psa.report.plan_view import render_plan
from psa.report.preview_view import render_preview, render_preview_step

import os


def _add_ignore_flag(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--no-default-ignores",
        action="store_true",
        help="Include paths normally excluded (tests/, fixtures/, skill test trees)",
    )


def _config_from_args(args: argparse.Namespace) -> ConfigView:
    if getattr(args, "no_default_ignores", False):
        return DEFAULT_CONFIG.with_no_default_ignores()
    return DEFAULT_CONFIG


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="psa",
        description=(
            "Prompt Structure Auditor — "
            "audit · plan · preview · apply · advise · doctor"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_audit = sub.add_parser(
        "audit",
        help="What do I have, and is it healthy? (factual assessment)",
    )
    p_audit.add_argument("path", nargs="?", default=".", help="Repository path")
    p_audit.add_argument("--format", choices=("text", "json"), default="text")
    p_audit.add_argument("--out", default=None, help="Write output to file")
    _add_ignore_flag(p_audit)

    p_plan = sub.add_parser(
        "plan",
        help="What should I fix first, and why? (Recommended Plan)",
    )
    p_plan.add_argument("path", nargs="?", default=".", help="Repository path")
    p_plan.add_argument("--format", choices=("text", "json"), default="text")
    p_plan.add_argument("--out", default=None, help="Write output to file")
    _add_ignore_flag(p_plan)

    p_preview = sub.add_parser(
        "preview",
        help="What will PSA change? (implementation preview; read-only)",
    )
    p_preview.add_argument("path", nargs="?", default=".", help="Repository path")
    p_preview.add_argument(
        "--step",
        type=int,
        default=None,
        metavar="N",
        help="Show implementation detail for recommendation step N",
    )
    _add_ignore_flag(p_preview)

    p_apply = sub.add_parser(
        "apply",
        help="Safely execute approved optimisation (internal validation)",
    )
    p_apply.add_argument("path", nargs="?", default=".", help="Repository path")
    p_apply.add_argument(
        "--step",
        type=int,
        default=None,
        metavar="N",
        help="Apply only recommendation step N, then stop",
    )
    p_apply.add_argument(
        "--dangerous",
        action="store_true",
        help="Continuous apply without confirmation (validation still runs)",
    )
    _add_ignore_flag(p_apply)

    p_advise = sub.add_parser(
        "advise",
        help="What else is worth investigating beyond current rules? (AI scout)",
    )
    p_advise.add_argument("path", nargs="?", default=".", help="Repository path")
    p_advise.add_argument(
        "--brief-only",
        action="store_true",
        help="Emit deterministic Advise brief JSON only (no AI judgment)",
    )
    p_advise.add_argument(
        "--judgment",
        default=None,
        metavar="PATH",
        help="Path to embedded-AI judgment JSON",
    )
    p_advise.add_argument("--format", choices=("text", "json"), default="text")
    p_advise.add_argument("--out", default=None, help="Write output to file")
    _add_ignore_flag(p_advise)

    p_doc = sub.add_parser(
        "doctor",
        help="Why was (or wasn't) something analysed? (diagnostics)",
    )
    p_doc.add_argument("path", nargs="?", default=".", help="Repository path")
    _add_ignore_flag(p_doc)

    p_base = sub.add_parser("baseline", help="Baseline operations")
    base_sub = p_base.add_subparsers(dest="base_cmd", required=True)
    p_save = base_sub.add_parser("save", help="Save baseline audit JSON")
    p_save.add_argument("path", nargs="?", default=".", help="Repository path")
    p_save.add_argument("--out", required=True, help="Baseline output path")
    _add_ignore_flag(p_save)

    p_diff = sub.add_parser("diff", help="Diff current audit against a baseline")
    p_diff.add_argument("path", nargs="?", default=".", help="Repository path")
    p_diff.add_argument("--baseline", required=True, help="Baseline JSON path")
    p_diff.add_argument("--format", choices=("text", "json"), default="text")
    p_diff.add_argument(
        "--fail-on-introduced",
        action="store_true",
        help="Exit 1 if any findings were introduced (CI ratchet)",
    )
    _add_ignore_flag(p_diff)

    p_patch = sub.add_parser("patch", help="Deprecated mechanical patch commands")
    patch_sub = p_patch.add_subparsers(dest="patch_cmd", required=True)

    def _add_finding_path(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "finding_id",
            help="Finding id (f_…) or rule id (e.g. ORDER001)",
        )
        p.add_argument("path", nargs="?", default=".", help="Repository path")
        _add_ignore_flag(p)

    p_prev = patch_sub.add_parser(
        "preview",
        help="Deprecated — use `psa preview`",
    )
    _add_finding_path(p_prev)

    p_val = patch_sub.add_parser(
        "validate",
        help="Deprecated — validation is internal to `psa apply`",
    )
    _add_finding_path(p_val)
    p_val.add_argument("--format", choices=("text", "json"), default="text")

    p_app = patch_sub.add_parser(
        "apply",
        help="Deprecated — use `psa apply`",
    )
    _add_finding_path(p_app)
    p_app.add_argument("--branch", default=None, help="Ignored (deprecated)")
    p_app.add_argument("--yes", action="store_true", help="Ignored (deprecated)")

    args = parser.parse_args(argv)
    cfg = _config_from_args(args)

    if args.cmd == "baseline" and args.base_cmd == "save":
        root = Path(args.path).resolve()
        if not root.exists():
            print(f"path not found: {root}", file=sys.stderr)
            return 2
        audit = analyze(LocalRepoFS(root), config=cfg)
        save_baseline(audit, args.out)
        print(f"baseline saved: {args.out}")
        return 0

    if args.cmd == "patch":
        print(
            "psa patch commands are deprecated.\n"
            "Use:  psa preview [PATH]\n"
            "      psa preview --step N [PATH]\n"
            "      psa apply --step N [PATH]\n"
            "      psa apply --dangerous [PATH]\n"
            "Validation is an internal phase of psa apply.",
            file=sys.stderr,
        )
        return 2

    if args.cmd == "apply":
        root = Path(args.path).resolve()
        if not root.exists():
            print(f"path not found: {root}", file=sys.stderr)
            return 2
        if not (root / ".git").exists():
            print(f"not a git repository: {root}", file=sys.stderr)
            return 2
        noninteractive = (
            not sys.stdin.isatty()
            or os.environ.get("PSA_NONINTERACTIVE", "").lower() in {"1", "true", "yes"}
        )
        if args.step is None and not args.dangerous and noninteractive:
            print(
                "Non-interactive apply requires --step N or --dangerous.",
                file=sys.stderr,
            )
            return 2

        def _confirm(prompt: str) -> bool:
            try:
                answer = input(f"{prompt} [y/N] ").strip().lower()
            except EOFError:
                return False
            return answer in {"y", "yes"}

        confirm = None if args.dangerous or args.step is not None else _confirm
        try:
            session = run_apply(
                root,
                step=args.step,
                dangerous=args.dangerous,
                config=cfg,
                confirm=confirm,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(session.report, end="")
        return session.exit_code

    if args.cmd == "advise":
        root = Path(args.path).resolve()
        if not root.exists():
            print(f"path not found: {root}", file=sys.stderr)
            return 2
        judgment_path = Path(args.judgment).resolve() if args.judgment else None
        if judgment_path is not None and not judgment_path.is_file():
            print(f"judgment file not found: {judgment_path}", file=sys.stderr)
            return 2
        result = run_advise(
            root,
            config=cfg,
            judgment_path=judgment_path,
            brief_only=args.brief_only,
            consider_stdin=not args.brief_only and judgment_path is None,
        )
        if args.brief_only:
            out = dumps(result.brief)
            if args.out:
                Path(args.out).write_text(out, encoding="utf-8")
            else:
                print(out, end="")
            return 0
        if result.exit_code != 0:
            print(result.error or "Advise failed.", file=sys.stderr)
            return result.exit_code
        if args.format == "json":
            out = dumps(result.judgment.to_dict())
        else:
            out = result.report
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out, end="")
        return 0

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"path not found: {root}", file=sys.stderr)
        return 2

    fs = LocalRepoFS(root)

    if args.cmd == "doctor":
        print(render_doctor(discover(fs, cfg), cfg), end="")
        return 0

    audit = analyze(fs, config=cfg)

    if args.cmd == "audit":
        if args.format == "json":
            out = dumps(audit.to_dict())
        else:
            out = render_audit(audit, repo_name=repo_display_name(root))
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out, end="")
        return 0

    if args.cmd == "plan":
        if args.format == "json":
            graph = audit.dependency_graph
            out = dumps(
                {
                    "repository": repo_display_name(root),
                    "findings_considered": len(audit.findings),
                    "plan": [p.to_dict() for p in (graph.plan if graph else ())],
                }
            )
        else:
            out = render_plan(audit, repo_name=repo_display_name(root))
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out, end="")
        return 0

    if args.cmd == "preview":
        name = repo_display_name(root)
        if args.step is not None:
            try:
                out = render_preview_step(audit, args.step, repo_name=name)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
        else:
            out = render_preview(audit, repo_name=name)
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
        if args.fail_on_introduced and d.introduced:
            return 1
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
