# RFC 0001 — Prompt Structure Auditor

| Field | Value |
|-------|-------|
| **Title** | Prompt Structure Auditor (working skill name: `prompt-structure-auditor`; see §0.1 on naming) |
| **Status** | Draft — for review |
| **Version** | 0.2.0 (specification, not implementation) |
| **Supersedes** | `cache-audit` skill (v0) |
| **Audience** | Skill implementers, reviewers, open-source contributors |
| **Author role** | Senior software architect (specification only) |
| **Scope of this document** | Architecture and behaviour contract. No implementation, no code, no `SKILL.md`. |

**Revision history**

- **0.2.0** — Incorporated review feedback: audit lifecycle with baselines and
  audit diff (§14); recommendation dependency graph (§9.7); validation phase
  between patch preview and apply (§12); Prompt Model promoted to a graph with
  explicit relationships (§6.7); Prompt Surface Inventory output artifact (§9.3);
  the former `Blocked` priority band replaced by an **orthogonal `verification`
  status** (`confirmed` / `requires-verification`), separate from priority (§10);
  CACHE pack split into `ORDERING` and `VOLATILITY`, and an `ACTIVATION` and
  `OWNERSHIP` pack added (§7.3); positioning/naming discussion (§0.1).
- **0.1.0** — Initial specification.

> **Normative intent.** This RFC is written so that two independent teams
> implementing it should produce substantially the same observable behaviour.
> Where wording matters, the key words **MUST**, **MUST NOT**, **SHOULD**,
> **SHOULD NOT**, and **MAY** are used in the sense of RFC 2119. Illustrative
> examples (report layouts, sample records) are explicitly labelled
> *non-normative*; the field semantics that surround them are normative.

---

## 0. Summary

The Prompt Structure Auditor is an **Agent Skill that performs static analysis
of the prompt-construction surface of a repository**. It behaves like a linter
(ESLint) or a static-analysis platform (SonarQube), not like a benchmark. It
reads the files and configuration that shape an agent's context — instruction
files, rules, memories, prompt templates, prompt-builder code — and reports
**structural findings** about stability, maintainability, duplication, ordering,
and cache friendliness.

Its defining constraint is **technical honesty**. It reports only what it can
observe from repository contents. It never fabricates precision: no cache score,
no optimisation score, no predicted hit rate, no estimated cost saving. Anything
that depends on provider internals or runtime behaviour is either omitted or
explicitly labelled **inference**.

The analysis phase is **deterministic and side-effect free**. Modification
(patch generation and application) is a separate, explicit, opt-in mode designed
around safety: preview first, one change at a time, isolated branch, individual
commits, easy rollback.

This document replaces the earlier `cache-audit` design, which over-reached by
emitting an "Overall Cache Score (0–100)", a "Stable Prefix %", an "Estimated
Cache Friendliness", and expected outcomes such as "higher cache hit ratio" and
"lower effective inference cost". Those are inferences presented as measurements
and are removed. Prompt caching survives here as **one concern among several**
(served by the `ORDERING` and `VOLATILITY` rule packs), not the product's
identity.

An audit is not a one-off report. The auditor supports a **continuous lifecycle**
— audit → baseline → improve → re-audit → compare — so a repository's prompt
surface can be kept healthy over time and gated in CI (§14). Comparison answers
*what improved, what regressed, and what remains* using only countable facts (no
fabricated metrics).

### 0.1 Positioning and naming

The design has grown well beyond prompt caching. Its rule packs now span
`ORDERING`, `VOLATILITY`, `DUPLICATION`, `CONTRADICTION`, `ACTIVATION`,
`ARCHITECTURE`, `OWNERSHIP`, and `STYLE` (§7.3). Functionally this is a **linter
for the prompt/agent-instruction surface** — much closer to ESLint or SonarQube
than to a cache-auditing utility. Caching is simply the concern that motivated
the first packs.

This RFC therefore treats "prompt architecture linting" as the product's true
identity and keeps the architecture broad enough to support it. No naming
decision is required yet; the working directory/skill name remains
`prompt-structure-auditor`. Candidate long-term names for the maintainers to
weigh (non-normative): **Prompt Architecture Auditor**, **Prompt Architecture
Linter**, **PromptLint**. Whatever the name, the founding constraint is
unchanged: report the observable, label the inferred, and never fabricate
precision.

---

## 1. Problem Definition

### 1.1 What problem this solves

As agent-assisted development matures, repositories accumulate a growing,
uncoordinated surface of prompt-shaping artifacts: `CLAUDE.md`, `AGENTS.md`,
Cursor rules, Copilot instructions, per-directory instruction files, memory
files, MCP server instructions, and hand-rolled prompt templates or builders in
application code. These are authored by different people, at different times,
with no shared conventions and no tooling to inspect them **as a system**.

The result is a class of *structural* problems that nobody currently owns:

- **Ordering problems** — volatile content (dates, ticket numbers, "current
  task", retrieved snippets) placed ahead of stable content (architecture,
  standards, role), shortening the reusable stable prefix that prompt caches
  depend on.
- **Duplication** — the same instruction, standard, or guardrail restated across
  multiple files, causing drift and contradiction over time.
- **Volatility leakage** — dynamic values embedded inside otherwise stable
  documents.
- **Maintainability erosion** — no clear ownership boundary between what the
  *user* controls, what the *tool/agent* injects, and what the *provider* does
  invisibly.
- **Silent contradiction** — two sources giving conflicting instructions.

The Prompt Structure Auditor gives these problems a home. It answers one
question:

> **"Based on the prompt construction I can observe, what structural
> improvements could improve prompt stability, maintainability, and cache
> friendliness?"**

### 1.2 What this deliberately does NOT solve

The first version **MUST NOT**:

- predict cache hit rate;
- estimate cost savings, token savings, or latency improvements as measurements;
- rewrite prompts automatically as part of analysis;
- claim runtime improvements will occur;
- infer or describe hidden provider behaviour as fact;
- optimise prompts in real time or reorder live context.

It does **not** answer *"what cache hit rate will I achieve?"* — that question is
unanswerable from repository contents alone and belongs to future runtime
tooling (see §16).

### 1.3 Why existing tools do not address this

- **General linters (ESLint, markdownlint, etc.)** understand syntax of code and
  markup, not the *semantics of prompt assembly* — they have no concept of
  stable vs volatile content, ordering for cache reuse, or ownership boundaries.
- **SonarQube / static-analysis platforms** target source-code quality metrics,
  not natural-language instruction surfaces spread across heterogeneous files.
- **Provider dashboards** report runtime cache metrics *after the fact*, are
  provider-specific, and cannot recommend structural source changes.
- **Prompt "optimisers" and benchmark harnesses** produce numbers that depend on
  a specific model, provider, and workload; they are not deterministic, not
  reproducible across environments, and cannot be run as a pre-commit check.

The gap is a **deterministic, provider-agnostic, source-level static analyser
for the prompt surface**. This skill fills exactly that gap.

---

## 2. User Personas

| Persona | Goal | What they get from the auditor |
|---------|------|--------------------------------|
| **AI / agent engineer** | Keep agent context effective and stable | Findings on ordering, volatility, and duplication; a prioritised roadmap |
| **Platform / DevEx engineer** | Enforce prompt conventions across many repos in CI | Deterministic, machine-readable findings usable as a gate |
| **Prompt engineer** | Improve instruction quality and reduce contradictions | Duplication and contradiction findings with evidence and rationale |
| **Repository maintainer** | Keep instruction files healthy over time | An audit they can re-run; small, reviewable patches instead of rewrites |
| **Open-source contributor / rule author** | Extend coverage | A rule-pack model that lets them add rules without touching existing ones |
| **Reviewer / auditor (compliance-minded)** | Trust the output | Explicit observable-vs-inference labelling and ownership boundaries |

