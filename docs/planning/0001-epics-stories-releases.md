# Prompt Structure Auditor — Epics, Stories & Releases

| Field | Value |
|-------|-------|
| **Status** | Draft — for review before Phase 1 coding |
| **Implements** | [RFC 0001 v0.2.0](../rfc/0001-prompt-structure-auditor.md), [ADR 0001](../adr/0001-implementation-plan.md) |
| **Validated against** | [RFC 0001 Validation Dry-Run](../rfc/0001-validation.md) |
| **Companion** | [Build Order](./0001-build-order.md) |

> **Scope.** Units of work only. No code. Stories are sized so each release
> delivers a **testable functional capability**. Acceptance criteria cite the
> three validation repositories and ADR Definition of Done (§15).
>
> **Terminology (v0.2.0).** Validation dry-run used v0.1.0 names. Stories use
> current names; expected findings map as: `CACHE*` → `ORDER*`/`VOL*`,
> `Blocked` → `requires-verification`, activation issues → `ACTIVATION` pack.

---

## 0. Validation repositories (test oracles)

| Alias | Path | Role in acceptance |
|-------|------|--------------------|
| **VR1** | `C:\Users\simon\IdeaProjects\ai-context-benchmark` | Empty / near-empty prompt surface; honest zero-findings; config vs instruction vs data |
| **VR2** | `C:\Users\simon\IdeaProjects\lateTrainQueries` | Cursor rules + activation metadata; duplication; tool-owned BMAD skills; references-vs-embeds |
| **VR3** | `C:\Users\simon\OneDrive\demo\demo` | `AGENTS.md` worklog / ordering / volatility / duplication |

**Fixture policy.** Golden tests use **reduced mini-repos** under
`tests/fixtures/` seeded from VR1–VR3. Full-repo smoke runs against VR1–VR3 are
acceptance gates for each release (not every unit test).

---

## 1. Release map

Releases are **functional batches**: each must be demable, testable, and
regression-safe before the next starts (unless marked parallel).

| Release | Name | Capability delivered | ADR phases | Gate |
|---------|------|----------------------|------------|------|
| **R0** | Foundations & spikes | Repo layout, Core Engine shell, resolved ambiguities | Pre-1 | Spikes closed; package imports; purity harness exists |
| **R1** | Walking skeleton | Discover → Prompt Graph → Inventory → JSON → CLI (no rules) | 1 | Inventory correct on VR1–VR3; determinism/golden/purity green |
| **R2** | First findings | Findings model + ORDERING (`ORDER001`) + human report | 2 | `ORDER001` on VR3 fixture; VR1 still empty of actionable findings |
| **R3** | Volatility & duplication | VOL + DUP packs (+ edges) | 3–4 | VR3 volatility/dup findings; VR2 references-vs-embeds correct |
| **R4** | Activation, style, ownership, contradiction | Remaining core rule packs | 5–8 | VR2 ACT findings; VR3 STYLE; ownership/contradiction coverage |
| **R5** | Recommendation graph | Dependency graph + roadmap (not priority-only) | 9 | Roadmap topological; cycles reported; ownership-filtered recs |
| **R6** | Audit lifecycle | Baseline save/load + audit diff + CI-ready JSON | 1 (extend) + 14 | Diff buckets correct; fixture baseline empty-diff |
| **R7** | Safe patch | Preview → Validate → Apply | 10–12 | Invariant held; VR3 ORDER001 preview/apply smoke |
| **R8** | Skill & public v1 | SKILL.md, docs, CI, release packaging | DoD §15 | Definition of Done checklist complete |

**Note on R6.** Baseline/diff *scaffolding* lands in R1 (empty findings). Full
lifecycle value (non-trivial diffs) is gated in R6 after packs exist.

---

## 2. Epic catalogue

