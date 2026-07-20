# Prompt Structure Auditor — Quickstart

Skill name: **`prompt-structure-auditor`**  
CLI package: **`psa`** (under `prompt-structure-auditor/scripts/`)

---

## Where we are (release map)

| Release | Outcome | Status |
|---------|---------|--------|
| **R1 – Audit (read-only)** | Tell me what's wrong | **Ready** |
| **R2 – Prioritise** | Tell me what to fix first | **Ready** |
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

In Cursor, install/copy the skill so `@prompt-structure-auditor` / `/prompt-structure-auditor` works, or run the CLI from `scripts/` as below.

---

## Skill invocations (Cursor)

### Full guided flow (through validate; apply only if asked)

```
/prompt-structure-auditor
```

or

```
@prompt-structure-auditor audit this repository end-to-end through validate
```

**Agent should:**

1. Run inventory  
2. Run audit (text)  
3. Summarise “Fix these first” from the roadmap  
4. If an `ORDER001` finding exists, run **patch preview**, then **patch validate**  
5. **Apply only** when the user explicitly asks (`--yes`); never apply by default  

### Per-release commands (agent or CLI)

| You say / run | Maps to |
|---------------|---------|
| `/prompt-structure-auditor inventory` | R1 inventory |
| `/prompt-structure-auditor audit` | R1+R2 audit + prioritise |
| `/prompt-structure-auditor preview ORDER001` | R3 preview |
| `/prompt-structure-auditor validate ORDER001` | R4 validate |
| `/prompt-structure-auditor apply ORDER001` | R5 apply (requires confirm) |
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

---

## Release 4 — Validate

```powershell
python -m psa patch validate ORDER001 .
python -m psa patch validate ORDER001 . --format json
```

### Expected

```
Patch Validation
  Target:     ORDER001 (f_…)
  Result:     PASS
  Resolved:   N
  Introduced: 0
  Worsened:   0
```

- Exit **0** on PASS, **1** on FAIL  
- Scratch copy only — **no writes** to the target repo  
- FAIL if target not resolved, new findings introduced, or priority worsens  

---

## Release 5 — Apply

Requires a **local git repository** (apply is refused on non-git trees). Prefer a throwaway clone; avoid OneDrive-synced paths if git is flaky there.

```powershell
# Always validate first (apply also re-validates)
python -m psa patch validate ORDER001 .
python -m psa patch apply ORDER001 . --yes
# optional: --branch psa/fix-order001-demo
```

Without `--yes`, apply exits **2** and writes nothing.

### Expected

```
Patch Applied
  Branch:  psa/fix-order001-…
  Commit:  <sha>
  Path:    AGENTS.md
  Message: psa: apply ORDER001 (…)
Rollback: git checkout - && git branch -D …
```

Working tree is on the new branch with one commit. Use the printed rollback instructions to undo.

---

## Release 6 — Continuous (baseline / diff / CI)

```powershell
python -m psa baseline save . --out .psa-baseline.json
# … change prompt files …
python -m psa diff . --baseline .psa-baseline.json
# CI ratchet — non-zero if anything new appeared:
python -m psa diff . --baseline .psa-baseline.json --fail-on-introduced
```

### Expected

```
Audit Diff
  Resolved:   N
  Introduced: N
  Unchanged:  N
```

No composite quality score.

### CI

Workflow: `.github/workflows/psa.yml` — installs `psa`, runs pytest, and smokes inventory/audit/baseline/diff/preview/validate on fixtures.

---

## Suggested manual test path

1. **R1** on `tests\fixtures\vr3_demo` — inventory + audit text + JSON  
2. **R2** — confirm “Fix these first” + dependency lines  
3. **R3** — `patch preview ORDER001`; confirm no file writes  
4. **R4** — `patch validate ORDER001` → PASS  
5. **R5** — copy fixture into a temp git repo; `apply … --yes`; confirm branch + rollback  
6. **R6** — baseline on empty fixture, diff against vr3, `--fail-on-introduced` → exit 1  

Automated gate: `python -m pytest` → expect **120+** passed.  
R1–R4 release matrix (fixtures + live sample repos when present):

```powershell
python -m pytest tests/acceptance/test_releases_r1_r4.py -v -s
```

---

## Honesty constraints (all releases)

- Observable vs inference labelled  
- No cache hit rate / cost / latency / token-saving metrics  
- Analysis and preview/validate are read-only; apply writes only with `--yes` after validation  
