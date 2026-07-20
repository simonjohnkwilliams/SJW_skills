# Manual test plan — Prompt Structure Auditor

Branch: `feat/prompt-structure-auditor`

Automated suite: **85 tests** (acceptance A–I + unit/functional/determinism + recommend/lifecycle/patch preview).

## Phase 1 sign-off status

| Criterion | Status |
|-----------|--------|
| All automated tests pass | ✅ 85 passed |
| Acceptance suite covers A/D/P/R/REP/G/CLI/I | ✅ `tests/acceptance/test_phase1_acceptance.py` |
| VR1/VR2/VR3 expected findings | ✅ fixtures + live smokes |
| Deterministic / read-only / immutable model | ✅ A001–A003 |
| Evidence + ownership + verification; no fabricated metrics | ✅ REP/I |
| ORDER001 not noisy on On Hold / Debugging | ✅ fixed + regression (G003) |

## What was constructed

| Area | Status |
|------|--------|
| Core Engine + discovery + Prompt Model | Done |
| Inventory / audit CLI | Done |
| Rules ORDER001, ACT001/002, STYLE001, DUP001 | Done |
| Phase 1 acceptance suite | Done |
| Recommendation dependency graph + roadmap | Done |
| Baseline save + audit diff CLI | Done |
| Patch **preview** (ORDER001 mechanical move) | Done |
| Patch validate / apply | **Not built** |
| OWNERSHIP / CONTRADICTION / VOL named rules | **Not built** |
| CI workflow | **Not built** |

### Documented ORDER001 edge case (closed)

Previously, headings like "On Hold" / "Debugging" / "Known Issue" were classified as ORDER001 prefix poison.  
**Fix:** only *session-dynamic* signals (`Current Focus`, sprint/ticket/date/session counter) raise ORDER001. Worklog headings feed STYLE001 instead. Regression: `test_G003_*`.

## Run automated tests

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
python -m pytest
```

## Manual tests

### M1 — Determinism (A001)

```powershell
python -m psa audit .\tests\fixtures\vr3_demo --format json --out a.json
python -m psa audit .\tests\fixtures\vr3_demo --format json --out b.json
fc /b a.json b.json
```

### M2 — Read-only (A002)

```powershell
cd <any-git-repo>
git status --porcelain
python -m psa audit .
git status --porcelain
```

Expect unchanged working tree (unless `--out`).

### M3 — Live VR3

```powershell
python -m psa audit "C:\Users\simon\OneDrive\demo\demo" --format text
```

Expect: one genuine ORDER001 on Current Focus; STYLE001; DUP001; **no** ORDER001 on On Hold/Debugging/Known Issue; roadmap section present.

### M4 — Live VR2

```powershell
python -m psa audit "C:\Users\simon\IdeaProjects\lateTrainQueries" --format text
```

Expect: ACT001/ACT002; DUP; no ORDER001 from `_bmad-output` references.

### M5 — Live VR1

```powershell
python -m psa inventory "C:\Users\simon\IdeaProjects\ai-context-benchmark"
python -m psa audit "C:\Users\simon\IdeaProjects\ai-context-benchmark" --format text
```

Expect: honest empty instruction surface; research out of scope.

### M6 — Baseline / diff

```powershell
python -m psa baseline save .\tests\fixtures\empty_repo --out empty-base.json
python -m psa diff .\tests\fixtures\vr3_demo --baseline empty-base.json
```

Expect: Introduced > 0.

### M7 — Patch preview (no write)

```powershell
python -m psa audit .\tests\fixtures\vr3_demo --format json --out audit.json
# copy an ORDER001 id from audit.json, then:
python -m psa patch preview <FINDING_ID> .\tests\fixtures\vr3_demo
```

Expect: unified diff only; working tree unchanged.

## Suggested next work

1. Patch validate (re-audit scratch; must-not-worsen invariant)
2. Patch apply (branch + one commit)
3. OWNERSHIP / CONTRADICTION packs
4. CI workflow + root README skill table update
