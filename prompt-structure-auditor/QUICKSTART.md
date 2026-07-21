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
| **`psa apply --step N`** | Safely apply one recommendation |
| **`psa apply`** | Continue optimisation (confirm between steps) |
| **`psa apply --dangerous`** | Continue without confirmation (validation still runs) |
| **`psa advise`** | What else is worth investigating beyond current rules? |
| **`psa doctor`** | Why was (or wasn't) something analysed? |
| `psa baseline` / `diff` | Continuous comparison (R6) |

**Product principle:** Audit → Plan → Preview → Apply, with optional **Advise** anytime (and after Apply when an embedded AI bridge is available). Validation is internal to Apply. Preview never emits patches. Apply uses pluggable executors (ORDER001 today) on branch `psa/optimise`, and updates `.psa/state.json` + `PSA_STATUS.md`. Advise writes `.psa/advise.json` (promotable backlog; never auto-applied).

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

## Release 5 advise UX contract

`psa advise` is a **separate scout** that finds gaps beyond the deterministic rule set. Judgment comes from an **embedded AI caller** (skill agent / `PSA_ADVISE_CMD` / `PSA_ADVISE_JUDGMENT` / `--judgment`) — PSA does not own an LLM API.

### Report shape (`Prompt Structure Advise`)

1. **Summary** (Repository, Advisory items, Investigation points, Status)
2. **Advisory Recommendations** (Step | Kind | Recommendation | Effort | Paths)
3. **Investigation Points** (same columns; `kind=conflict` when AI contradicts deterministic rules)
4. **Recommendation Details** + promotion footer

### Bridge

| Source | Use |
|--------|-----|
| `--brief-only` | Deterministic brief JSON for the caller AI |
| `--judgment PATH` | Render + persist from judgment JSON |
| `PSA_ADVISE_JUDGMENT` | Path or inline JSON |
| `PSA_ADVISE_CMD` | Command: brief on stdin → judgment on stdout |

Without a bridge, `psa advise` exits 2: `Advise requires an embedded AI caller.`

After Apply, if a bridge is available, the Apply report may include one thematic line (`… - run psa advise`). Missing bridge never fails Apply.

---

## Where we are (release map)

| Release | Outcome | Status |
|---------|---------|--------|
| **R1 – Audit** | Health report (frozen UX) | **Complete** |
| **R2 – Plan** | `psa plan` frozen Recommended Plan | **Complete** |
| **R3 – Preview** | Semantic implementation preview | **Complete** |
| **R4 – Apply** | Optimisation engine + persistent state | **Complete** |
| **R5 – Advise** | Embedded-AI scout + `.psa/advise.json` | **Complete** |
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
4. Run **`psa apply --step N`** when the user wants to execute  
5. After Apply (skill): run **Advise** and show the one-line theme; offer full report  
6. If discovery looks wrong → **`psa doctor`**  

| You say | Command |
|---------|---------|
| `audit` | `python -m psa audit <PATH>` |
| `plan` | `python -m psa plan <PATH>` |
| `preview` | `python -m psa preview <PATH>` |
| `preview --step N` | `python -m psa preview --step N <PATH>` |
| `apply --step N` | `python -m psa apply --step N <PATH>` |
| `apply --dangerous` | `python -m psa apply --dangerous <PATH>` |
| `advise --brief-only` | `python -m psa advise <PATH> --brief-only` |
| `advise --judgment` | `python -m psa advise <PATH> --judgment judgment.json` |
| `doctor` | `python -m psa doctor <PATH>` |

---

## Day-to-day

```powershell
python -m psa audit .
python -m psa plan .            # advisor — separate from audit
python -m psa preview .         # implementation overview
python -m psa preview --step 1  # one recommendation in detail
python -m psa apply --step 1    # apply one recommendation (git repo)
python -m psa advise . --brief-only
python -m psa advise . --judgment judgment.json
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

## Apply + Advise + continuous (R4/R5 + R6)

```powershell
python -m psa apply --step 1 .
python -m psa apply --dangerous .
python -m psa advise . --brief-only
python -m psa advise . --judgment .\tests\fixtures\advise_judgment.json
python -m psa baseline save . --out .psa-baseline.json
python -m psa diff . --baseline .psa-baseline.json --fail-on-introduced
```

Apply writes commits on `psa/optimise`, updates `.psa/state.json` and `PSA_STATUS.md`. Unsupported recommendation types are skipped cleanly (no executor yet). Advise persists `.psa/advise.json` and an Advise Backlog section in `PSA_STATUS.md`.

See [MANUAL_TEST.md](MANUAL_TEST.md).
