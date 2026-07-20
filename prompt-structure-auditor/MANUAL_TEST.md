# Manual test plan — current handoff

**Built through: Release 3 (Preview), plus partial Release 6 (baseline/diff).**  
**Not built: Release 4 Validate, Release 5 Apply, CI.**

Automated: `cd scripts; $env:PYTHONPATH=(Get-Location).Path; python -m pytest`  
User guide: [QUICKSTART.md](QUICKSTART.md)

## What was performed (engineering)

| Item | Done |
|------|------|
| R1 Discovery, model, rules, inventory, human+JSON audit, determinism | Yes |
| Phase 1 acceptance suite (A–I) | Yes |
| ORDER001 false-positive fix (On Hold / Debugging) | Yes |
| R2 Roadmap + “Fix these first” + dependency hints in report | Yes |
| R3 `psa patch preview ORDER001` (also accepts finding id) | Yes |
| R6 `baseline save` / `diff` | Yes |
| R4 validate / R5 apply | No |

## What you should manually test

### 1) R1 — Audit

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
python -m psa inventory .\tests\fixtures\vr3_demo
python -m psa audit .\tests\fixtures\vr3_demo
python -m psa audit .\tests\fixtures\vr3_demo --format json
```

Expect inventory + findings + honesty note; JSON has `findings` / no scores.

Live (optional): VR1 empty honesty; VR2 ACT; VR3 ORDER+STYLE+DUP without ORDER on “On Hold”.

### 2) R2 — Prioritise

In the text audit, expect **Fix these first (roadmap)** and **Dependencies** lines
(e.g. don’t apply ORDER001 until STYLE/DUP where edged).

### 3) R3 — Preview (no writes)

```powershell
git status --porcelain   # in a throwaway copy if needed
python -m psa patch preview ORDER001 .\tests\fixtures\vr3_demo
git status --porcelain   # unchanged
```

Expect unified diff only.

### 4) Confirm unavailable

```powershell
python -m psa patch validate ORDER001   # should fail (unknown command)
python -m psa patch apply ORDER001      # should fail
```

### 5) R6 partial

```powershell
python -m psa baseline save .\tests\fixtures\empty_repo --out empty.json
python -m psa diff .\tests\fixtures\vr3_demo --baseline empty.json
```

Expect Introduced > 0.

## Skill smoke (Cursor)

1. `/prompt-structure-auditor` → agent runs inventory + audit + explains roadmap; stops before apply.  
2. `/prompt-structure-auditor preview ORDER001` → shows diff only.