Non-persona (explicit): a user seeking a *guaranteed performance number*. The
tool intentionally does not serve that expectation and should say so.

---

## 3. Success Criteria

"Good" is defined behaviourally, and only in terms the tool can actually stand
behind. The auditor is successful when:

1. **Determinism.** Running the auditor twice on the same repository state
   produces identical findings (same IDs, same evidence, same ordering). No
   randomness, no time-of-day dependence, no network dependence.
2. **Evidence-backed findings.** Every finding cites concrete, locatable
   evidence (file path, and where meaningful a line range or section anchor) that
   a reader can open and verify.
3. **Honest labelling.** Every statement is classifiable as *observable* or
   *inference*; inferences are labelled as such and never presented as
   measurement. There is no fabricated score or percentage that is not directly
   countable from source.
4. **Explainability.** Every finding explains *why it matters* in plain terms,
   independent of any specific provider.
5. **Actionability.** Every finding carries a concrete recommendation and a
   clear ownership boundary (who can act on it).
6. **Safety of modification.** In its default mode the tool changes nothing. Any
   modification is opt-in, previewed, isolated, and reversible.
7. **Extensibility in practice.** A new rule can be added without editing any
   existing rule, and appears in output through the same schema.
8. **Reproducibility of recommendations.** Recommendations are framed so a user
   can *independently test* them (see §14), rather than trusting a claimed
   outcome.

Explicitly **not** success criteria: a high "cache score", a predicted hit-rate
improvement, or any number the tool cannot derive by counting observable facts.

---

## 4. Architecture

### 4.1 Pipeline

The auditor is a staged pipeline whose analysis stages are pure (deterministic,
side-effect free). Each stage has a single responsibility and a well-defined
output that becomes the next stage's input. Only the opt-in modification stage
may touch the working tree, and even then it re-runs analysis to validate itself
before writing (§12). The pipeline is embedded in a **continuous lifecycle**: an
audit can be baselined, improved against, re-audited, and compared (§14).

```
   ┌─────────────────────────── continuous lifecycle (§14) ───────────────────────────┐
   │                                                                                    │
   ▼                          (read-only, deterministic)                                │
 ┌───────────┐   ┌──────────────┐   ┌─────────────┐   ┌───────────┐   ┌────────────────┐
 │ Discovery │ → │ Prompt Model │ → │ Rule Engine │ → │ Findings  │ → │ Recommendations│
 │           │   │  (graph, §6) │   │  (packs §7) │   │   (§8)    │   │ + dep-graph §9.7│
 └───────────┘   └──────────────┘   └─────────────┘   └───────────┘   └───────┬────────┘
        │                                                                      │
        │                                                                      ▼
        │                                                             ┌──────────────────┐
        │                                                             │   Report(s) §9   │
        │                                                             │  (+ audit diff)  │
        │                                                             └──────────────────┘
        │                                                                      │
        │                        (opt-in, side-effecting)                      ▼
        │                                              ┌───────────────────────────────────┐
        └───────────────────────────────────────────  │ Patch: Preview → Validate → Apply │
                                                       │   (validation re-runs analysis)   │
                                                       └───────────────────────────────────┘
```

### 4.2 Stage responsibilities

| Stage | Responsibility | Input | Output | Side effects |
|-------|----------------|-------|--------|--------------|
| **Discovery** | Find prompt-shaping sources in the repo via an extensible set of *source adapters* | Repository tree | Ordered list of raw *sources* with provenance | Read-only |
| **Prompt Model** | Normalise sources into a provider-agnostic, ordered model of prompt *segments* with attributes and evidence | Raw sources | Prompt Model (see §6) | None |
| **Rule Engine** | Run independent rules over the Prompt Model | Prompt Model + rule config | Raw findings | None |
| **Findings** | Normalise, de-duplicate, and stabilise findings; attach IDs and ordering | Raw findings | Canonical findings set (see §8) | None |
| **Recommendations** | Derive prioritised guidance from findings; compute the **recommendation dependency graph** and a dependency-aware roadmap (see §9.7) | Findings | Recommendations + dependency graph + roadmap | None |
| **Report(s)** | Render output artifacts (human + machine), including the Prompt Surface Inventory (§9.3) and, when a baseline exists, the audit diff (§14) | Findings + recommendations (+ baseline) | Reports (see §9) | Writes report file(s) only if the user asks for file output |
| **Patch: Preview → Validate → Apply** | *Opt-in only.* Turn a chosen finding into a previewable change, **re-run analysis to validate it does not worsen the audit**, then optionally apply | A selected finding + repo | Patch preview; validation result; optionally a branch + commit | Writes to a branch only under explicit opt-in, and only after validation passes |

### 4.3 Determinism boundary

Everything up to and including **Recommendations** is a pure function of
`(repository state, tool version, rule configuration)`. It **MUST NOT** read the
clock, the network, environment entropy, or any provider API. Rendering a report
to stdout is pure; writing a report file is a benign, explicitly requested side
effect. Patch application is the only stage permitted to modify tracked files,
and only in the opt-in modification mode.

### 4.4 Why this shape

- A staged pipeline with typed hand-offs makes each stage **independently
  testable** and keeps rules ignorant of discovery details.
- Isolating side effects to the final stage preserves the guarantee that
  *analysis never mutates the repo*, which is what makes the tool safe to run in
  CI and pre-commit contexts.
- Placing the **Prompt Model** as a stable interface between discovery and rules
  is the key extensibility seam: new source types and new rules evolve
  independently as long as both speak "Prompt Model".
- Because analysis is a deterministic pure function, the same machinery serves
  three roles with no special-casing: a one-off audit, the **validation step**
  inside patch application (§12), and the **re-audit** that powers baseline
  comparison (§14).

---

## 5. Discovery Phase

### 5.1 Purpose

Discovery finds and orders the artifacts that shape agent context, and records
*how* each was found (provenance) so downstream stages can cite evidence and
assign ownership.

### 5.2 Source-adapter model

Discovery is implemented as a set of independent **source adapters**. Each
adapter answers three questions for a given repository:

1. **Match** — does this repo contain sources of my type? (path globs / file
   detection)
2. **Extract** — what raw text/segments do those sources contribute?
3. **Describe** — what provenance and default ownership applies (see §11)?

Adapters **MUST** be additive: adding one **MUST NOT** change the behaviour of
another. Discovery output is the concatenation of adapter outputs in a
**defined, stable order** (see §5.5).

### 5.3 Baseline source catalogue (v1)

The following adapters SHOULD ship in v1. Each is independent and individually
switchable.

| Adapter | Typical sources | Notes |
|---------|-----------------|-------|
| Claude instructions | `CLAUDE.md`, `CLAUDE.local.md` | Root and nested |
| Agents instructions | `AGENTS.md` | Root and nested |
| Cursor rules | `.cursor/rules/**`, legacy `.cursorrules` | Rule files with their own metadata |
| Copilot instructions | `.github/copilot-instructions.md` | GitHub Copilot |
| OpenCode instructions | OpenCode instruction files | Extensible |
| Generic project prompts | `PROMPT.md`, `prompts/**`, `docs/prompts/**` | Convention-based |
| Prompt templates | Template files (e.g. `*.prompt`, template dirs) | Text templates with placeholders |
| Runtime prompt builders | Source files that assemble prompts programmatically | See §5.4 (observed structurally, not executed) |
| Memory / persistent fragments | Agent memory files, persisted context fragments | Where present as files |
| MCP instructions | MCP server instruction/config declarations | Where declared in-repo |

