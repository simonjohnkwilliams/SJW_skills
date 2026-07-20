# RFC 0001 — Validation Dry-Run

> **Revision Note (RFC v0.2.0)**
>
> This validation was produced against **RFC v0.1.0** terminology. The concepts
> remain valid; only the naming has since evolved:
>
> - `CACHE` → split into `ORDERING` + `VOLATILITY`
> - `Blocked` → `Requires Verification` (now an orthogonal **status**, not a
>   priority band — see RFC §10)
> - Activation findings (e.g. `ARCH-ACT`) → the dedicated `ACTIVATION` rule pack
> - Example rule IDs such as `CACHE001` → `ORDER001` / `VOL001`
>
> The examples below are **intentionally preserved** as a historical record of the
> design process that produced those changes. They are not updated in place.

| Field | Value |
|-------|-------|
| **Companion to** | [RFC 0001 — Prompt Structure Auditor](./0001-prompt-structure-auditor.md) |
| **Status** | Informational — manual validation |
| **Method** | The RFC pipeline (Discovery → Prompt Model → Rules → Findings → Report) applied *by hand* to three real repositories, before any implementation exists |
| **Purpose** | Test whether the specification holds up on real input, and feed concrete refinements back into the design |

> These audits were produced manually to exercise the specified behaviour. They
> are **not** the output of an implemented tool. Every finding is labelled
> *observable* or *inference* per the RFC's honesty constraint. No fabricated
> metric (cache score, hit-rate, cost) appears anywhere — by design.

## Test set

| Repo | Character | Why chosen |
|------|-----------|------------|
| `ai-context-benchmark` | No authored prompt surface | Negative test — must not fabricate findings |
| `lateTrainQueries` | Cursor rules + large installed skill surface | Activation metadata, duplication, ownership boundaries |
| `demo` | Single `AGENTS.md` used as a worklog | Ordering / volatility / duplication (the richest CACHE case) |

---

## Audit 1 — `ai-context-benchmark`

### Executive Summary

```
Scope
  Discovered sources: 0 instruction sources, 3 tool-config sources
    - .claude/settings.local.json      (tool config: permissions only)
    - .serena/project.yml              (tool config)
    - .agents/skills/cache-audit/**    (installed skill — tool-controlled)
  Out of scope (data, not prompt construction):
    - research/**/claude-stdout.json   (benchmark run outputs)
    - research/case_d/snapshots/*/claude_dot_json  (captured runtime contexts)
  docs/** : 60+ design docs (ADRs, specs) — not wired as agent-instruction sources

Findings by priority
  High value: 0   Medium: 0   Low: 0   Blocked: 1   Informational: 2

Honesty note
  No user-authored persistent prompt-instruction file (CLAUDE.md / AGENTS.md /
  Cursor rules) was found. This audit reports the *absence* of a prompt surface;
  it does not invent findings.
```

### Detailed Findings

```
[INFO-1] Informational · observable · owner: user
No conventional agent-instruction source present
  Evidence: no CLAUDE.md/AGENTS.md at root; .cursor/rules absent;
            research/case_d/snapshots/cbm_native_batch_pre/CLAUDE.md.absent
  Why it matters: the agent runs on provider defaults + Serena. That is a valid
    choice; there is simply no authored prompt structure to audit here.
  Recommendation: none required. If persistent conventions are desired, introduce
    a single stable instruction file.

[INFO-2] Informational · observable · owner: user
Session-state document exists under docs/
  Evidence: docs/SESSION-STATE.md, docs/STORY-0-FINDINGS.md
  Why it matters: these are volatile working documents. They are fine as docs.
  Recommendation: keep them out of any always-injected context if you later add one.

[BLOCKED-1] Blocked · inference · owner: provider/tool
Effect of research artifacts / captured contexts on live prompt assembly
  Evidence: research/**/claude_dot_json (49–50 KB captured contexts)
  Why blocked: whether/how these are assembled into a live prompt is not
    observable from the repo. Not asserted.
```

This is the **honest empty-result case** — the most important negative test.

---

## Audit 2 — `lateTrainQueries`

### Executive Summary