| Epic | Title | Primary releases | Outcome |
|------|-------|------------------|---------|
| **E0** | Spikes & ambiguity resolution | R0 | Open questions closed or deferred with recorded decisions |
| **E1** | Core Engine foundation | R0–R1 | Package, ports, config, IDs, canon JSON, purity harness |
| **E2** | Discovery & adapters | R1 | Source adapters + inventory |
| **E3** | Prompt Graph | R1 | Immutable segments + edges + builder |
| **E4** | Findings & reporting | R2 | Finding schema, normalize, human + machine reports |
| **E5** | Rule pack: ORDERING | R2 | First rule end-to-end |
| **E6** | Rule pack: VOLATILITY | R3 | Volatility detection + references-vs-embeds |
| **E7** | Rule pack: DUPLICATION | R3 | Duplicate detection + `duplicates` edges |
| **E8** | Rule pack: ACTIVATION | R4 | Dormant / invalid metadata rules |
| **E9** | Rule pack: STYLE | R4 | Worklog / hygiene rules |
| **E10** | Rule pack: OWNERSHIP | R4 | Ownership-boundary findings |
| **E11** | Rule pack: CONTRADICTION | R4 | Conflicting directives + edges |
| **E12** | Recommendation dependency graph | R5 | Recs + RecEdges + roadmap |
| **E13** | Audit lifecycle & baselines | R1 scaffold + R6 | Baseline + diff + ratchet-ready |
| **E14** | Patch preview | R7 | Mechanical single-finding diffs |
| **E15** | Patch validation | R7 | Re-audit invariant |
| **E16** | Patch apply | R7 | Branch + commit + rollback |
| **E17** | Remaining discovery adapters | R1 partial + R4/R8 | Full RFC §5.3 catalogue |
| **E18** | Skill packaging, docs, CI, release | R8 | Public v1 |

---

## 3. Stories by epic

Story IDs: `E{n}-S{m}`. Priority within an epic is story order unless noted.
Acceptance criteria use **Given / When / Then**. Spikes are marked **SPIKE**.

### E0 — Spikes & ambiguity resolution

#### E0-S1 — SPIKE: Confirm Python packaging for skill distribution
**Goal.** Validate ADR A1/D1–D3 against `npx skills` install path.  
**Acceptance.**
- Document: recommended layout under `prompt-structure-auditor/scripts/psa/` works with `npx skills add …`.
- Record go/no-go for Python vs TypeScript fallback.
- **Placeholder:** `[SPIKE-RESULT: packaging]` — fill before R1 merge.

#### E0-S2 — SPIKE: Config file convention (`psa.toml` vs pyproject)
**Goal.** Close ADR A5.  
**Acceptance.**
- Choose one primary config location; document override flags.
- Spec config keys for adapters on/off, packs on/off, include/exclude globs.
- **Placeholder:** `[SPIKE-RESULT: config-format]`.

#### E0-S3 — SPIKE: Heading-anchor extraction for stable IDs
**Goal.** Close ADR A3 for markdown / `.mdc`.  
**Acceptance.**
- Algorithm for heading path anchors on sample VR3 `AGENTS.md` and VR2 `.mdc`.
- Fallback to excerpt-hash documented.
- **Placeholder:** `[SPIKE-RESULT: id-anchors]`.

#### E0-S4 — SPIKE: Cursor rule activation semantics
**Goal.** Ground ACT rules in documented Cursor behaviour (alwaysApply / description / globs).  
**Acceptance.**
- Written truth table: when a rule is always / auto / never selected.
- Mark any unverifiable claim as inference.
- **Placeholder:** `[SPIKE-RESULT: cursor-activation]`.

#### E0-S5 — SPIKE: Fixture reduction from VR1–VR3
**Goal.** Define mini-repos that preserve dry-run signal without full BMAD/research trees.  
**Acceptance.**
- Fixture matrix: which files from each VR; what expected inventory rows; which findings expected per release.
- Exclude `research/**` as data (VR1); exclude `.claude/skills/bmad-*` as tool instruction bulk for default scan (VR2) — confirm via config.
- **Placeholder:** `[SPIKE-RESULT: fixture-matrix]`.