The catalogue is **open**. Any source type not listed is a candidate for a
future adapter (§13), not a reason to hard-code.

### 5.4 Runtime prompt builders

Prompt builders (code that concatenates strings, reads files, and injects
variables to form a prompt) are **observed structurally, never executed**. The
adapter MAY identify:

- the ordered set of literal/text fragments a builder assembles;
- the points at which dynamic values are interpolated;
- references to external files the builder pulls in.

Anything the builder does *at runtime* that cannot be determined statically
(e.g. values fetched from a network, conditional branches whose selection is
unknown) **MUST** be treated as *inference* or marked *unknown*, never asserted.

### 5.5 Ordering and provenance

- Discovery **MUST** assign each source a deterministic position derived from a
  documented precedence (e.g. adapter order, then path sort). Ordering is central
  because several rules reason about *what comes before what*.
- Where the true runtime assembly order is **not** observable (the tool cannot
  know the exact order a given agent/provider concatenates sources), the model
  **MUST** record ordering confidence and treat cross-source ordering claims as
  *inference* (see §6.4 and §15).
- Each discovered source **MUST** carry provenance: absolute-within-repo path,
  adapter identity, and (where meaningful) byte/line ranges.

### 5.6 Configuration

Discovery SHOULD be configurable via a repo-local config: enable/disable
adapters, add include/exclude globs, and register additional source paths. Absent
config, sensible defaults apply. Configuration is part of the determinism input
(§4.3): the same repo + same config ⇒ same discovery.

---

## 6. Prompt Model

### 6.1 Purpose

The Prompt Model is the **normalised, provider-agnostic intermediate
representation** that decouples discovery from rules. Rules operate *only* on the
Prompt Model, never on raw files. This is the extensibility seam of the whole
design.

### 6.2 Structure

The Prompt Model is a **graph**, not merely an ordered list. Its **nodes** are an
ordered collection of Segments, each optionally decomposed into finer **Units**
(e.g. a document split into headed sections, or a builder split into fragments).
A Segment is the smallest thing a rule reasons about for ordering; a Unit is the
smallest thing evidence and patches point at. Its **edges** are typed
relationships between segments (§6.7).

Ordering remains a first-class property (it is what several rules and the cache
concern depend on), but it is now one relationship among several rather than the
model's only structure. Treating the model as a graph is what makes
recommendation dependencies (§9.7), duplication/contradiction pairing, and
dependency-aware patch sequencing expressible without special-casing.

### 6.3 Segment attributes

The following attributes are **normative in meaning**. Exact field names and
serialization are an implementation choice; the *semantics* below must be
preserved so that two implementations converge.

| Attribute | Meaning | Value space | Determinism |
|-----------|---------|-------------|-------------|
| `id` | Stable identifier for the segment | Deterministic from provenance + content | Required stable |
| `source` | Which discovered source it came from | Provenance reference | Observable |
| `order` | Position in the model's defined ordering | Integer / ordinal | Observable within a source; cross-source may be inference |
| `content_kind` | Nature of content | e.g. instruction, standard, role, example, retrieved-context, state, metadata | Observable (classified) |
| `stability` | How likely the content is to remain identical across sessions | `stable` \| `volatile` \| `mixed` \| `unknown` | Classified, with confidence |
| `volatility_signals` | Concrete markers suggesting change (dates, "current", ticket ids, counters, interpolation points) | List of evidence spans | Observable |
| `ownership` | Who controls this content | `user` \| `tool` \| `provider` \| `unknown` (see §11) | Classified |
| `relocatability` | Whether/where the content could be moved | e.g. `freely-movable` \| `movable-within-source` \| `fixed` \| `unknown` | Classified |
| `confidence` | Confidence in the *classification* of this segment | `high` \| `medium` \| `low` (see §6.5) | Required |
| `evidence` | Locatable proof for the above (paths, ranges, matched strings) | List | Required |

> The user's brief listed candidate attributes and invited scrutiny. Adjustments
> made deliberately: **`volatility` and `stability` are unified** into a single
> `stability` scale (with `mixed`) plus explicit `volatility_signals`, because a
> segment cannot be independently "very stable" and "very volatile" — that split
> invites contradictory values. **`confidence` is scoped to the classification**,
> not the finding (findings carry their own confidence, §8). **`content_kind`**
> is added because several rules (duplication, contradiction, retrieval
> placement) need to know *what a segment is*, not just how stable it is.

### 6.4 Stability classification

Stability is derived from **observable signals only**, using a documented,
deterministic ruleset (this replaces the old free-text example lists with a
categorised, testable classifier):

- **Stable indicators**: architecture, coding standards, style guides, project
  structure, technology stack, guardrails, team conventions, output formatting,
  role definition, testing strategy.
- **Volatile indicators**: current date/time, sprint/ticket/build/release/branch
  identifiers, "current task", session counters, retrieved documentation / RAG
  snippets / search results, conversation summaries, recently edited files,
  dynamic TODO lists, and interpolation points in templates/builders.
- **Mixed**: a stable document containing embedded volatile spans.
- **Unknown**: insufficient signal — classified explicitly as such rather than
  guessed.

The classifier **MUST** attach the matched signal(s) as evidence so a reader can
audit the decision.

### 6.5 Confidence

`confidence` is a small ordinal (`high | medium | low`). It reflects how strong
the observable signal is — e.g. an explicit `{{date}}` interpolation is
high-confidence volatile; a heading merely *named* "context" is low-confidence.
The tool **MUST NOT** convert confidence into a spurious numeric percentage.

### 6.6 What the model must NOT contain

The Prompt Model **MUST NOT** contain provider cache state, hit rates, cost
figures, hidden system prompts, or any value the tool did not observe. Fields
representing such things do not exist in v1; they are the domain of inference and
are handled (if at all) as labelled notes in findings, never as model data.

### 6.7 Relationships (edges)

Segments are connected by **typed, directed relationships**. Each edge carries
its own `evidence`, `confidence`, and `observability` (an edge may itself be
inference — e.g. a suspected cross-source ordering). Rules read edges just as
they read node attributes; they **MUST NOT** create edges (edges are built during
Prompt Model construction, keeping rules pure).

Baseline relationship types for v1 (the set is **open**, like adapters and
rules):

| Relationship | Direction | Meaning | Primary consumers |
|--------------|-----------|---------|-------------------|
| `precedes` | A → B | A appears before B in a defined ordering | ORDERING rules; cache concern |
| `references` | A → B | A points at B (e.g. architecture doc → coding standards; a rule → a planning artifact) | ARCHITECTURE, ACTIVATION, roadmap |
| `duplicates` | A ↔ B | A and B restate the same content | DUPLICATION; patch consolidation |
| `contradicts` | A ↔ B | A and B give conflicting directives | CONTRADICTION |
| `depends_on` | A → B | A's meaning/validity depends on B (e.g. runtime state → current sprint) | OWNERSHIP, roadmap sequencing |
| `derived_from` | A → B | A is generated/interpolated from B (builder fragment → variable/source) | VOLATILITY, builder analysis |
| `governs` | A → B | A's activation metadata controls whether B applies (rule frontmatter → rule body/scope) | ACTIVATION |