```
Scope
  Instruction sources (user-controlled):
    - .cursor/rules/architecture.mdc      (168 B)
    - .cursor/rules/bmad-builder.mdc      (597 B)
    - .cursor/rules/implementation.mdc    (313 B)
  Tool config: .opencode/opencode.json, .serena/project.yml
  Tool-controlled installed skills: .claude/skills/bmad-* (~150 files)
  Referenced volatile state: _bmad-output/planning-artifacts/**

Findings by priority
  High value: 1   Medium: 2   Low: 1   Blocked: 1   Informational: 1
```

### Detailed Findings

```
[ARCH-ACT] High value · observable · confidence: high · owner: user
Cursor rules cannot be auto-selected: missing activation metadata
  Evidence:
    - architecture.mdc:1     no YAML frontmatter at all
    - bmad-builder.mdc:1-3    alwaysApply: false, no `description`, no `globs`
    - implementation.mdc:1-3  alwaysApply: false, no `description`, no `globs`
  Why it matters: a rule with alwaysApply:false and neither description nor globs
    has no trigger the agent can match, so it is effectively dormant. The frontmatter-
    less rule's scope is undefined. The user wrote guardrails that likely never load.
  Recommendation: add a `description` (and/or `globs`) to each rule, or set
    alwaysApply:true for the ones meant to be constant (e.g. architecture freeze).
  Patchable: yes (mechanical frontmatter edit)

[DUP-ARCH] Medium value · observable · owner: user
Architecture-freeze guardrail duplicated across rules
  Evidence:
    - architecture.mdc:1  "Architecture is frozen."
    - bmad-builder.mdc    "Do not redesign the architecture."
    - implementation.mdc  "Anything requiring architectural review."
  Recommendation: state the freeze once in an always-applied rule; reference it elsewhere.

[DUP-STORY] Medium value · observable · owner: user
"One story at a time" restated in two rules
  Evidence: bmad-builder.mdc "Implement only the requested story";
            implementation.mdc "Only implement one story at a time."
  Recommendation: consolidate to a single owner rule.

[ARCH-LOC] Low value · observable · owner: user
Misplaced permissions file nested inside rules directory
  Evidence: .cursor/rules/.cursor/permissions.json
  Why it matters: permissions normally live at .cursor/permissions.json; nested
    under rules/ it is likely ineffective/unintended.
  Recommendation: move to .cursor/ (verify against your tool's expected path).

[INFO-BMAD] Informational · observable · owner: tool
Large installed skill surface (.claude/skills/bmad-*)
  Evidence: ~150 files, hundreds of KB of tool-controlled instructions.
  Why it matters: this is installed tooling, not your prompt construction; it is
    out of your direct editing scope. Noted for ownership clarity.

[BLOCKED-ORDER] Blocked · inference · owner: provider/tool
Assembly order of rules + installed skills + defaults
  Why blocked: the true concatenation order across these sources is not observable.
    No ordering/cache claim is made.
```

**Correctness nuance (good test).** The rules *point to* volatile state
(`_bmad-output/.../current story`, sprint status) but do **not** embed volatile
values. The classifier correctly treats them as **stable instructions that
reference volatile data** — not an early-volatility violation.

---

## Audit 3 — `demo`

### Executive Summary

```
Scope
  Primary instruction source: AGENTS.md (5.8 KB, user-controlled)
  Other root docs: 13 markdown files (README, STATUS, GETTING_STARTED,
    QUICKSTART, START_HERE, PROJECT_SUMMARY, IMPLEMENTATION_CHECKLIST, HELP,
    DOCUMENTATION_INDEX, FIXED_AND_RUNNING, README_SIMPLIFIED,
    SPENDING_DASHBOARD_README, SPENDING_QUICKSTART)

Findings by priority
  High value: 2   Medium: 1   Low: 0   Blocked: 1   Informational: 1
```

### Detailed Findings

