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

`inventory` and `discover` are **not** public commands. Internals unchanged.

---

## Where we are (release map)

| Release | Outcome | Status |
|---------|---------|--------|
| **R1 – Audit (read-only)** | Tell me what's wrong | **Ready** (`audit` + `doctor`) |
| **R2 – Prioritise** | Tell me what to fix first | **Ready** (in findings; dedicated `recommend` later) |
| **R3 – Preview** | Show the exact change | **Ready** (`ORDER001` only) |
| **R4 – Validate** | Prove fix does not worsen audit | **Ready** |
| **R5 – Apply** | Apply validated fix on a git branch | **Ready** (local git repos; not OneDrive) |
| **R6 – Continuous** | Baselines / diff / CI | **Ready** |

Manual-test focus: walk R1 → R6 using [MANUAL_TEST.md](MANUAL_TEST.md).

---

## Setup (once)

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
python -m pytest
```

---

## Skill invocations (Cursor)

### Default — primary health check

```
/prompt-structure-auditor
```

**Agent should:**

1. Run **`psa audit`** (text) — present Repository / Status / Findings / Honesty note  
2. If discovery looks wrong, run **`psa doctor`**  
3. If an `ORDER001` finding exists and the user wants a change path: preview → validate  
4. **Apply only** when the user explicitly asks (`--yes`)

### Per-command map

| You say / run | Maps to |
|---------------|---------|
| `/prompt-structure-auditor audit` | R1 health check |
| `/prompt-structure-auditor doctor` | R1 diagnostics |
| `/prompt-structure-auditor preview ORDER001` | R3 |
| `/prompt-structure-auditor validate ORDER001` | R4 |
| `/prompt-structure-auditor apply ORDER001` | R5 |
| `/prompt-structure-auditor baseline` / `diff` | R6 |

---

## Release 1 — `audit` (primary) + `doctor` (diagnostics)

Discovery **ignores test/fixture trees by default** (including an installed skill’s
`scripts/tests/fixtures`). Override with `--no-default-ignores`.

### Day-to-day

```powershell
python -m psa audit .
python -m psa audit . --format json
```

### Expected audit text

```
Repository
  financeTracker_SW

Prompt Sources
  1 instruction source
  2 configuration files
  2 ignored paths
  8 data files excluded

Status
  Healthy
  # or: Issues found

Findings
  No prompt architecture issues detected.
  # or grouped High / Medium / … with recommendations

Honesty note
  …

Run `psa doctor` for discovery details.
```

JSON still has full `meta` / `inventory` / `findings` / `dependency_graph` (no fabricated scores).

### Diagnostics

```powershell
python -m psa doctor .
python -m psa doctor . --no-default-ignores
```

Lists instruction/config/data paths, ignored roots with **pattern matched**, ignore pattern list, adapters not found, and config flags.

---

## Release 2 — Prioritise

Findings in `audit` already include per-finding recommendations. A dedicated
`psa recommend` command is planned; until then, use finding recommendations
(and JSON `dependency_graph` for tooling).

---

## Release 3 — Preview

```powershell
python -m psa patch preview ORDER001 .
```

---

## Release 4 — Validate

```powershell
python -m psa patch validate ORDER001 .
```

---

## Release 5 — Apply

```powershell
python -m psa patch apply ORDER001 . --yes
```

---

## Release 6 — Continuous

```powershell
python -m psa baseline save . --out .psa-baseline.json
python -m psa diff . --baseline .psa-baseline.json --fail-on-introduced
```

CI: `.github/workflows/psa.yml`.

---

## Suggested manual test path

1. **R1** `audit` on `tests\fixtures\vr3_demo` — quiet health view + JSON  
2. **R1** `doctor` — reasons + ignore patterns  
3. **R3–R5** preview → validate → apply (temp git clone)  
4. **R6** baseline/diff  

Automated: `python -m pytest`

---

## Honesty constraints

- Observable vs inference labelled  
- No cache hit rate / cost / latency metrics  
- Analysis and preview/validate are read-only; apply needs `--yes`  