Why this matters:

- **Roadmap quality.** Recommendation dependencies (§9.7) are largely derived
  from edges: consolidating a `duplicates` pair before acting on a `precedes`
  issue avoids reordering the same content twice.
- **Better patches.** A move patch can consult `references`/`depends_on` edges to
  avoid separating content from what it relies on.
- **Honest ordering.** `precedes` edges that cross sources carry
  `observability: inference` and low `confidence`, keeping cross-source ordering
  claims labelled rather than asserted.

Edges **MUST NOT** encode unobservable provider behaviour as fact; an inferred
edge is labelled as such, exactly like an inferred node attribute.

---

## 7. Rule Engine

### 7.1 Rule contract

A **rule** is an independent, deterministic unit that reads the Prompt Model and
emits zero or more findings. Every rule **MUST**:

- be **independent** — depend only on the Prompt Model (and its own config),
  never on other rules or their outputs;
- be **deterministic** — same model ⇒ same findings, in a stable order;
- be **explainable** — carry a static rationale ("why this matters") that ends up
  in output;
- be **individually testable** — testable in isolation with a small Prompt Model
  fixture;
- **stay within observation** — either report observable facts, or label the
  inferential part of any finding it raises.

Rules **MUST NOT** mutate the model, perform I/O, or read the clock/network.

### 7.2 Rule identity and metadata

Each rule declares stable metadata that flows into findings:

| Field | Meaning |
|-------|---------|
| `rule_id` | Stable, namespaced identifier, e.g. `ORDER001` (see §7.4) |
| `category` | Rule pack it belongs to (see §7.3) |
| `title` | Short human name |
| `rationale` | Provider-agnostic "why it matters" |
| `default_priority` | Suggested priority band (see §10), overridable by config |
| `ownership_hint` | Typical ownership boundary of what it flags (see §11) |
| `observability` | Whether findings are inherently `observable` or `inference` |

### 7.3 Rule packs (categories)

Rules are grouped into **packs**. Packs are additive; enabling/disabling a pack
is a config action. v1 SHOULD ship:

| Pack | Purpose (examples) |
|------|--------------------|
| **ORDERING** | *Sequence* concerns: stable-before-volatile ordering, interleaving, early placement of volatile content |
| **VOLATILITY** | *Change* concerns: detecting volatile content and its leakage into otherwise-stable sources (independent of where it sits) |
| **DUPLICATION** | Repeated architecture/standards/conventions/instructions across sources |
| **CONTRADICTION** | Conflicting instructions across sources |
| **ACTIVATION** | Whether authored rules/skills can actually load: missing/invalid activation metadata, missing `description`/`globs`, `alwaysApply` misconfiguration, dormant rules, invalid skill frontmatter |
| **ARCHITECTURE** | Structural health of the surface: sprawl (too many overlapping sources), missing consolidation seams, misplaced files |
| **OWNERSHIP** | Ownership-boundary violations: user-controlled sources restating tool- or provider-controlled content |
| **STYLE** | Instruction-file hygiene: clarity, structure, heading discipline, instruction-file-as-worklog/scratchpad, contradictory phrasing within a source |

Two deliberate structural choices:

- **CACHE is split into `ORDERING` and `VOLATILITY`.** The former `CACHE` pack
  conflated two distinct concerns — *sequence* (what comes before what) and
  *change* (what is volatile). They are related but separable: a value can be
  volatile without being mis-ordered, and content can be mis-ordered without
  being volatile. Splitting them yields cleaner, individually-testable rules.
  **Cache-friendliness is a cross-cutting concern served primarily by these two
  packs**, not a pack of its own — which is why caching no longer names the
  product (§0.1).
- **`ACTIVATION` is its own pack**, not a corner of `ARCHITECTURE`. The
  validation dry-run showed activation-metadata problems (dormant Cursor rules,
  missing `description`/`globs`) to be among the most actionable findings and a
  whole observable class in their own right; they also make the tool useful far
  beyond caching.

Prompt caching is deliberately **not** the product; it is one concern among many.
The architecture allows arbitrarily many future packs (§13) without touching
existing ones.

### 7.4 Rule identifier scheme

Rule IDs **MUST** be stable across versions and namespaced by pack, e.g.
`ORDER001`, `VOL001`, `DUP001`, `CONTRA001`, `ACT001`, `ARCH001`, `OWN001`,
`STYLE001`. IDs are permanent: a retired rule's ID is not reused. Third-party
packs SHOULD use a vendor prefix (e.g. `ACME-ORDER001`) to avoid collisions with
core IDs.

### 7.5 Illustrative v1 rules (non-normative examples)

These illustrate the *kind* of rules and are not an exhaustive list.

- `ORDER001 — Early volatility`: a volatile segment appears before stable project
  information (a `precedes` edge from volatile to stable). *Observable.*
- `ORDER002 — Interleaved ordering`: stable/volatile segments alternate rather
  than grouping stable-first. *Observable within a source; cross-source ordering
  is inference and MUST be labelled.*
- `VOL001 — Volatility leakage`: a `mixed` segment embeds volatile spans inside
  an otherwise stable source. *Observable.*
- `VOL002 — References vs embeds volatile data`: distinguishes a stable
  instruction that *points at* volatile state (via `references`/`depends_on`)
  from one that *embeds* a volatile value — only the latter is flagged. *Observable.*
- `DUP001 — Duplicated standard`: the same standard/instruction appears in ≥2
  sources (a `duplicates` edge). *Observable.*
- `CONTRA001 — Conflicting instruction`: two sources give opposing directives (a
  `contradicts` edge). *Observable.*
- `ACT001 — Dormant rule`: a rule sets `alwaysApply:false` yet declares neither
  `description` nor `globs`, so it can never be auto-selected. *Observable.*
- `ACT002 — Missing/invalid activation metadata`: a rule/skill file lacks required
  frontmatter or has malformed metadata. *Observable.*
- `ARCH001 — Instruction sprawl`: many overlapping sources where consolidation is
  possible. *Observable count; agent-context impact may be inference, labelled.*
- `OWN001 — Ownership leakage`: a user-controlled source restates content that is
  tool- or provider-controlled. *Observable fact + inference about origin,
  labelled.*
- `STYLE001 — Instruction file used as worklog`: an instruction source is
  dominated by volatile session narrative/decisions rather than durable guidance.
  *Observable.*

### 7.6 Configuration

Rules and packs are configurable: enable/disable, priority override, and
per-rule thresholds where applicable. Configuration participates in determinism
(§4.3). Unknown rule IDs in config **MUST** produce a warning, not a silent
no-op, and **MUST NOT** change other rules' behaviour.

---

## 8. Findings Model

### 8.1 Purpose

A **finding** is the atomic unit of output: one observed structural issue, with
evidence, explanation, recommendation, confidence, and ownership. The findings
schema is the contract between the analysis core and every report renderer.

### 8.2 Fields

Normative field semantics (names/serialization are an implementation choice):