#### E0-S6 — SPIKE: Git worktree strategy for patch validate/apply (Windows)
**Goal.** Close ADR D12 feasibility on Windows + OneDrive paths (VR3).  
**Acceptance.**
- Chosen approach (git worktree vs tempfile copy); documented limitations for VR3.
- **Placeholder:** `[SPIKE-RESULT: patch-scratch]`.

---

### E1 — Core Engine foundation

#### E1-S1 — Package skeleton & CLI entry
**Acceptance.**
- `python -m psa --help` lists `audit`, `inventory` (stubs OK).
- Package lives under skill `scripts/` per `[SPIKE-RESULT: packaging]`.
- No network/clock imports in `psa.core`.

#### E1-S2 — `RepoFS` read-only port + in-memory test FS
**Acceptance.**
- Core stages accept `RepoFS` only.
- In-memory FS used in unit tests; no direct `pathlib` write in core.

#### E1-S3 — Config loader & config hash
**Acceptance.**
- Loads `[SPIKE-RESULT: config-format]`.
- Same config → same `config_hash` in run metadata.
- Unknown rule IDs warn (when rules exist later).

#### E1-S4 — Stable ID & canonical JSON utilities
**Acceptance.**
- `canon.dumps` byte-stable; golden unit test.
- Segment/finding ID helpers use `[SPIKE-RESULT: id-anchors]`.

#### E1-S5 — Determinism & purity harness
**Acceptance.**
- Harness fails if core touches socket/time/random/datetime.now.
- Double-run identity assertion helper ready for R1 fixtures.

#### E1-S6 — Empty `Audit` pipeline shell
**Acceptance.**
- `analyze()` returns Audit with empty findings, empty rec-graph, populated meta + inventory stub.
- Tool version injected (not read from env at call time).

---

### E2 — Discovery & adapters

#### E2-S1 — SourceAdapter protocol + registry
**Acceptance.**
- Adapters additive; stable adapter order documented.
- Subtypes: `instruction | config | data` (A2).

#### E2-S2 — Adapter: Claude instructions
**Acceptance.**
- Discovers `CLAUDE.md` / `CLAUDE.local.md` when present.
- **VR1:** no CLAUDE.md → adapter reports absent in inventory (not an error).

#### E2-S3 — Adapter: AGENTS.md
**Acceptance.**
- **VR3:** discovers root `AGENTS.md` as `instruction`, ownership `user`.
- Nested AGENTS.md if present (document behaviour).

#### E2-S4 — Adapter: Cursor rules
**Acceptance.**
- **VR2:** discovers `.cursor/rules/*.mdc` (architecture, bmad-builder, implementation).
- Captures frontmatter fields raw for later ACT rules.
- Misplaced `.cursor/rules/.cursor/permissions.json` listed as `config` or out-of-scope note (not as instruction body).

#### E2-S5 — Adapter: tool/config noise (Serena, OpenCode, Claude settings)
**Acceptance.**
- **VR1/VR2:** `.serena/*`, `.opencode/opencode.json`, `.claude/settings.local.json` typed `config`.
- Not audited as instruction content.

#### E2-S6 — Adapter: installed skills / agents dirs (tool-owned)
**Acceptance.**
- **VR1:** `.agents/skills/cache-audit/**` typed tool / not primary instruction inventory (or listed under tool with ownership `tool`).
- **VR2:** `.claude/skills/bmad-*` ownership `tool`; default config excludes from instruction audit volume or lists under tool surface only — per `[SPIKE-RESULT: fixture-matrix]`.

#### E2-S7 — Data exclusion: research & captured contexts
**Acceptance.**
- **VR1:** `research/**/claude-stdout.json` and `claude_dot_json` typed `data` / out of scope.
- Inventory notes out-of-scope data; no findings from them.

---

### E3 — Prompt Graph

#### E3-S1 — Frozen Segment / Edge / PromptModel types
**Acceptance.**
- Frozen dataclasses; MappingProxyType adjacency.
- No mutators; rules cannot import edge builders.

