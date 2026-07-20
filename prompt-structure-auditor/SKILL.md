---
name: prompt-structure-auditor
description: >-
  Audits the repository prompt-construction surface (CLAUDE.md, AGENTS.md,
  Cursor rules, and related sources) for structural issues: ordering, volatility,
  duplication, activation metadata, and style. Produces evidence-backed findings,
  a prioritised roadmap, ORDER001 patch preview/validate/apply, and baseline/diff
  for continuous checks — with no fabricated cache scores. Use when the user runs
  /prompt-structure-auditor, asks to audit prompt structure, inventory agent
  instructions, preview/validate/apply an ORDER001 fix, or save/diff an audit
  baseline.
disable-model-invocation: true
---

# Prompt Structure Auditor

Deterministic static analysis of the prompt surface. Follow the RFC honesty rules:
report only observables; label inference; never invent cache hit rates or cost savings.

**Do not rewrite files** unless the user explicitly asks for patch **apply**.
Preview and validate are read-only. Apply requires `--yes` after a passing validate.

## Setup

From the skill `scripts/` directory:

```powershell
$env:PYTHONPATH = (Resolve-Path .).Path
python -m psa --help
```

See [QUICKSTART.md](QUICKSTART.md) for release status and expected outputs.
See [MANUAL_TEST.md](MANUAL_TEST.md) for the R1–R6 manual checklist.

## Modes

### Default — full flow through validate (`/prompt-structure-auditor`)

When the user invokes the skill without a subcommand:

1. Run **inventory** on the target repo (default: workspace root).
2. Run **audit** (text). Present:
   - Inventory
   - Executive Summary
   - **Fix these first (roadmap)**
   - Findings (evidence-backed)
   - Honesty note
3. If `ORDER001` exists, run **patch preview**, then **patch validate**. Show diff + PASS/FAIL.
4. **Do not apply** unless the user explicitly asks. Then re-validate and run
   `python -m psa patch apply ORDER001 <path> --yes`.

### `/prompt-structure-auditor inventory`

```powershell
python -m psa inventory <PATH>
```

### `/prompt-structure-auditor audit`

```powershell
python -m psa audit <PATH>
python -m psa audit <PATH> --format json
```

### `/prompt-structure-auditor preview` (or `preview ORDER001`)

```powershell
python -m psa patch preview ORDER001 <PATH>
```

Accepts a rule id (`ORDER001`) or finding id (`f_…`). Preview only — no writes.

### `/prompt-structure-auditor validate` (or `validate ORDER001`)

```powershell
python -m psa patch validate ORDER001 <PATH>
```

Scratch re-audit; exit 0 only if the target is resolved and the audit does not worsen.

### `/prompt-structure-auditor apply` (or `apply ORDER001`)

```powershell
python -m psa patch apply ORDER001 <PATH> --yes
```

Requires a git repository. Creates `psa/fix-…` branch, one commit, prints rollback.
Refuse if the user has not confirmed apply.

### `/prompt-structure-auditor baseline`

```powershell
python -m psa baseline save <PATH> --out .psa-baseline.json
```

### `/prompt-structure-auditor diff`

```powershell
python -m psa diff <PATH> --baseline .psa-baseline.json
python -m psa diff <PATH> --baseline .psa-baseline.json --fail-on-introduced
```

## Release availability (agent must respect)

| Release | Available |
|---------|-----------|
| R1 Audit | Yes |
| R2 Prioritise | Yes (part of audit report) |
| R3 Preview | Yes (`ORDER001` only) |
| R4 Validate | Yes |
| R5 Apply | Yes (local git; `--yes` required) |
| R6 Baseline/diff/CI | Yes |

## Hard rules

- Never fabricate scores, hit rates, costs, or latency claims.
- Every finding must cite evidence the user can open.
- Analysis, preview, and validate are read-only.
- Apply only after explicit user confirmation and a passing validate.