| Field | Meaning | Required | Notes |
|-------|---------|----------|-------|
| `id` | Deterministic identifier for *this occurrence* | Yes | Stable across runs on unchanged input; distinct from `rule_id` |
| `rule_id` | The rule that produced it | Yes | Namespaced (§7.4) |
| `title` | Short human summary | Yes | From rule metadata, may be specialised |
| `category` | Rule pack | Yes | e.g. ORDERING, VOLATILITY, DUPLICATION, ACTIVATION |
| `priority` | Engineering-value band | Yes | High/Medium/Low value or Informational (§10.2) — "should I fix this?" |
| `verification` | `confirmed` \| `requires-verification` | Yes | Orthogonal to priority (§10.4) — "can the tool prove it?" |
| `observability` | `observable` \| `inference` | Yes | Nature of the claim; if `inference`, the finding text MUST be phrased as such |
| `evidence` | One or more locatable citations | Yes | Path + range/anchor + matched excerpt |
| `explanation` | Why this matters, provider-agnostic | Yes | No provider-specific claims of fact |
| `recommendation` | Concrete suggested change | Yes | Must be actionable; must not assert an outcome as measured |
| `confidence` | `high` \| `medium` \| `low` | Yes | Confidence in the finding itself |
| `ownership` | `user` \| `tool` \| `provider` \| `unknown` | Yes | Who can act (see §11) |
| `related` | Other finding/segment references | No | For grouping (e.g. duplicate pairs) |
| `patchable` | Whether a safe patch can be generated | No | Drives §12; default false |

### 8.3 Fields deliberately excluded

To avoid fabricated precision, findings **MUST NOT** carry: numeric severity
scores, predicted hit-rate deltas, estimated token/cost savings, or any
percentage not directly countable from source. A finding MAY state a countable
observable (e.g. "this instruction appears in 3 files") because that is a fact.

### 8.4 Determinism of findings

Findings **MUST** be emitted in a deterministic order (e.g. by priority, then
`rule_id`, then evidence location). The `id` **MUST** be reproducible so that the
same repository state yields the same finding IDs across runs and machines,
enabling diffing between audits (§14).

### 8.5 Illustrative finding (non-normative)

The following shows *shape and content*, not a required serialization:

```
id:            f_9f2a1c
rule_id:       ORDER001
title:         Volatile "current sprint" appears before project standards
category:      ORDERING
priority:      High value
verification:  confirmed
observability: observable
confidence:    high
ownership:     user
evidence:
  - CLAUDE.md:12-14  ("Current sprint: 47")
  - CLAUDE.md:40-88  (project standards section)
explanation:   Content before the first change is what a prompt cache can reuse.
               Placing a value that changes every sprint ahead of stable
               standards means the stable material sits behind a frequent
               change point.
recommendation: Move the "current sprint" line below the project standards
               section, grouping it with other dynamic values near the end of
               the file.
patchable:     true
```

Note what is absent: no score, no "+18% cache hit rate", no cost figure. The
*why* is explained in provider-agnostic terms.

---

## 9. Output Design

### 9.1 Principles

- **Two audiences, one source of truth.** A human-readable report and a
  machine-readable findings artifact are both rendered from the same canonical
  findings set. They **MUST NOT** disagree.
- **Honesty is visible.** Observable and inference content are visually
  distinguished; inference is always labelled.
- **No fabricated metrics** appear anywhere in any report.
- **Read-only by default.** Producing reports does not modify tracked files
  (writing a report file only when the user requests file output is permitted).

### 9.2 Artifacts

| Artifact | Audience | Purpose |
|----------|----------|---------|
| **Prompt Surface Inventory** | Human | What prompt surface was discovered (present *and* absent adapters), rendered *before* findings — useful even when there are no findings (see §9.3) |
| **Executive Summary** | Human | What was audited, headline counts by priority/category, top issues, and an explicit honesty note |
| **Detailed Findings** | Human | Full findings with evidence, explanation, recommendation, confidence, ownership |
| **Implementation Roadmap** | Human | Findings sequenced by engineering value *and dependency* (from §9.7) |
| **Recommendation Dependency Graph** | Human/Tools | Which recommendations should precede others, and why (see §9.7) |
| **Audit Diff** (when a baseline exists) | Human/Tools | Resolved / introduced / unchanged findings vs a baseline (see §14) |
| **Machine findings** | Tools/CI | The canonical findings set for gating and diffing (see §9.8) |
| **Patch Preview / Validation / Apply summary** (opt-in) | Human | Proposed diff, its validation result, and (if applied) branch/commit/rollback info (see §12) |

### 9.3 Prompt Surface Inventory (non-normative layout)

The inventory is rendered **before** any findings. It states, per adapter,
whether a source type was found — including explicit **absences** — so the reader
always knows what was in and out of scope. This provides value even for a
repository with zero findings, and improves explainability.

```
Prompt Surface Inventory

Discovered (instruction)
  ✓ CLAUDE.md                 1 file
  ✓ AGENTS.md                 1 file
  ✓ Cursor rules              3 files (.cursor/rules/*.mdc)
  ✓ Prompt builder            1 (src/prompt/build.ts — analysed statically)
  ✓ Runtime templates         4 (prompts/*.prompt)

Discovered (config, not instruction)
  ✓ OpenCode config           .opencode/opencode.json
  ✓ Serena project config     .serena/project.yml

Not found
  ✗ Copilot instructions      (.github/copilot-instructions.md)
  ✗ MCP instructions

Out of scope (data)
  • research/**/*.json         captured contexts / run outputs

Notes
  Sources are classified by subtype: instruction | config | data. Only
  instruction sources are audited for structure; config and data are listed
  for transparency but not flagged (see §5.3).
```

### 9.4 Executive Summary (non-normative layout)

```
Prompt Structure Audit — Executive Summary

Scope
  Instruction sources audited: 6 (CLAUDE.md, AGENTS.md, .cursor/rules/*, ...)
  Rule packs run: ORDERING, VOLATILITY, DUPLICATION, CONTRADICTION,
                  ACTIVATION, ARCHITECTURE, OWNERSHIP, STYLE

Findings by priority
  High value:    3
  Medium value:  5
  Low value:     2
  Informational: 4

Findings by verification (orthogonal to priority)
  Confirmed:              13
  Requires Verification:   1

Top issues
  1. [ORDER001] High value · Confirmed — volatile "current sprint" before standards (CLAUDE.md)
  2. [DUP001]   High value · Confirmed — "testing strategy" duplicated across 3 files
  3. [ACT001]   High value · Confirmed — dormant Cursor rule: no description/globs (.cursor/rules/impl.mdc)

Change since baseline (if a baseline exists — see §14)
  Resolved: 2   Introduced: 0   Unchanged: 13

Honesty note
  This audit reports structure observable from repository contents. It does
  not measure or predict cache hit rate, cost, or latency. Items marked
  (inference) or "Requires Verification" cannot be directly observed and should
  be checked with runtime evidence.
```

### 9.5 Detailed Findings (non-normative layout)

```
[ORDER001] High value · Confirmed · observable · confidence: high · owner: user
Volatile "current sprint" appears before project standards

Evidence
  CLAUDE.md:12-14   "Current sprint: 47"
  CLAUDE.md:40-88   project standards

Why it matters
  A cache reuses the prompt up to the first change. Stable standards placed
  after a frequently-changing line sit behind that change point.

Recommendation
  Move the volatile line below the standards section; group dynamic values
  together near the end.

Depends on
  DUP001 should be applied first (the same standards block is duplicated;
  consolidating avoids reordering it twice). See §9.7.

Patch available: yes  (preview → validate → apply; §12)
```

### 9.6 Implementation Roadmap (non-normative layout)

Findings are sequenced by engineering value **and by the dependency graph of
§9.7** (e.g. consolidate duplicates before reordering, so reordering happens
once):

