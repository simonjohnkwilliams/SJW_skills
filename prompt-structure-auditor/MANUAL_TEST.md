# Manual test plan — Prompt Structure Auditor v0.1

Branch: `feat/prompt-structure-auditor`

Automated suite: **31 unit/behaviour/functional/determinism tests** (fixtures) plus
optional live-repo smokes when VR1–VR3 paths exist.

## What was constructed

| Area | Status | Notes |
|------|--------|--------|
| Documentation (RFC/ADR/planning) | Done | Committed earlier on this branch |
| Package `psa` Core Engine | Done | `prompt-structure-auditor/scripts/psa/` |
| Discovery adapters | Done | CLAUDE.md, AGENTS.md, Cursor `.mdc`, config (Serena/OpenCode/Claude settings), research data exclusion |
| Prompt Model (immutable) | Done | Segments + `precedes`/`governs` edges; classifier |
| Inventory + human/JSON reports | Done | ASCII marks for Windows consoles |
| CLI `inventory` / `audit` | Done | `--format text\|json`, `--out` |
| Rules ORDER001, ACT001, ACT002, STYLE001, DUP001 | Done | Pack-toggleable via config defaults |
| Recommendation dependency graph | **Not built** | Empty stub in JSON (`nodes`/`edges` []) |
| Baseline / audit diff | **Not built** | |
| Patch preview / validate / apply | **Not built** | |
| VOL002 as named rule / OWNERSHIP / CONTRADICTION packs | **Not built** | Classifier covers references-vs-embeds for ORDER false positives |
| Full RFC adapter catalogue (Copilot live, builders, MCP) | Partial | Copilot absent-row in inventory only |
| CI workflow | **Not built** | |
| `pip install -e` on this machine | Blocked by SSL to PyPI | Use `PYTHONPATH=scripts` |

## Automated tests already covering

```text
cd prompt-structure-auditor/scripts
set PYTHONPATH=%CD%
python -m pytest
```

Expect: `31 passed` (without live repos) or more if live VR paths resolve.

## Manual tests (please run)

### M1 — Fixture inventory (walking skeleton)

```powershell
cd c:\Users\simon\cursor\SJW_skills\prompt-structure-auditor\scripts
$env:PYTHONPATH = (Get-Location).Path
python -m psa inventory .\tests\fixtures\vr1_empty
python -m psa inventory .\tests\fixtures\vr2_latetrain
python -m psa inventory .\tests\fixtures\vr3_demo
```

**Expect**
- VR1: AGENTS/CLAUDE/Cursor absent; config + research data listed
- VR2: Cursor Rules present
- VR3: AGENTS.md present

### M2 — Fixture audit JSON determinism

```powershell
python -m psa audit .\tests\fixtures\vr3_demo --format json --out a.json
python -m psa audit .\tests\fixtures\vr3_demo --format json --out b.json
fc /b a.json b.json
```

**Expect:** no differences; contains `ORDER001`, `STYLE001`, `DUP001`; no cache score fields.

### M3 — Live VR3 (demo)

```powershell
python -m psa audit "C:\Users\simon\OneDrive\demo\demo" --format text
```

**Expect:** ORDER001 (Current Focus before CSV Format), STYLE001 worklog, DUP001 TrueLayer repetition; honesty note; no hit-rate/cost claims.

### M4 — Live VR2 (lateTrainQueries)

```powershell
python -m psa audit "C:\Users\simon\IdeaProjects\lateTrainQueries" --format text
```

**Expect:** ACT001/ACT002 on dormant / missing-frontmatter rules; DUP on architecture freeze / one-story; **no** ORDER001 solely from `_bmad-output` references.

### M5 — Live VR1 (ai-context-benchmark)

```powershell
python -m psa inventory "C:\Users\simon\IdeaProjects\ai-context-benchmark"
python -m psa audit "C:\Users\simon\IdeaProjects\ai-context-benchmark" --format json
```

**Expect:** honest empty instruction surface; research outputs out of scope; no fabricated findings.

### M6 — Honesty / schema spot-check

Open JSON from M2/M3 and confirm each finding has:
- `priority` and `verification` as **separate** fields
- `evidence` with paths
- **no** `score`, `hit_rate`, `cost`, `stable_prefix_pct`

### M7 — Skill discoverability (optional)

Confirm `prompt-structure-auditor/SKILL.md` frontmatter `name` matches directory name for future `npx skills` install (not fully validated here due to packaging SSL).

## Suggested focus for your review

1. Are ACT001 findings on VR2 accurate enough (false positives on intentional `alwaysApply:false` with missing metadata)?
2. Is DUP001 phrase matching too blunt for TrueLayer / architecture families?
3. Confirm ORDER001 on real VR3 `AGENTS.md` matches the dry-run intent.
4. Priority for next slice: recommendation graph (R5) vs baseline/diff (R6) vs patch preview (R7).

## Out of scope this pass (do not test as if complete)

- Patch apply / validate invariant
- Audit diff vs baseline
- Recommendation roadmap ordering
- Cost/cache performance claims (intentionally absent)
