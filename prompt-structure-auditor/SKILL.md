---
name: prompt-structure-auditor
description: >-
  Audits the repository prompt-construction surface (CLAUDE.md, AGENTS.md,
  Cursor rules, and related sources) for structural issues: ordering, volatility,
  duplication, activation metadata, and style. Produces evidence-backed findings,
  a prioritised roadmap, and optional ORDER001 patch previews — with no fabricated
  cache scores. Use when the user runs /prompt-structure-auditor, asks to audit
  prompt structure, inventory agent instructions, preview an ORDER001 fix, or
  save/diff an audit baseline.
disable-model-invocation: true
---

# Prompt Structure Auditor

Deterministic static analysis of the prompt surface. Follow the RFC honesty rules:
report only observables; label inference; never invent cache hit rates or cost savings.

**Do not rewrite files** unless the user explicitly asks for patch **apply** (not
shipped yet). Preview is read-only.

## Setup

From the skill `scripts/` directory:

```powershell
$env:PYTHONPATH = (Resolve-Path .).Path
python -m psa --help
```

See [QUICKSTART.md](QUICKSTART.md) for release status and expected outputs.

## Modes

### Default — full flow through preview (`/prompt-structure-auditor`)

When the user invokes the skill without a subcommand:

1. Run **inventory** on the target repo (default: workspace root).
2. Run **audit** (text). Present:
   - Inventory
   - Executive Summary
   - **Fix these first (roadmap)**
   - Findings (evidence-backed)
   - Honesty note
3. If the user wants to see a change and `ORDER001` exists, offer **patch preview**
   (`python -m psa patch preview ORDER001 <path>`). Show the diff only.
4. **Stop.** Do not run validate/apply (not available). Do not modify the repo.

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

### `/prompt-structure-auditor baseline`

```powershell
python -m psa baseline save <PATH> --out .psa-baseline.json
```

### `/prompt-structure-auditor diff`

```powershell
python -m psa diff <PATH> --baseline .psa-baseline.json
```

## Release availability (agent must respect)

| Release | Available |
|---------|-----------|
| R1 Audit | Yes |
| R2 Prioritise | Yes (part of audit report) |
| R3 Preview | Yes (`ORDER001` only) |
| R4 Validate | **No** — say so if asked |
| R5 Apply | **No** — say so if asked |
| R6 Baseline/diff | Yes (CLI); CI not wired |

## Hard rules

- Never fabricate scores, hit rates, costs, or latency claims.
- Every finding must cite evidence the user can open.
- Analysis is read-only. Preview does not write. Apply is not implemented.