```
Implementation Roadmap

Phase 1 — High value, no unmet dependencies
  - DUP001  Consolidate duplicated "testing strategy" into one source
  - ACT001  Add description/globs to the dormant rule

Phase 2 — High/medium, unblocked by Phase 1
  - ORDER001 Move "current sprint" below standards (after DUP001)

Phase 3 — Medium / low / informational
  - STYLE003 Split instruction/worklog content
  - OWN001   Remove restated provider-owned content
```

### 9.7 Recommendation Dependency Graph

Rules are independent (§7.1); **recommendations are not**. Acting on one
recommendation can change the cost, safety, or even necessity of another. The
Recommendations stage therefore computes a directed **recommendation dependency
graph** and the roadmap is a topological ordering of it.

- **Distinct concepts.** `Rule → Finding → Recommendation → Recommendation
  Dependency Graph`. A rule produces findings; a finding yields a recommendation;
  dependencies are edges *between recommendations*.
- **Where dependencies come from.** Primarily from Prompt Model edges (§6.7):
  a `duplicates` edge implies "consolidate before reorder"; a
  `references`/`depends_on` edge implies "do not move A away from B"; a
  `governs` edge implies "fix activation before auditing the body's ordering".
- **Edge semantics.** An edge `A ⇒ B` means "prefer applying A before B", with a
  reason string and a type: `enables` (A makes B simpler/possible),
  `supersedes` (A may remove the need for B), or `conflicts` (A and B should not
  both be applied blindly). Cycles **MUST** be detected and reported rather than
  silently broken.
- **Determinism.** The graph is a deterministic function of the findings and the
  Prompt Model; it introduces no runtime inference and no fabricated metric.

```
Recommendation Dependency Graph (illustrative)

  DUP001 ──enables──▶ ORDER001        "consolidate the block, then move it once"
  ACT001 ──enables──▶ ORDER002        "make the rule load before judging its order"
  DUP002 ──supersedes──▶ STYLE003     "consolidation removes the style issue"
```

### 9.8 Machine-readable artifact

A stable, documented, structured artifact (e.g. a JSON document) containing the
canonical findings set exactly as specified in §8, the recommendation dependency
graph (§9.7), the Prompt Surface Inventory (§9.3), and run metadata (tool
version, rule config hash, source inventory, baseline reference if any). This
artifact is what CI consumes and what two audits are diffed against (§14). Its
schema is versioned.

---

## 10. Priority & Verification

Every finding is described along **two orthogonal dimensions**. Conflating them
produces awkward, meaningless combinations; separating them keeps each honest.

| Dimension | Question it answers | Values |
|-----------|---------------------|--------|
| **Priority** (§10.2–10.3) | *Should I fix this?* — engineering value | High value / Medium value / Low value / Informational |
| **Verification** (§10.4) | *Can the tool actually prove it?* — epistemic confidence | Confirmed / Requires Verification |

A finding can legitimately be **"High value + Requires Verification"** (worth
acting on, but the tool cannot confirm the effect from source alone) or
**"Low value + Confirmed"** (provable, but minor). These are independent axes:
priority is about worth, verification is about provability.

### 10.1 Rationale for not using severity

Traditional severity (Critical/High/Medium/Low) implies a risk of *failure* or
*harm*. Structural prompt issues rarely "break" anything; they erode stability,
maintainability, and reuse. Severity also invites the fabricated-precision trap
(ranking by an invented score). Instead, priority ranks by **engineering
value**: how much value acting on the finding is likely to deliver relative to
effort and certainty — a framing honest about the fact that these are
*improvements*, not defects.

### 10.2 Priority bands

| Band | Meaning |
|------|---------|
| **High value** | Clear structural improvement with broad or compounding benefit and reasonable effort |
| **Medium value** | Worthwhile improvement, narrower benefit or higher effort |
| **Low value** | Minor or cosmetic improvement |
| **Informational** | An observation worth surfacing that needs no action |

### 10.3 Assigning priority

- Each rule declares a `default_priority`; a finding MAY refine it based on
  observable factors (e.g. duplication across *more* files → higher value).
- Priority derivation **MUST** be deterministic and documented.
- Priority **MUST NOT** be computed from any inferred runtime metric.

### 10.4 Verification status

`verification` is a separate, required field on every finding (§8.2):

| Status | Meaning |
|--------|---------|
| **Confirmed** | The finding — both the fact *and* its relevance — is fully supported by observable repository contents. |
| **Requires Verification** | The finding, or its impact, depends on information the tool cannot observe (e.g. true cross-source runtime order, provider assembly). Surfaced honestly, stating exactly what runtime/external evidence would confirm or dismiss it. |

`Requires Verification` **was previously modelled as a priority band named
`Blocked`.** It is now a status because it answers a different question from
priority: "blocked" wrongly implied the tool knew the answer but could not
proceed, whereas the situation is *epistemic* — the tool genuinely cannot
determine the answer from what it observes. Making it a status lets a finding be
both high value and unprovable, which a single band could not express.
(Alternatives considered for the name: "Requires Runtime Evidence", "Not
Observable"; "Requires Verification" covers both the not-observable and
needs-runtime-evidence cases.)

Relationship to `observability` (§8.2): `observability` describes the *nature of
the claim* (observed fact vs inference); `verification` is the *disposition*
(can the tool stand behind the finding, or must the user verify externally).
They correlate — inference-dependent findings are typically
`Requires Verification` — but they are recorded separately so the report can say
both "this is an inference" and "here is what would confirm it". A finding whose
correctness hinges on unobservable data **MUST** be `Requires Verification`
regardless of its priority.

---

## 11. Ownership Boundaries

### 11.1 The three domains

Every segment and finding is attributed to who actually controls the content:

| Ownership | Meaning | Can the user act? |
|-----------|---------|-------------------|
| **User controlled** | Repo content the user authored/edits (`CLAUDE.md`, rules, templates, builder source) | Yes — recommendations are actionable |
| **Tool controlled** | Content injected by the agent/tooling (agent-managed memory, tool-injected context, skill scaffolding) | Sometimes — via tool configuration, not by editing a file |
| **Provider controlled** | Hidden system prompts, provider context assembly, internal ordering | No — unobservable; only inference |
| **Unknown** | Cannot be attributed with confidence | Treated cautiously; usually marked `requires-verification` (§10.4) |

### 11.2 Why this matters

Recommendations must not tell a user to "fix" something they cannot control.
Ownership determines whether a finding yields an actionable recommendation (user
domain), a configuration suggestion (tool domain), or an *inference-labelled
note* (provider domain). A finding whose fix lies in the provider domain is
typically marked `requires-verification` (and often `Informational` priority),
never a confident "do this".

### 11.3 Representation

Ownership is a required field on both segments (§6.3) and findings (§8.2).
Adapters supply a default ownership per source; rules MAY refine it with
evidence. Provider-domain statements **MUST** be labelled `inference`.

---

## 12. Patch Generation

### 12.1 Stance

Patch generation is **opt-in, off by default, and deliberately conservative**.
The analysis phase never proposes edits to files; a user must explicitly enter
modification mode and select a specific finding.

### 12.2 Capabilities (in order of the intended workflow)

The workflow is **Preview → Validate → Apply** — validation is a distinct phase
between previewing and writing.

1. **Preview** — render the proposed diff for exactly one finding, changing
   nothing. This is always the first step.
