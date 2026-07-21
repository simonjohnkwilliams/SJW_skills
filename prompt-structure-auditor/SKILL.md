---
name: prompt-structure-auditor
description: >-
  Audits the repository prompt-construction surface (CLAUDE.md, AGENTS.md,
  Cursor rules, and related sources) for structural issues. Produces findings,
  Recommended Plan (`psa plan`), semantic preview (`psa preview`), and
  optimisation apply (`psa apply`) with internal validation, persistent state
  (.psa/state.json, PSA_STATUS.md), and commits on psa/optimise. Use when the
  user runs /prompt-structure-auditor, audits prompt structure, plans remediations,
  previews implementation, applies optimisations, or saves/diffs baselines.
disable-model-invocation: true
---

# Prompt Structure Auditor

Deterministic static analysis and optimisation of the prompt surface. Follow the RFC honesty rules:
report only observables; label inference; never invent cache hit rates or cost savings.

**Do not rewrite files** unless the user explicitly asks for **`psa apply`**.
Preview is read-only. Apply performs internal validation, then commits on `psa/optimise`.

## Setup

```powershell
$env:PYTHONPATH = (Resolve-Path .).Path   # skill scripts/ directory
python -m psa --help
```

See [QUICKSTART.md](QUICKSTART.md) and [MANUAL_TEST.md](MANUAL_TEST.md).

## Command map (one question each)

| Command | Question |
|---------|----------|
| `psa audit` | What do I have, and is it healthy? |
| `psa plan` | What should I fix first, and why? |
| `psa preview` | What will PSA change? |
| `psa preview --step N` | How will recommendation N be implemented? |
| `psa apply --step N` | Safely apply one recommendation |
| `psa apply` | Continue optimisation (confirm between) |
| `psa apply --dangerous` | Continue without confirmation (validation still on) |
| `psa doctor` | Why was (or wasn't) something analysed? |

## Modes

### Default (`/prompt-structure-auditor`)

1. Run **`python -m psa audit <PATH>`**. Present Summary + Findings only.
2. If asked what to fix: **`psa plan`**.
3. If asked what will change: **`psa preview`** / **`--step N`**.
4. If asked to execute: **`psa apply --step N`** (preferred) or **`--dangerous`**.
5. Discovery questions: **`psa doctor`**.

### Apply notes

- Requires a git repository.
- Commits land on `psa/optimise` (one commit per successful recommendation).
- Updates `.psa/state.json` and `PSA_STATUS.md`.
- Only recommendations with a registered executor are applied (ORDER001 today); others are skipped cleanly.
- Non-interactive shells require `--step` or `--dangerous`.

## Hard rules

- Never fabricate scores, hit rates, costs, or latency claims.
- Every finding must cite evidence the user can open.
- Analysis and preview are read-only.
- Apply only after explicit user request.
- Prefer `audit` for day-to-day; use `doctor` only for discovery troubleshooting.