#### E3-S2 — Model builder: segments from instruction sources
**Acceptance.**
- **VR3:** `AGENTS.md` produces ordered segments with provenance + anchors.
- Segment IDs stable across two builds.

#### E3-S3 — Classifier: stability & content_kind & volatility_signals
**Acceptance.**
- Signal-based classification with evidence spans.
- **VR2:** rules that *reference* `_bmad-output/...` are not auto-classified `volatile` solely due to the reference (foundation for VOL002).

#### E3-S4 — Edge builder v1: `precedes`, `references`, `governs`
**Acceptance.**
- Within-source `precedes` edges deterministic.
- Cross-source `precedes` marked `observability: inference` if emitted at all.
- `governs` links frontmatter → body for Cursor rules where applicable.

#### E3-S5 — Deferred edges scaffolding
**Acceptance.**
- `duplicates` / `contradicts` hooks exist but unused until E7/E11.
- `depends_on` / `derived_from` deferred (A4) — no silent fabrication.

---

### E4 — Findings & reporting

#### E4-S1 — Finding type (priority ⊥ verification)
**Acceptance.**
- Required: `priority`, `verification`, `observability`, `ownership`, `evidence`, etc.
- No score / hit-rate / cost fields in schema.

#### E4-S2 — Normalize findings (stable IDs, order)
**Acceptance.**
- Deterministic sort; reproducible IDs per §ADR 7.2.

#### E4-S3 — Prompt Surface Inventory renderer
**Acceptance.**
- Present + absent adapters shown before findings.
- **VR1:** inventory shows missing CLAUDE/AGENTS/Cursor rules; config/data noted.
- **VR2:** Cursor rules ✓; Copilot ✗ (unless present).
- **VR3:** AGENTS ✓; Cursor ✗.

#### E4-S4 — Machine JSON report
**Acceptance.**
- Schema versioned; golden byte-equal on fixtures.
- Empty findings valid for R1.

#### E4-S5 — Human executive summary + detailed findings
**Acceptance.**
- Honesty note present; no fabricated metrics.
- Priority and verification reported as separate axes.

#### E4-S6 — CLI: `psa audit` / `psa inventory`
**Acceptance.**
- Runs on VR1–VR3 paths; exits 0 on success.
- `--format text|json`, `--out` supported.

---

### E5 — Rule pack: ORDERING

#### E5-S1 — RuleRegistry + rule protocol
**Acceptance.**
- Rules independent; ordered registry; pack enable/disable.

#### E5-S2 — `ORDER001` Early volatility
**Acceptance.**
- **VR3 fixture:** finding for "Current Focus" (or equivalent) before stable CSV/spec content.
- Evidence cites line/anchor ranges; `verification: confirmed`; `ownership: user`; `patchable: true` candidate.
- **VR1:** no ORDER001.
- **VR2:** no false ORDER001 solely from referencing volatile planning paths.

#### E5-S3 — `ORDER002` Interleaved ordering (optional in R2 if time; else R3)
**Acceptance.**
- Detects stable/volatile interleaving within a source.
- Cross-source claims labelled inference / `requires-verification`.

#### E5-S4 — Golden update for ORDER findings
**Acceptance.**
- Fixture golden JSON/report updated; determinism double-run green.

---

### E6 — Rule pack: VOLATILITY

#### E6-S1 — `VOL001` Volatility leakage (mixed segments)
**Acceptance.**
- Flags embedded volatile spans in otherwise stable sources with evidence.

#### E6-S2 — `VOL002` References vs embeds
**Acceptance.**
- **VR2:** stable rules referencing `_bmad-output` / current story **do not** fire VOL001/ORDER001 incorrectly.
- Explicit embed of live sprint/date **does** fire.

#### E6-S3 — VR3 volatility signals on worklog sections
**Acceptance.**
- Aligns with dry-run STYLE/CACHE themes without fabricating cache scores.

---

### E7 — Rule pack: DUPLICATION