2. **Validate** — before writing anything, apply the proposed change to an
   **in-memory / scratch copy** and **re-run the full analysis** against it.
   Compare the resulting findings to the current audit:
   - if the target finding is resolved **and** no new findings are introduced
     **and** nothing regresses to a worse priority, validation **passes**;
   - otherwise validation **fails** and the application **MUST abort**, reporting
     exactly which findings would have been introduced or worsened.
3. **Single-finding application** — apply the change for *one* selected,
   `patchable` finding, only after validation passes. Bulk apply is **not**
   offered in v1.
4. **Branch creation** — apply on a dedicated branch, never directly on the
   user's working branch, so the change is trivially isolable.
5. **Individual commits** — one finding ⇒ one commit, with a message referencing
   the `rule_id` and finding `id`, so history is legible and bisectable.
6. **Rollback** — because each change is one commit on an isolated branch,
   reverting is a single, obvious operation. The apply summary states exactly how.

### 12.3 The validation invariant

Validation gives the implementation a load-bearing invariant:

> **Applying a recommendation MUST NOT make the audit worse.**

Concretely, for the change under consideration, the post-change audit **MUST**
resolve the target finding and **MUST NOT** introduce new findings or push any
existing finding to a higher-value/worse band. Because analysis is a
deterministic pure function (§4.3), this check is exact, repeatable, and free of
runtime inference — the same engine that produced the audit validates the fix.
This is the safety mechanism that makes even mechanical patches trustworthy: a
"move" that would, say, create a new early-volatility problem elsewhere is caught
and refused before any bytes are written.

### 12.4 Safety requirements

- Only findings marked `patchable` (and whose ownership is `user`) are eligible.
- A patch **MUST** be a mechanical, reviewable transformation (e.g. *move* a
  block, *deduplicate* a restated section) — never a semantic rewrite of the
  user's wording.
- The tool **MUST** show the preview, **MUST** pass validation (§12.3), and
  **MUST** obtain explicit confirmation before writing anything.
- Re-running analysis after apply **MUST** show the finding resolved and
  introduce no hidden changes (this is the same check validation performed
  pre-write, now confirmed post-write).

### 12.5 Why single, isolated changes beat bulk rewriting

- **Reviewability** — one small diff per issue is easy to reason about; a bulk
  rewrite is not.
- **Attribution** — each commit maps to one finding, so intent is preserved in
  history.
- **Reversibility** — undoing one change never entangles others.
- **Trust** — the tool earns adoption by never surprising the user with sweeping,
  hard-to-audit edits. This mirrors the linter norm of `--fix` for individual,
  well-understood rules, not wholesale reformatting of authored prose.

Automatic prompt rewriting is explicitly a **non-goal** for v1 (§1.2) and a
future concern (§16).

---

## 13. Extensibility

### 13.1 Goals

The repository is expected to accumulate many rules over time. Adding coverage
**MUST NOT** require modifying existing rules, the Prompt Model, or the report
renderers.

### 13.2 Extension seams

| Seam | What it enables | Contract that keeps it additive |
|------|-----------------|---------------------------------|
| **Source adapter** (§5.2) | New prompt-source types | Speak "raw sources with provenance"; must not alter other adapters |
| **Rule** (§7.1) | New checks | Pure function of Prompt Model → findings; namespaced ID |
| **Rule pack** (§7.3) | New categories | A named, independently toggleable group of rules |
| **Report renderer** (§9) | New output formats | Consume the canonical findings schema only |
| **Priority/config policy** | Org-specific tuning | Override defaults via config; no code change to rules |

### 13.3 Rules for adding rules

- New rules get new, permanent, namespaced IDs (§7.4); never reuse or repurpose.
- A rule declares its metadata (§7.2), including whether it is inherently
  `observable` or `inference`.
- A rule ships with isolated tests over small Prompt Model fixtures.
- Third-party/community packs use a vendor prefix and are discovered/enabled via
  config, so core and community rules coexist without collision.
- Changing a rule's behaviour in a way that alters findings is a **versioned**
  change (§9.8 schema version + tool version participate in determinism).

### 13.4 Backward compatibility

Because findings are keyed by stable IDs and rendered from a versioned schema,
downstream consumers (CI gates, dashboards, audit diffs) keep working as new
rules are added. Removing or materially changing a rule is a breaking change and
**MUST** be versioned and documented.

---

## 14. Audit Lifecycle: Baselines, Diff & Benchmarking

An audit is not a point-in-time report; it is one turn of a **continuous
engineering loop**. This section defines the baseline, the audit diff, CI use,
and how (external) benchmarking relates to all of it.

### 14.1 The lifecycle

```
   Audit ─▶ Baseline ─▶ Improve ─▶ Re-audit ─▶ Compare ─▶ (continue)
     ▲                                                        │
     └────────────────────────────────────────────────────────┘
```

- **Audit** — run the deterministic analysis (§4).
- **Baseline** — persist the machine-readable audit (§9.8) as the reference point.
- **Improve** — apply changes (manually, or via the validated patch mode §12).
- **Re-audit** — run analysis again on the new state.
- **Compare** — diff the re-audit against the baseline (§14.3).
- **Continue** — the new audit can itself become the next baseline.

This turns one-off analysis into **long-term repository health** and is the
foundation for CI adoption (§14.4).

### 14.2 The baseline

A **baseline** is simply a stored machine-readable audit artifact (§9.8) plus its
run metadata (tool version, rule config hash, source inventory). Because finding
`id`s are deterministic and reproducible (§8.4), a baseline can be compared to
any later audit of the same repository without re-deriving anything. A baseline
is data, not a metric: it contains no score, only findings and provenance.

### 14.3 Audit diff

Comparing a current audit to a baseline partitions findings by stable `id` into
three sets, using only countable facts:

| Bucket | Meaning |
|--------|---------|
| **Resolved** | In the baseline, absent now |
| **Introduced** | Absent in the baseline, present now |
| **Unchanged** | Present in both |

This lets the auditor answer, **without any fabricated metric**:

- *What improved?* → the Resolved set.
- *What regressed?* → the Introduced set.
- *What remains?* → the Unchanged set.

```
Audit Diff (illustrative, non-normative)

  Baseline: 12 findings        Current: 8 findings

  Resolved (4)
    - [ORDER001] volatile "current sprint" before standards
    - [DUP002]   duplicated testing strategy
  Introduced (0)
  Unchanged (8)
    - [ACT001]  dormant rule (still missing description/globs)
    - ...
```

"Overall audit evolution" is expressed as these three counts and their trend
over successive baselines — never as a single composite quality number, which
would reintroduce fabricated precision. Movement between priority bands (e.g. a
finding that dropped from High value to Low value) MAY be reported as an explicit
`reprioritised` sub-list, since band membership is itself a countable fact.

### 14.4 CI integration

The diff makes the auditor suitable as a CI gate. Typical policies (all
deterministic, all configurable):

- **No new findings** in the changed files (Introduced set must be empty).
- **No regressions** above a configured priority band.
- **Ratchet**: total findings in a chosen band MUST NOT increase versus the
  committed baseline.

CI consumes the machine artifact (§9.8); the baseline is committed to the repo so
comparisons are reproducible across machines.

### 14.5 Benchmarking (external, out of scope for the auditor)

The auditor **does not benchmark**. Benchmarking depends on a model, provider,
and workload — none observable from source, all non-deterministic. Embedding it
would violate the determinism and honesty principles. Instead, the auditor
produces **recommendations framed so a user can validate them experimentally and
independently**, and the lifecycle above supplies the controlled before/after:

