---
name: prompt-structure-auditor
description: >-
  Audits the repository prompt-construction surface (CLAUDE.md, AGENTS.md,
  Cursor rules, and related sources) for structural issues. Produces findings,
  Recommended Plan (`psa plan`), semantic preview (`psa preview`), optimisation
  apply (`psa apply`), and AI-assisted Advise (`psa advise`) for gaps beyond the
  deterministic rule set. Use when the user runs /prompt-structure-auditor,
  audits prompt structure, plans remediations, previews implementation, applies
  optimisations, seeks advisory gaps, or saves/diffs baselines.
disable-model-invocation: true
---

# Prompt Structure Auditor

Deterministic static analysis and optimisation of the prompt surface, plus an
optional **Advise** scout that piggybacks on the calling embedded AI.

Follow the RFC honesty rules: report only observables; label inference; never
invent cache hit rates or cost savings.

**Do not rewrite files** unless the user explicitly asks for **`psa apply`**.
Preview and Advise are read-only for the repo (Advise may write `.psa/advise.json`).
Apply performs internal validation, then commits on `psa/optimise`.

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
| `psa advise` | What else is worth investigating beyond current rules? |
| `psa doctor` | Why was (or wasn't) something analysed? |

## Modes

### Default (`/prompt-structure-auditor`)

1. Run **`python -m psa audit <PATH>`**. Present Summary + Findings only.
2. If asked what to fix: **`psa plan`**.
3. If asked what will change: **`psa preview`** / **`--step N`**.
4. If asked to execute: **`psa apply --step N`** (preferred) or **`--dangerous`**.
5. After a successful Apply (skill path): run **Advise** (below) and show the one-line theme if present; offer the full Advise report.
6. If asked what else / gaps beyond rules: **Advise**.
7. Discovery questions: **`psa doctor`**.

### Advise (Release 5) — embedded AI scout

PSA does **not** call an LLM API. You (the calling agent) are the judgment layer.

1. Build the brief: `python -m psa advise <PATH> --brief-only`
2. Read the brief. Propose gaps **not** already covered by `rule_catalog` / outstanding plan.
   If you contradict a deterministic rule/finding, emit `kind: "conflict"`.
3. Write judgment JSON matching the brief `output_contract` (include `summary_theme`).
4. Render + persist: `python -m psa advise <PATH> --judgment <judgment.json>`

Terminal operators may set `PSA_ADVISE_JUDGMENT` (path or inline JSON) or `PSA_ADVISE_CMD`
(command that reads brief stdin → judgment stdout). Without a bridge, `psa advise` exits 2.

Advise items are a **promotable backlog** (`.psa/advise.json`) — never auto-planned or auto-applied.

### Apply notes

- Requires a git repository.
- Commits land on `psa/optimise` (one commit per successful recommendation).
- Updates `.psa/state.json` and `PSA_STATUS.md`.
- Only recommendations with a registered executor are applied (ORDER001 today); others are skipped cleanly.
- Non-interactive shells require `--step` or `--dangerous`.
- When an Advise bridge is available, Apply may append one thematic line (`… - run psa advise`). Missing bridge never fails Apply.

## Hard rules

- Never fabricate scores, hit rates, costs, or latency claims.
- Every finding must cite evidence the user can open.
- Analysis, preview, and advise are read-only for instruction files.
- Apply only after explicit user request.
- Prefer `audit` for day-to-day; use `doctor` only for discovery troubleshooting.
- Never merge Advise items into Plan/Apply automatically.