#### E7-S1 — Build `duplicates` edges in model.relate
**Acceptance.**
- Deterministic pairing; evidence on both sides.

#### E7-S2 — `DUP001` Duplicated standard/instruction
**Acceptance.**
- **VR2:** architecture-freeze restated across rules → finding(s).
- **VR2:** "one story at a time" restated → finding.
- **VR3:** TrueLayer setup steps restated → finding.

#### E7-S3 — Golden + independence test
**Acceptance.**
- DUP rules produce same findings with ORDER/VOL disabled (independence).

---

### E8 — Rule pack: ACTIVATION

#### E8-S1 — `ACT001` Dormant rule
**Acceptance.**
- Per `[SPIKE-RESULT: cursor-activation]`.
- **VR2:** `bmad-builder.mdc` and `implementation.mdc` with `alwaysApply: false` and no description/globs → High value · Confirmed · user.
- **VR2:** `architecture.mdc` missing frontmatter → finding or sibling ACT finding.

#### E8-S2 — `ACT002` Missing/invalid activation / skill metadata
**Acceptance.**
- Malformed frontmatter detected with evidence.
- Invalid skill frontmatter cases covered by fixture (may be synthetic).

#### E8-S3 — Misplaced permissions path (ARCH or ACT — pick one pack)
**Acceptance.**
- **VR2:** `.cursor/rules/.cursor/permissions.json` Low value / Informational finding with recommendation to relocate.
- **Placeholder pack assignment:** `[DECISION: permissions-finding-pack]` default ARCHITECTURE if ARCH pack stories exist; else ACT Informational.

---

### E9 — Rule pack: STYLE

#### E9-S1 — `STYLE001` Instruction file used as worklog
**Acceptance.**
- **VR3:** `AGENTS.md` dominated by decisions/debugging narrative → High value finding.
- Recommendation: split durable vs volatile without semantic rewrite.

#### E9-S2 — Additional STYLE hygiene (as needed)
**Acceptance.**
- Document which STYLE### ship in v1; defer rest.

---

### E10 — Rule pack: OWNERSHIP

#### E10-S1 — `OWN001` Ownership leakage
**Acceptance.**
- Detects user sources restating tool/provider-owned content where observable.
- Provider claims → `requires-verification` where needed.

#### E10-S2 — Tool-owned BMAD surface informational
**Acceptance.**
- **VR2:** large `.claude/skills/bmad-*` surfaced as Informational · ownership tool (not "fix the skill files").

---

### E11 — Rule pack: CONTRADICTION

#### E11-S1 — Build `contradicts` edges
**Acceptance.**
- Conservative matching; evidence required; prefer high precision.

#### E11-S2 — `CONTRA001` Conflicting instruction
**Acceptance.**
- Synthetic fixture mandatory (VR2/VR3 may lack clear contradiction).
- **Placeholder:** `[SPIKE-RESULT: contradiction-fixtures]` if auto-detection threshold unclear.

#### E11-S3 — Independence & golden
**Acceptance.**
- Pack toggleable; golden updated.

---

### E12 — Recommendation dependency graph

#### E12-S1 — Recommendation builder (ownership filter)
**Acceptance.**
- User → actionable; tool → config suggestion; provider/unknown → note / not patchable.

#### E12-S2 — RecEdge derivation from Prompt Model edges
**Acceptance.**
- Example: DUP before ORDER (`enables`); ACT before ORDER on same rule (`enables`).
- Roadmap **not** sorted by priority alone.

#### E12-S3 — Cycle detection
**Acceptance.**
- Synthetic cycle fixture; cycles reported; acyclic portion still emitted (A7).

#### E12-S4 — Roadmap in human + machine output
**Acceptance.**
- Phases reflect topological order; reasons on edges visible.

---

### E13 — Audit lifecycle & baselines

#### E13-S1 — Baseline save/load (R1 scaffold)
**Acceptance.**
- `psa baseline save`; default path per A6 / `[SPIKE-RESULT: config-format]` if needed.
- Empty findings baseline round-trips.

