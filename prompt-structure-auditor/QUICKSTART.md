# Prompt Structure Auditor — Quickstart

Skill name: **`prompt-structure-auditor`**  
CLI package: **`psa`** (under `prompt-structure-auditor/scripts/`)

---

## CLI product map

| Command | User question |
|---------|----------------|
| **`psa audit`** | Is my prompt architecture healthy? |
| **`psa doctor`** | Why was (or wasn't) something analysed? |
| `psa patch preview` | What exactly would change? (R3) |
| `psa patch validate` | Is the proposed change safe? (R4) |
| `psa patch apply` | Apply the validated change (R5) |
| `psa baseline` / `diff` | Continuous comparison (R6) |

---

## Release 1 audit UX contract (frozen)

`psa audit` text output is the **stable public interface**. Every repository gets the same structure:

1. **Prompt Structure Auditor** (title)
2. **Summary** (table — fixed fields, fixed order)
3. **Findings** (table — always present; placeholder row when empty)

Future releases may **append** sections after Findings only. They must not reorder, rename, or reshape Summary or Findings.

### Summary fields (fixed)

| Field | Description |
|-------|-------------|
| Repository | Repository name |
| Active Prompt Sources | Instruction files discovered |
| Documentation | AI-relevant guidance only (not all Markdown) |
| Configuration | Prompt-related config files |
| Status | `Healthy` or `Needs Attention` |
| Findings | `None` or `N (x High, y Medium, …)` |

### Findings columns (fixed)

`Severity | Rule | Issue`

Empty repositories render one placeholder row:

`| - | - | No prompt architecture issues detected |`

Diagnostics (ignores, patterns, parsers) belong in **`psa doctor` only**.

Output is ASCII-safe for standard Windows terminals (no emoji, no UTF-8 requirement).

---

## Where we are (release map)

| Release | Outcome | Status |
|---------|---------|--------|
| **R1 – Audit** | Health report (frozen UX) | **Complete** — fixtures + live |
| **R2 – Prioritise** | Remediation plan | Covered in suite (`recommend` / matrix) |
| **R3 – Preview** | Exact change | Covered in suite (`ORDER001`) |
| **R4 – Validate** | Safe change | Covered in suite |
| **R5 – Apply** | Apply on branch | Covered in suite (temp copy; live refuse-only) |
| **R6 – Continuous** | Baseline / diff / CI | Covered in suite |

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

1. Run **`psa audit`** — present the title, Summary, and Findings tables as-is  
2. If discovery looks wrong → **`psa doctor`**  
3. Preview/validate/apply only when asked  

| You say | Command |
|---------|---------|
| `audit` | `python -m psa audit <PATH>` |
| `doctor` | `python -m psa doctor <PATH>` |
| `preview ORDER001` | `python -m psa patch preview ORDER001 <PATH>` |
| `validate` / `apply` | patch validate / apply `--yes` |

---

## Day-to-day

```powershell
python -m psa audit .
python -m psa doctor .          # diagnostics only
python -m psa audit . --format json
```

### Example audit (healthy)

```
Prompt Structure Auditor

Summary

| Field | Result |
| --- | --- |
| Repository | financeTracker_SW |
| Active Prompt Sources | 1 instruction file |
| Documentation | 0 files |
| Configuration | 2 files |
| Status | Healthy |
| Findings | None |

Findings

| Severity | Rule | Issue |
| --- | --- | --- |
| - | - | No prompt architecture issues detected |
```

---

## Releases 3–6 (unchanged commands)

```powershell
python -m psa patch preview ORDER001 .
python -m psa patch validate ORDER001 .
python -m psa patch apply ORDER001 . --yes
python -m psa baseline save . --out .psa-baseline.json
python -m psa diff . --baseline .psa-baseline.json --fail-on-introduced
```

See [MANUAL_TEST.md](MANUAL_TEST.md).
