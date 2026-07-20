# Prompt Structure Auditor — Quickstart

Skill name: **`prompt-structure-auditor`**  
CLI package: **`psa`** (under `prompt-structure-auditor/scripts/`)

---

## Where we are (release map)

| Release | Outcome | Status |
|---------|---------|--------|
| **R1 – Audit (read-only)** | Tell me what's wrong | **Ready for manual test** |
| **R2 – Prioritise** | Tell me what to fix first | **Ready** (roadmap + “Fix these first”) |
| **R3 – Preview** | Show the exact change | **Ready** for `ORDER001` only |
| **R4 – Validate** | Prove fix does not worsen audit | **Not built** |
| **R5 – Apply** | Apply validated fix on a branch | **Not built** |
| **R6 – Continuous** | Baselines / diff / CI health | **Partial** (`baseline save` + `diff`; no CI yet) |

**Manual-test focus now:** R1 → R2 → R3 (stop before apply). Treat R4/R5 as unavailable.

---

## Setup (once)

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
# Optional: python -m pytest
```

In Cursor, install/copy the skill so `@prompt-structure-auditor` / `/prompt-structure-auditor` works, or run the CLI from `scripts/` as below.

---

## Skill invocations (Cursor)

### Full guided flow (until preview — not apply)

```
/prompt-structure-auditor
```

or

```
@prompt-structure-auditor audit this repository end-to-end through preview
```

**Agent should:**

1. Run inventory  
2. Run audit (text)  
3. Summarise “Fix these first” from the roadmap  
4. If an `ORDER001` finding exists and user wants a preview, run patch preview  
5. **Stop** — do not validate/apply unless those commands exist and the user explicitly asks  

### Per-release commands (agent or CLI)

| You say / run | Maps to |
|---------------|---------|
| `/prompt-structure-auditor inventory` | R1 inventory |
| `/prompt-structure-auditor audit` | R1+R2 audit + prioritise |
| `/prompt-structure-auditor preview ORDER001` | R3 preview |
| `/prompt-structure-auditor baseline` | R6 save baseline |
| `/prompt-structure-auditor diff` | R6 compare to baseline |

---

## Release 1 — Audit (read-only)

### CLI

```powershell
python -m psa inventory .
python -m psa audit .
python -m psa audit . --format json
```

### Expected output (inventory)

```
Prompt Surface Inventory

Discovered (instruction)
  [x] AGENTS.md  1 file(s)          # or Cursor Rules / CLAUDE.md

Not found
  [ ] Claude instructions
  ...
```

Empty repos also list absences and may show config/data as out of scope — **no fabricated findings**.

### Expected output (audit text)

- Prompt Surface Inventory  
- Executive Summary (counts by priority, or honest empty message)  
- Findings with: rule id, priority, verification, ownership, evidence, explanation, recommendation  
- Honesty note (no cache hit rate / cost claims)  
- **No** `score`, `hit_rate`, `cost` fields in JSON  

### Expected output (audit JSON)

Top-level keys: `meta`, `inventory`, `findings`, `dependency_graph`.  
Each finding: `id`, `rule_id`, `priority`, `verification`, `ownership`, `evidence`, `confidence`, …

---

## Release 2 — Prioritise

Same command: `python -m psa audit .`

### Extra expected sections

```
Fix these first (roadmap)
  1. [STYLE001] ...
  2. [DUP001] ...
  3. [ORDER001] ...
  Dependencies
    - Do not apply [ORDER001] until [STYLE001] (...)
    - Do not apply [ORDER001] until [DUP001] (...)

Implementation Roadmap
  1. ...
```

**Usability check:** you should leave with “fix these N first”, not only a flat list of findings.

---

## Release 3 — Preview

```powershell
python -m psa patch preview ORDER001 .
# or: python -m psa patch preview f_<id> .
```

### Expected

- Unified diff on stdout  
- Working tree **unchanged** (`git status` clean of tool writes)  
- Only mechanical move for ORDER001 today  
- Non-patchable rules (e.g. STYLE001) error clearly  

### Not available yet

```powershell
python -m psa patch validate ORDER001   # R4 — missing
python -m psa patch apply ORDER001      # R5 — missing
```

---

## Release 6 (partial) — Baseline / diff

```powershell
python -m psa baseline save . --out .psa-baseline.json
# … change prompt files …
python -m psa diff . --baseline .psa-baseline.json
```

### Expected

```
Audit Diff
  Resolved:   N
  Introduced: N
  Unchanged:  N
```

No composite quality score.

---

## Suggested manual test path (this handoff)

1. **R1** on fixture `tests\fixtures\vr3_demo` — inventory + audit text + JSON  
2. **R1** on live VR1 (empty honesty) / VR2 (ACT) / VR3 (ORDER+STYLE+DUP)  
3. **R2** — confirm “Fix these first” + dependency lines  
4. **R3** — `patch preview ORDER001` on fixture; confirm no file writes  
5. **Stop** — do not expect validate/apply  

Automated gate: `python -m pytest` → expect **85+** passed.

---

## Honesty constraints (all releases)

- Observable vs inference labelled  
- No cache hit rate / cost / latency / token-saving metrics  
- Analysis is read-only until R5 Apply (not shipped)  