#### E13-S2 — Audit diff (resolved / introduced / unchanged)
**Acceptance.**
- Fixture: mutate golden → introduce finding; diff shows Introduced.
- Fix → Resolved; identical → Unchanged only.

#### E13-S3 — Reprioritised sub-list
**Acceptance.**
- Same ID, changed priority band reported as countable fact.

#### E13-S4 — CLI `psa diff` + honesty (no composite score)
**Acceptance.**
- Output buckets only; no quality score.

#### E13-S5 — CI gate policy stubs
**Acceptance.**
- Documented policies (no new findings / no High-value regressions / ratchet).
- Optional exit codes for CI — **Placeholder:** `[DECISION: ci-exit-codes]`.

---

### E14 — Patch preview

#### E14-S1 — Patch model (mechanical transforms only)
**Acceptance.**
- Move block / dedupe templates; never semantic rewrite.

#### E14-S2 — Preview ORDER001 on VR3 fixture
**Acceptance.**
- Unified diff; writes nothing; finding must be `patchable` + `user`.

#### E14-S3 — Preview DUP consolidation (where safe)
**Acceptance.**
- Mechanical only; abort preview generation if unsafe → not patchable.

#### E14-S4 — CLI `psa patch preview`
**Acceptance.**
- Requires prior audit context or re-audits read-only; no apply.

---

### E15 — Patch validation

#### E15-S1 — Scratch tree + re-`analyze`
**Acceptance.**
- Uses `[SPIKE-RESULT: patch-scratch]`.
- Pure analyze on scratch; compare to current audit.

#### E15-S2 — Invariant: must not worsen audit
**Acceptance.**
- Deliberately bad patch fixture → validate fails; lists introduced/worsened findings.
- Good ORDER001 move → validate passes.

#### E15-S3 — CLI `psa patch validate`
**Acceptance.**
- Non-zero exit on failure; no writes.

---

### E16 — Patch apply

#### E16-S1 — Apply only after validate
**Acceptance.**
- Shortcut blocked; validate failure refuses apply.

#### E16-S2 — Branch + one commit + rollback message
**Acceptance.**
- Commit message includes `rule_id` + finding `id`.
- Apply summary states rollback steps.

#### E16-S3 — Post-apply re-audit smoke
**Acceptance.**
- Target finding resolved on branch; determinism still holds.

#### E16-S4 — Windows / VR3 path smoke
**Acceptance.**
- Documented result of apply on OneDrive path or skip with explicit limitation from spike.

---

### E17 — Remaining discovery adapters

#### E17-S1 — Copilot instructions adapter
**Acceptance.**
- Absent on VR1–VR3 → ✗ in inventory; present in fixture → discovered.

#### E17-S2 — OpenCode instruction files (beyond config JSON)
**Acceptance.**
- **Placeholder:** `[SPIKE-RESULT: opencode-instruction-paths]` — what counts as instruction vs config.

#### E17-S3 — Generic PROMPT.md / prompts/**
**Acceptance.**
- Fixture-based; configurable globs.

#### E17-S4 — Prompt templates + runtime builders (static)
**Acceptance.**
- Structural only; unknown runtime → inference / unknown.
- **Placeholder:** `[SPIKE-RESULT: builder-extraction-depth]` (RFC OQ).

#### E17-S5 — Memory / MCP adapters
**Acceptance.**
- Conservative discovery; ownership defaults documented.

---

### E18 — Skill packaging, docs, CI, release

#### E18-S1 — Author `SKILL.md`
**Acceptance.**
- Frontmatter name/description; progressive disclosure to references; recommend-only default; disable-model-invocation as appropriate.
- Follows repo README authoring guidelines.

#### E18-S2 — User docs (README section, rule catalogue, config reference)
**Acceptance.**
- Links RFC/ADR; honesty principles visible.