```
[CACHE001] High value · observable · confidence: high · owner: user
Volatile "Current Focus" placed first in AGENTS.md
  Evidence: AGENTS.md:1-3  ("records setup steps and decisions...")
            AGENTS.md:5-7  ("## Current Focus: CSV Import")
            AGENTS.md:9-14 (stable CSV format spec, appears *after*)
  Why it matters: content before the first change is what a cache can reuse.
    A "current focus" line that changes over time sits ahead of the stable spec,
    so the stable material is behind a frequent change point.
  Recommendation: move "Current Focus" below the stable spec; group dynamic status
    together near the end.
  Patchable: yes (block move)

[STYLE-LOG] High value · observable · owner: user
AGENTS.md is used as a running worklog, not durable guidance
  Evidence: AGENTS.md:18 "On Hold – Can Return"; :43 "Decision: Try Live
    Environment"; :70 "Debugging invalid client_id"; :35 "Known Issue".
  Why it matters: session narrative and debugging history are volatile and erode
    the stable prefix and maintainability of the instruction file.
  Recommendation: split durable guidance (CSV format, conventions) from the
    volatile worklog (move the log to NOTES/CHANGELOG or the end of the file).

[DUP001] Medium value · observable · owner: user
TrueLayer setup steps repeated
  Evidence: AGENTS.md:26-33 "Console Configuration"; :49-55 "Config changes for
    Live"; :57-62 "Live Console checklist"; :64-66 "Config for Live".
    Redirect-URI / client-id / client-secret steps restated ~4 times.
  Recommendation: consolidate into one setup section; link rather than repeat.

[INFO-SPRAWL] Informational · observable · owner: user
Overlapping onboarding docs at repo root
  Evidence: README, README_SIMPLIFIED, GETTING_STARTED, QUICKSTART, START_HERE,
    SPENDING_QUICKSTART (6 overlapping entry points).
  Note: whether these are injected as agent context is not observable; flagged as
    documentation sprawl, not asserted as prompt content.

[BLOCKED-SECRETS] Blocked/Informational · observable(fact)+inference · owner: user
Instructions describe storing tokens/secrets in application.yaml
  Evidence: AGENTS.md:86-96 curl with client_secret / access-token placeholders;
    :95 "truelayer.access-token: YOUR_ACCESS_TOKEN".
  Observable fact: only placeholders are present — no real secret is committed.
  Why limited: this is guidance, not a leak; not overclaimed.
```

### Implementation Roadmap (demo)

```
Phase 1 — High value, independent
  - STYLE-LOG  Split durable spec from worklog
  - CACHE001   Move "Current Focus" and dynamic status to the end
Phase 2 — Medium
  - DUP001     Consolidate TrueLayer setup
Phase 3 — Informational
  - INFO-SPRAWL Consider consolidating onboarding docs
```

---

## What this dry-run revealed about the RFC

Refinements to fold back into `0001-prompt-structure-auditor.md`:

1. **Discovery needs a `source subtype: config | instruction | data`.**
   `settings.local.json`, `opencode.json`, and `.serena/project.yml` are *tool
   config*, not instruction content. Without this distinction a naive
   implementation would raise false positives on JSON config. (Refines §5.)

2. **A missing rule category: rule-activation metadata.** The strongest,
   highest-value finding (repo 2) was Cursor `.mdc` rules with `alwaysApply:false`
   and no `description`/`globs` — effectively dormant. This observable class is
   not in the v1 rule list; add an **ACTIVATION** pack (or fold into
   ARCHITECTURE). (Refines §7.3.)

3. **The classifier must separate "references volatile data" from "embeds
   volatile data."** Repo 2's rules point at `_bmad-output/.../current story` yet
   are themselves stable. Without this nuance the tool produces false
   early-volatility hits. (Refines §6.4.)

4. **Ownership boundaries and `Blocked` worked exactly as intended.** The BMAD
   installed-skill surface (tool-controlled) and cross-source assembly order
   (provider-controlled) were correctly labelled inference/Blocked rather than
   fabricated into a score. (Validates §10–§11.)

5. **The empty-result case (repo 1) is a first-class output state.** The tool
   must confidently say "no prompt surface to audit". Add an explicit "Not
   applicable / no actionable findings" report state. (Refines §9.)

6. **`AGENTS.md`-as-scratchpad (repo 3) is a common real anti-pattern** worth a
   dedicated STYLE rule ("instruction file used as worklog/memory"). (Refines §7.3.)

7. **Discovery scope for ambient docs must be configurable.** Repo 3's 14 root
   markdown files are only *maybe* prompt sources; treat them as in-scope only via
   config, otherwise label Informational. (Confirms §5.6.)

Notably, **no repo tempted a fabricated metric** — the honesty constraints held
under real input.
