---
name: prompt-structure-auditor
description: >-
  Audits the repository prompt-construction surface (CLAUDE.md, AGENTS.md,
  Cursor rules, and related sources) for structural issues: ordering, volatility,
  duplication, activation metadata, and style. Produces evidence-backed findings,
  a separate Recommended Plan (`psa plan`), semantic implementation preview
  (`psa preview` / `--step`), ORDER001 patch validate/apply, and baseline/diff —
  with no fabricated cache scores. Use when the user runs /prompt-structure-auditor,
  asks to audit prompt structure, run psa plan for remediation order, run psa
  preview for implementation intent, run psa doctor on discovery, validate/apply
  an ORDER001 fix, or save/diff an audit baseline.
disable-model-invocation: true
---

# Prompt Structure Auditor

Deterministic static analysis of the prompt surface. Follow the RFC honesty rules:
report only observables; label inference; never invent cache hit rates or cost savings.

**Do not rewrite files** unless the user explicitly asks for patch **apply**.
Preview and validate are read-only. Apply requires `--yes` after a passing validate.

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
| `psa doctor` | Why was (or wasn't) something analysed? |
| `psa patch validate` | If applied, is it safe? |
| `psa patch apply` | Apply the validated change |

There is **no** public `inventory` or `discover` command. Audit never includes recommendations — use **`psa plan`**. Preview never emits diffs — use **`psa preview`**.

## Modes

### Default (`/prompt-structure-auditor`)

1. Run **`python -m psa audit <PATH>`** (text). Present **Summary** and **Findings** only (do not invent recommendations).
2. If the user asks what to fix / prioritise, run **`python -m psa plan <PATH>`** and present the **Recommended Plan**.
3. If the user asks what will change / how a step is implemented, run **`psa preview`** or **`psa preview --step N`**.
4. If the user questions discovery (missing files, unexpected ignores), run **`psa doctor`**.
5. If `ORDER001` exists and they want a mechanical change path: validate → apply.
6. **Do not apply** unless explicitly asked (`--yes`).

### `/prompt-structure-auditor audit`

```powershell
python -m psa audit <PATH>
python -m psa audit <PATH> --format json
```

### `/prompt-structure-auditor plan`

```powershell
python -m psa plan <PATH>
python -m psa plan <PATH> --format json
```

### `/prompt-structure-auditor preview`

```powershell
python -m psa preview <PATH>
python -m psa preview --step 1 <PATH>
```

### `/prompt-structure-auditor doctor`

```powershell
python -m psa doctor <PATH>
python -m psa doctor <PATH> --no-default-ignores
```

### `/prompt-structure-auditor validate` / `apply`

```powershell
python -m psa patch validate ORDER001 <PATH>
python -m psa patch apply ORDER001 <PATH> --yes
```

### `/prompt-structure-auditor baseline` / `diff`

```powershell
python -m psa baseline save <PATH> --out .psa-baseline.json
python -m psa diff <PATH> --baseline .psa-baseline.json --fail-on-introduced
```

## Hard rules

- Never fabricate scores, hit rates, costs, or latency claims.
- Every finding must cite evidence the user can open.
- Analysis, preview, and validate are read-only.
- Preview explains semantic implementation — never unified diffs.
- Apply only after explicit user confirmation and a passing validate.
- Prefer `audit` for day-to-day; use `doctor` only for discovery troubleshooting.