#### E18-S3 — CI workflow
**Acceptance.**
- Unit + golden + determinism + purity on PR.
- Optional: audit gate on this repo’s own prompt surface.

#### E18-S4 — Reproduce RFC illustrative examples
**Acceptance.**
- Synthetic fixtures match RFC §8/§9/§14 shapes (not fabricated metrics).

#### E18-S5 — Validation repos full smoke matrix
**Acceptance.**
- Documented expected inventory + finding sets for VR1–VR3 at v1 (terminology-updated from dry-run).
- Sign-off checklist signed.

#### E18-S6 — Public release prep
**Acceptance.**
- Versioned; installable via `npx skills`; ADR DoD §15 checklist complete.

---

## 4. Cross-cutting non-functional stories

These attach to every release that ships code:

| Story | Title | Applies |
|-------|-------|---------|
| **NF-S1** | Unit tests for new modules | Every epic shipping code |
| **NF-S2** | Golden / snapshot update + review | Every release changing output |
| **NF-S3** | Determinism double-run on fixtures | R1+ |
| **NF-S4** | Purity harness green | R0+ |
| **NF-S5** | No fabricated metrics in any renderer | R1+ (lint/review checklist) |
| **NF-S6** | Rule independence tests when ≥2 packs | R3+ |

---

## 5. Spike / decision placeholder register

| ID | Blocks | Owner | Status |
|----|--------|-------|--------|
| `[SPIKE-RESULT: packaging]` | E1-S1, R1 | — | Open |
| `[SPIKE-RESULT: config-format]` | E1-S3, E13 | — | Open |
| `[SPIKE-RESULT: id-anchors]` | E1-S4, E3 | — | Open |
| `[SPIKE-RESULT: cursor-activation]` | E8 | — | Open |
| `[SPIKE-RESULT: fixture-matrix]` | E2, golden, all rule ACs | — | Open |
| `[SPIKE-RESULT: patch-scratch]` | E15–E16 | — | Open |
| `[SPIKE-RESULT: opencode-instruction-paths]` | E17-S2 | — | Open |
| `[SPIKE-RESULT: builder-extraction-depth]` | E17-S4 | — | Open |
| `[SPIKE-RESULT: contradiction-fixtures]` | E11 | — | Open |
| `[DECISION: permissions-finding-pack]` | E8-S3 | — | Open |
| `[DECISION: ci-exit-codes]` | E13-S5 | — | Open |

---

## 6. Release ↔ story checklist (summary)

| Release | Must-complete stories (minimum) |
|---------|----------------------------------|
| **R0** | E0-S1…S6 (spikes to draft results); E1-S1…S5 |
| **R1** | E1-S6; E2-S1…S7; E3-S1…S5; E4-S3,S4,S6; E13-S1 (scaffold); NF-S1–S5 |
| **R2** | E4-S1,S2,S5; E5-S1…S4; NF updates |
| **R3** | E6-*; E7-*; NF-S6 |
| **R4** | E8-*; E9-*; E10-*; E11-*; E17 as available |
| **R5** | E12-* |
| **R6** | E13-S2…S5 |
| **R7** | E14-*; E15-*; E16-* |
| **R8** | E17 remainder; E18-*; ADR §15 DoD |

---

## 7. Traceability

| DoD item (ADR §15) | Release |
|--------------------|---------|
| Core rule packs | R2–R4 |
| Discovery adapters (full catalogue) | R1 + R4/R8 (E17) |
| Prompt Graph | R1 |
| Recommendation Graph | R5 |
| Audit lifecycle / baseline / diff | R1 scaffold + R6 |
| Patch Preview / Validation / Apply | R7 |
| RFC examples reproduced | R8 |
| Validation repos pass | Each release smoke + R8 sign-off |
| Documentation / SKILL.md / CI / public release | R8 |

---

## 8. Out of scope (explicit)

- Predicting cache hit rate, cost, latency, token savings
- Semantic prompt rewriting
- Runtime / live prompt transformation
- Redesigning RFC architecture when implementation is hard (document assumption instead)