1. Baseline the current audit (§14.2).
2. Apply exactly one validated change (§12), isolating the variable.
3. Measure *externally* — the provider's own cache/latency/cost telemetry or a
   user-run harness — under a representative, repeatable workload.
4. Compare against the baseline and attribute the delta to that single change.

The tool contributes stable finding IDs, isolated single changes, and
provider-agnostic mechanism explanations (e.g. "longer stable prefix before the
first change point"), **without asserting the magnitude of any result**.

### 14.6 Honesty guardrail

The tool **MUST NOT** report or imply benchmark outcomes it did not run, and the
audit diff **MUST NOT** be dressed up as a performance measurement. It may say
"this change is expected to increase the reusable stable prefix (observable);
whether that improves your cache hit rate depends on your provider and workload
(inference — verify independently)".

---

## 15. Risks

| Risk | Description | Mitigation in this design |
|------|-------------|---------------------------|
| **False positives** | A rule flags a non-issue (e.g. a "date" that is documentation, not a live value) | Evidence-backed findings the user can verify; confidence field; conservative, signal-based classification; per-rule config/thresholds |
| **False confidence** | Users treat structural findings as guaranteed performance wins | Strict observable/inference labelling; no fabricated metrics; honesty note in every report; benchmarking left to the user (§14) |
| **Platform differences** | Different agents/providers assemble context differently | Provider-agnostic Prompt Model and explanations; cross-provider runtime order treated as inference |
| **Hidden prompts** | System prompts and injected context the tool cannot see | Represented only as provider-owned/inference; never asserted; findings marked `requires-verification` (§10.4) |
| **IDE behaviour** | IDE-specific injection/ordering is opaque | Not asserted; ordering claims that depend on it are inference and marked `requires-verification` |
| **Provider differences** | Cache mechanics vary and change over time | The tool reasons about *structure*, not any specific cache implementation |
| **Unknown runtime order** | The true concatenation order across sources may be unobservable | Ordering confidence recorded; cross-source ordering is inference; findings marked `requires-verification` (§10.4) for exactly this case |
| **Future compatibility** | New source types / provider changes | Additive adapter and rule model (§13); versioned schema; stable IDs |
| **Config drift / non-determinism** | Environment-dependent results | Determinism boundary (§4.3); config hash + tool version recorded in output |
| **Over-eager patching** | Automated edits corrupt authored prose | Opt-in, preview-first, single-change, isolated-branch, reversible modification model (§12); mechanical transforms only |

---

## 16. Future Evolution

These are **out of scope for v1** but are the reason the v1 architecture is
shaped as it is. Each is enabled by a seam that already exists.

| Future phase | Description | Which v1 seam enables it |
|--------------|-------------|--------------------------|
| **Runtime optimisation** | Observe live context assembly and advise at run time | The Prompt Model becomes the shared representation between static and runtime views |
| **Prompt orchestration** | Coordinate multiple sources into an intentional assembly order | Ordering + ownership metadata already modelled |
| **Live prompt transformation** | Reorder/deduplicate context as it is built | Mechanical, single-change patch discipline (§12) generalises to runtime transforms |
| **Semantic prompt rewriting** | Improve wording, not just structure | Explicitly deferred; would require a new, clearly-labelled rule class and stronger safety review than v1 offers |
| **Cross-repo policy** | Enforce org-wide prompt conventions | Deterministic, machine-readable findings + config policy already suit CI/fleet use |
| **Runtime-verified findings** | Fold real telemetry back to confirm structural findings | Stable finding IDs + snapshots make before/after correlation possible |

The guiding rule for every future phase remains the founding one: **never
fabricate precision, and always separate the observable from the inferred.**

---

## Appendix A — Glossary

- **Observable** — a fact derivable directly from repository contents (files,
  rules, templates, builder source). May be reported confidently.
- **Inference** — a claim about something not directly observable (provider cache
  behaviour, hit rate, cost, hidden prompts, IDE internals, true runtime order).
  Must always be labelled as inference; never presented as measurement.
- **Source** — a discovered artifact that shapes agent context.
- **Segment / Unit** — the ordered elements of the Prompt Model (§6).
- **Rule** — an independent, deterministic check over the Prompt Model (§7).
- **Rule pack / category** — a named, toggleable group of rules (e.g. ORDERING,
  VOLATILITY, ACTIVATION).
- **Relationship / edge** — a typed, directed connection between segments in the
  Prompt Model graph (e.g. `precedes`, `duplicates`, `governs`) (§6.7).
- **Baseline** — a stored machine-readable audit used as the reference point for
  comparison (§14.2).
- **Audit diff** — the partition of findings into resolved / introduced /
  unchanged versus a baseline (§14.3).
- **Recommendation dependency graph** — directed graph of "apply-before" ordering
  between recommendations (§9.7).
- **Finding** — one observed structural issue with evidence and recommendation
  (§8).
- **Priority** — the "should I fix this?" dimension: High/Medium/Low value or
  Informational (§10.2).
- **Verification status** — the orthogonal "can the tool prove it?" dimension:
  `confirmed` or `requires-verification` (§10.4); formerly the `Blocked` band.
- **Ownership boundary** — user / tool / provider / unknown control domain (§11).
- **Determinism boundary** — the line before which the tool is a pure function of
  `(repo state, tool version, config)` (§4.3).

## Appendix B — Relationship to the former `cache-audit` skill

This RFC intentionally supersedes `cache-audit`. Concretely:

- **Removed** (fabricated precision): "Overall Cache Score (0–100)", "Stable
  Prefix %", "Estimated Cache Friendliness", and expected outcomes such as
  "higher cache hit ratio" and "lower effective inference cost".
- **Reframed**: the eight ad-hoc "tests" become **rules within the `ORDERING` and
  `VOLATILITY` packs**, each independent, deterministic, and evidence-backed.
- **Generalised**: cache-friendliness is one cross-cutting concern served by
  `ORDERING`/`VOLATILITY`; the taxonomy also includes `DUPLICATION`,
  `CONTRADICTION`, `ACTIVATION`, `ARCHITECTURE`, `OWNERSHIP`, and `STYLE`, and the
  architecture admits arbitrarily many more (§0.1, §7.3).
- **Preserved**: the core, honest insight that a cache reuses the prompt up to
  the first change, so stable content should precede volatile content — now
  stated as a *mechanism to explain*, not an outcome to promise.

## Appendix C — Open questions for reviewers

1. Should `mixed` stability decompose into sub-segments automatically, or only
   when a rule requests finer granularity?
2. What is the minimum viable config format, and should adapter/rule config share
   one file?
3. For runtime prompt builders, how far should static extraction go before a
   fragment is declared `unknown`?
4. Should the machine-readable schema be frozen at v1, or explicitly labelled
   experimental until the rule set stabilises?
5. Where should the baseline live — committed in-repo (reproducible, versioned)
   vs stored by CI — and what is the canonical format (§14.2)?
6. How should recommendation-dependency **cycles** be surfaced to the user when
   detected (§9.7): reported and left to the user, or broken by a documented
   deterministic tie-break?
7. Which relationship types in §6.7 are worth shipping in v1 vs deferring, given
   each adds construction cost to the Prompt Model?

> **Resolved on review (was Open Question 2):** whether `Requires Verification`
> should be a priority band or an orthogonal status. **Decision: an orthogonal
> `verification` status**, separate from priority (§10.4) — priority answers
> "should I fix this?", verification answers "can the tool prove it?".
