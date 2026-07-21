# Prompt Structure Auditor — Quickstart

Skill name: **`prompt-structure-auditor`**  
CLI package: **`psa`** (under `prompt-structure-auditor/scripts/`)

---

## CLI product map

| Command | User question |
|---------|----------------|
| **`psa audit`** | What do I have, and is it healthy? |
| **`psa plan`** | What should I fix first, and why? |
| **`psa preview`** | What will PSA change? |
| **`psa preview --step N`** | How will recommendation N be implemented? |
| **`psa doctor`** | Why was (or wasn't) something analysed? |
| `psa patch validate` | If applied, is it safe? (R4) |
| `psa patch apply` | Execute the validated change (R5) |
| `psa baseline` / `diff` | Continuous comparison (R6) |

**Product principle:** Audit, Plan, and Preview are separate capabilities. Audit is factual. Plan prioritises solutions. Preview explains implementation — never emits patches or diffs.

### Architectural assets (mutually exclusive)

Everything PSA discovers belongs in **exactly one** bucket:

| Bucket | Meaning | Examples |
|--------|---------|----------|
| **Instruction Assets** | Runtime prompt surfaces | `CLAUDE.md`, `AGENTS.md`, Cursor rules |
| **Guidance Surface** | Non-runtime docs that shape assistant behaviour | AI standards, prompt playbooks, `docs/ai/` |

Guidance is counted for honesty only — it never produces findings. Repos with only `docs/ai/` correctly report `Active Prompt Sources: 0` and `Guidance: N`.

---

## Release 1 audit UX contract (frozen)

`psa audit` text output is the **stable public audit interface**. Every repository gets the same structure:

1. **Prompt Structure Auditor** (title)
2. **Summary** (table — fixed fields, fixed order)
3. **Findings** (table — always present; placeholder row when empty)

**No recommendations, effort estimates, or plan steps in audit.**

### Summary fields (fixed)

| Field | Description |
|-------|-------------|
| Repository | Repository name |
| Active Prompt Sources | Instruction files discovered |
| Guidance | Guidance Surface — shapes assistant behaviour; never findings |
| Configuration | Prompt-related config files |
| Status | `Healthy` or `Needs Attention` |
| Findings | `None` or `N (x High, y Medium, …)` |

### Findings columns (fixed)

`Severity | Rule | Issue`

Empty repositories render one placeholder row:

`| - | - | No prompt architecture issues detected |`

Diagnostics belong in **`psa doctor` only**. Output is ASCII-safe for standard Windows terminals.

---

## Release 2 plan UX contract (frozen)

`psa plan` is a **separate, stable public interface** (ongoing through later releases).

Every repository gets the same structure:

1. **Prompt Structure Plan** (title)
2. **Summary** (fixed fields)
3. **Recommended Plan** (overview table — always present)
4. **Recommendation Details** (compact per-step notes)
5. **Expected end state** (where the full plan leads)

### Plan Summary fields (fixed)

| Field | Description |
|-------|-------------|
| Repository | Repository name |
| Findings considered | Count from audit |
| Recommendations | Number of plan steps |
| Status | `No action needed` or `Plan ready` |

### Recommended Plan columns (fixed)

`Step | Recommendation | Effort | Resolves | Why now`

`Why now` is the strategy cue (e.g. `Best open value (2 @ Small)` or `After Step 2`) so the sequence is readable without opening every detail.

### Each detail step (compact)

Why · Resolves · Effort · Depends on · After this step

Dependencies use **Depends on** only (no separate Unblocks section).

Future releases may append after **Expected end state** only.

---

## Release 3 preview UX contract (frozen)

`psa preview` is a **separate, stable public interface**. It answers implementation intent — not analysis, not validation.

### Overview (`psa preview`)

1. **Prompt Structure Preview** (title)
2. **Summary** (Repository, Recommendations, Unique files affected, Files added/modified/removed, Expected status)
3. **Implementation Plan** (Step | Recommendation | Files | Primary Change)
4. **Repository Impact** (semantic bullets)

### Step detail (`psa preview --step N`)

1. **Prompt Structure Preview**
2. **Recommendation**
3. **Summary** (Effort, Unique files affected, Primary change)
4. **Overview** (short scope paragraph)
5. **Intent**
6. **Implementation Plan** (per file: Purpose + Actions)
7. **Result**
8. **Repository Changes** (Modified / Added / Removed)

Preview is read-only. It never emits unified diffs, patches, or validation output.

---

## Where we are (release map)

| Release | Outcome | Status |
|---------|---------|--------|
| **R1 – Audit** | Health report (frozen UX) | **Complete** |
| **R2 – Plan** | `psa plan` frozen Recommended Plan | **Complete** |
| **R3 – Preview** | Semantic implementation preview | **Complete** (contract frozen) |
| **R4 – Validate** | Safe change | Ready |
| **R5 – Apply** | Apply on branch | Ready |
| **R6 – Continuous** | Baseline / diff / CI | Ready |

---

## Setup (once)

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
python -m pytest
```

---

## Skill invocations (Cursor)

```
/prompt-structure-auditor
```

1. Run **`psa audit`** — present Summary + Findings only  
2. Run **`psa plan`** when the user asks what to fix / prioritisation  
3. Run **`psa preview`** / **`psa preview --step N`** for implementation intent  
4. If discovery looks wrong → **`psa doctor`**  
5. Validate/apply only when asked  

| You say | Command |
|---------|---------|
| `audit` | `python -m psa audit <PATH>` |
| `plan` | `python -m psa plan <PATH>` |
| `preview` | `python -m psa preview <PATH>` |
| `preview --step N` | `python -m psa preview --step N <PATH>` |
| `doctor` | `python -m psa doctor <PATH>` |
| `validate` / `apply` | patch validate / apply `--yes` |

---

## Day-to-day

```powershell
python -m psa audit .
python -m psa plan .            # advisor — separate from audit
python -m psa preview .         # implementation overview
python -m psa preview --step 1  # one recommendation in detail
python -m psa doctor .          # diagnostics only
python -m psa audit . --format json
```

### Example audit (healthy) — no plan section

```
Prompt Structure Auditor

Summary

| Field | Result |
| --- | --- |
| Repository | financeTracker_SW |
| Active Prompt Sources | 1 instruction file |
| Guidance | 0 files |
| Configuration | 2 files |
| Status | Healthy |
| Findings | None |

Findings

| Severity | Rule | Issue |
| --- | --- | --- |
| - | - | No prompt architecture issues detected |
```

---

## Releases 4–6

```powershell
python -m psa patch validate ORDER001 .
python -m psa patch apply ORDER001 . --yes
python -m psa baseline save . --out .psa-baseline.json
python -m psa diff . --baseline .psa-baseline.json --fail-on-introduced
```

See [MANUAL_TEST.md](MANUAL_TEST.md).
