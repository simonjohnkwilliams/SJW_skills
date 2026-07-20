# Manual test plan — Releases 1–6

**Built through: R1 Audit → R2 Prioritise → R3 Preview → R4 Validate → R5 Apply → R6 Continuous (baseline/diff/CI).**

Automated: `cd scripts; $env:PYTHONPATH=(Get-Location).Path; python -m pytest`

**Release automation (R1–R4):**

```powershell
python -m pytest tests/acceptance/test_releases_r1_r4.py -v -s
```

Runs fixtures always; live VR1/VR2/VR3 when those paths exist on the machine.

User guide: [QUICKSTART.md](QUICKSTART.md)

## What was performed (engineering)

| Item | Done |
|------|------|
| R1 Discovery, model, rules, inventory, human+JSON audit, determinism | Yes |
| Phase 1 acceptance suite (A–I) | Yes |
| ORDER001 false-positive fix (On Hold / Debugging) | Yes |
| R2 Roadmap + “Fix these first” + dependency hints | Yes |
| R3 `psa patch preview` (ORDER001; finding id or rule id) | Yes |
| R4 `psa patch validate` (scratch re-audit; invariant) | Yes |
| R5 `psa patch apply` (git branch + commit + `--yes` + rollback text) | Yes |
| R6 `baseline save` / `diff` / `--fail-on-introduced` + GitHub Actions | Yes |

## Setup

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
```

---

### 1) R1 — Audit

```powershell
python -m psa inventory .\tests\fixtures\vr3_demo
python -m psa discover .
python -m psa inventory .
python -m psa audit .\tests\fixtures\vr3_demo
python -m psa audit .\tests\fixtures\vr3_demo --format json
```

**Pass if:** inventory lists AGENTS.md with a **Reason**; ignored skill/test trees show under Ignored when auditing a repo that contains the installed skill; JSON has `findings` and no `score` / `hit_rate` / `cost`.

**Regression (install-in-repo):** after copying the skill into `.cursor/skills/`, `discover` / `audit` on the **app** root must not emit findings from `.cursor/skills/**/scripts/tests/fixtures/**`.

**Optional live repos:** VR1 empty honesty; VR2 ACT; VR3 ORDER+STYLE+DUP without ORDER on “On Hold”.

---

### 2) R2 — Prioritise

In the text audit output, confirm:

- **Fix these first (roadmap)** with numbered unique rules  
- **Dependencies** (e.g. don’t apply ORDER001 until STYLE/DUP where edged)

**Pass if:** you can answer “what do I fix first?” without scanning the whole finding list.

---

### 3) R3 — Preview (no writes)

```powershell
git status --porcelain   # optional baseline
python -m psa patch preview ORDER001 .\tests\fixtures\vr3_demo
git status --porcelain   # unchanged
```

**Pass if:** unified diff only; working tree unchanged; `STYLE001` preview errors clearly if tried.

---

### 4) R4 — Validate

```powershell
python -m psa patch validate ORDER001 .\tests\fixtures\vr3_demo
python -m psa patch validate ORDER001 .\tests\fixtures\vr3_demo --format json
```

**Pass if:** `Result: PASS`, Introduced 0, exit code 0; fixture files unchanged.

---

### 5) R5 — Apply (throwaway git repo)

```powershell
$demo = Join-Path $env:TEMP "psa-apply-demo"
Remove-Item -Recurse -Force $demo -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $demo | Out-Null
Copy-Item .\tests\fixtures\vr3_demo\* $demo -Recurse
Set-Location $demo
git init
git add -A
git -c user.email=t@t -c user.name=t commit -m init
$env:PYTHONPATH = "c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts"
python -m psa patch apply ORDER001 . --yes
git log -1 --oneline
git branch --show-current
# Rollback when done:
# git checkout main   # or master
# git branch -D <psa/fix-…>
```

**Pass if:** refuses without `--yes` (exit 2); with `--yes` creates `psa/fix-…` branch, one commit, prints rollback text; `## CSV Format` appears before `## Current Focus` in `AGENTS.md`.

**Skip / note:** apply on OneDrive-synced trees may be unreliable — use a local temp path.

---

### 6) R6 — Continuous

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
python -m psa baseline save .\tests\fixtures\empty_repo --out empty.json
python -m psa diff .\tests\fixtures\vr3_demo --baseline empty.json
python -m psa diff .\tests\fixtures\vr3_demo --baseline empty.json --fail-on-introduced
echo $LASTEXITCODE   # expect 1
```

**Pass if:** Introduced > 0; `--fail-on-introduced` exits 1; no quality score in output.

**CI:** after push, `.github/workflows/psa.yml` should run pytest + CLI smoke.

---

## Skill smoke (Cursor)

1. `/prompt-structure-auditor` → inventory + audit + roadmap; offers preview/validate; **does not apply** unless asked.  
2. `/prompt-structure-auditor preview ORDER001` → diff only.  
3. `/prompt-structure-auditor validate ORDER001` → PASS/FAIL summary.  
4. `/prompt-structure-auditor apply ORDER001` → only with explicit user confirm; agent uses `--yes`.  
5. `/prompt-structure-auditor baseline` / `diff` → save + compare.  
