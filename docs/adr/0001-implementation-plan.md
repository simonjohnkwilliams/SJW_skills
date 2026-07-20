# ADR 0001 — Prompt Structure Auditor: Implementation Plan

| Field | Value |
|-------|-------|
| **Type** | Architecture Decision Record — Implementation Plan |
| **Status** | Proposed — for sign-off before Phase 1 |
| **Implements** | [RFC 0001 — Prompt Structure Auditor, v0.2.0](../rfc/0001-prompt-structure-auditor.md) |
| **Scope** | *How* the RFC is built. This ADR describes structure, interfaces, and mechanisms only. |

> **Binding rule for this ADR.** This document **MUST NOT change RFC behaviour.**
> Where the RFC is silent on a purely internal matter, this ADR makes a decision
> and labels it an **Assumption (A#)**. Where the RFC left an explicit open
> question, this ADR records an implementation-level default without altering the
> contract. Nothing here relaxes an architectural constraint from the Implementation
> Brief.
>
> Code fences below are **interface sketches**, not final code. They exist to make
> two independent implementations converge; they are not the implementation.

---

## 0. Engineering Principles

The architecture (RFC) says *how the system is structured*. These principles say
*how to decide when you hit ambiguity* — the questions no diagram answers. When a
trade-off is unclear, resolve it in favour of the higher-listed principle.

1. **Preserve determinism over convenience.** If a shortcut risks non-reproducible
   output, take the longer deterministic path.
2. **Prefer observable evidence over inferred conclusions.** State what you can
   see; label everything else as inference.
3. **Never sacrifice explainability for optimisation.** A finding a human cannot
   verify is worthless, however clever.
4. **Every recommendation must be independently testable.** Frame it as a
   hypothesis with a controlled before/after, never as a promised outcome.
5. **Rules remain independent.** No rule may depend on another rule or its output.
6. **The Prompt Model is the system of record.** Build it once, treat it as
   immutable, and read everything from it.
7. **Implementation must follow the RFC, not reinterpret it.** Ambiguity is
   documented as an assumption, not resolved by silent redesign.
8. **Backwards compatibility matters more than cleverness.** Stable IDs and
   versioned schemas outrank elegant refactors.
9. **Small vertical slices over horizontal completeness.** Ship one working
   end-to-end path before broadening.
10. **When uncertain, produce evidence rather than confidence.** Emit a
    `requires-verification` finding with the evidence needed, not a confident guess.

### 0.1 The single-responsibility mandate

The most effective guardrail against architecture drift: **every object has
exactly one reason to exist.** Nothing does two jobs.

| Component | Its one job |
|-----------|-------------|
| Discovery | discovers sources |
| Prompt Model | models the surface as an immutable graph |
| Rules | detect issues |
| Findings | explain issues |
| Recommendations | sequence fixes |
| Patch | modifies files |
| Validation | protects the invariant |

If a change tempts a component to take on a second job, that is the signal to add
a new component instead.

---

## 1. Context

RFC 0001 defines a deterministic, read-only static analyser for a repository's
prompt-construction surface, plus an opt-in, validated patch workflow. This ADR
selects the technology, module boundaries, data models, interfaces, serialization,
CLI, and test strategy that realise that contract, and sequences the work as
vertical slices (one usable tool per phase).

### 1.1 Non-negotiable constraints (from the brief) and where they are enforced

| Constraint | Enforcement mechanism (this ADR) |
|------------|----------------------------------|
| Analysis is deterministic (no net/clock/rng/provider) | §7 Determinism strategy; purity test harness (§11.4); no such imports in `core` |
| Prompt Model is immutable | Frozen dataclasses + tuples (§4, §5.3); constructed once in `model`, never mutated |
| Rules are read-only; do not create edges/mutate nodes | `Rule` protocol receives a read-only view; edges built in `model`, not `rules` (§8) |
| Recommendation graph is independent of rule deps | Built in `recommend` stage *after* findings (§5.6, §9) |
| Analysis never modifies the repo | `core` has no write API; only `patch` writes, on a branch (§10) |
| Validation mandatory; must not worsen audit | `patch.validate` re-runs `core.analyze` on a scratch tree (§10.3) |
| Observable vs inference; never fabricate precision | Types carry `observability`/`verification`; no numeric score fields exist (§5) |
| Ownership required; recommend only to the owner | `ownership` required on findings; recommender filters by owner (§9) |
| Roadmap from dependency graph, not priority | Roadmap = topological sort of the recommendation graph (§9) |
| Stable finding IDs | Content/anchor-based hashing (§7.2) |

---

## 2. Key implementation decisions

Each is a discrete decision (D#) with rationale and the main alternative.

| # | Decision | Rationale | Alternative considered |
|---|----------|-----------|------------------------|
| **D1** | **Language: Python 3.11+** | Matches sibling repos (`ai-context-benchmark`, BMAD skills ship Python); excellent text/frontmatter parsing; `pytest`+`syrupy` for golden/snapshot; trivial deterministic hashing; cross-platform (incl. Windows) | TypeScript/Node (aligns with `npx skills` distribution) — kept as fallback; see A1 |
| **D2** | **Ship as an Agent Skill**: `prompt-structure-auditor/` with `SKILL.md`, `scripts/` (the package), `references/` | RFC working name; skills distribute their own code under `scripts/` | Separate PyPI package — deferred; skill can vendor it later |
| **D3** | **Package name `psa`**, invoked `python -m psa` / console entry `psa` | Short, unambiguous | `prompt_structure_auditor` (verbose) |
| **D4** | **Immutability via `@dataclass(frozen=True)` + tuples** everywhere in `core` | Enforces "Prompt Model immutable" and safe sharing across rules | `attrs`; hand-rolled — no added value |
| **D5** | **Pure staged pipeline**: each stage a free function `stage(input, config) -> output` | Directly mirrors RFC §4; each stage independently testable | God-object orchestrator — hides the determinism boundary |
| **D6** | **Rules discovered via an explicit registry**, not import side-effects | Deterministic rule ordering; enable/disable by config | Entry-point plugin scan — nondeterministic order; deferred to §12 extensibility |
| **D7** | **Canonical JSON** for all machine artifacts (sorted keys, `ensure_ascii=False`, `\n`) | Byte-stable output ⇒ golden tests + audit diff work | Pickle/YAML — nondeterministic or lossy |
| **D8** | **Stable IDs by content+anchor hash** (blake2b, hex, truncated) | Reproducible across runs/machines; resilient to unrelated edits | Sequential integers — unstable across edits; breaks diff |
| **D9** | **CLI via `argparse`** (stdlib) | Zero-dependency, deterministic help; scriptable | `click`/`typer` — extra deps for little gain |
| **D10** | **Minimal deps**: stdlib + `PyYAML`/`tomllib` for frontmatter, `pytest`+`syrupy` (dev only) | Keep the analysis core dependency-light and auditable | Heavy parser stacks — determinism/audit risk |
| **D11** | **Repo access through a `RepoFS` port** (read-only interface) | Lets tests inject in-memory trees; guarantees no accidental writes in `core` | Direct `pathlib` calls in rules — leaks I/O into the Core Engine |
| **D12** | **Patch scratch validation via a copy-on-write temp worktree** | Validate before writing to the real branch (§10.3) | In-place edit + revert — unsafe if process dies mid-way |

---

## 3. Package / module structure

### 3.0 The Core Engine

The deterministic, read-only heart of the system is the **Core Engine** (formerly
called the "pure zone"). It takes `(repository state, configuration, tool
version)` and produces an `Audit` — with no network, clock, randomness, provider
API, or filesystem writes. Everything else is an **adapter around the Core
Engine**: the CLI drives it, reports render its output, the patch system consumes
and re-invokes it.

```
        CLI
         │
         ▼
   Core Engine ───▶ Prompt Graph ───▶ Rules ───▶ Reports
         │                                          
         ▼                                          
   Patch System   (separate; re-invokes the Core Engine to validate)
```

The Core Engine is `psa.core` plus the pure stages it orchestrates
(`discovery → model → rules → findings → recommend`). Naming it explicitly makes
the project easy to explain: *the Core Engine analyses; adapters surround it.*

### 3.1 Layout

Everything ships inside the skill directory so `npx skills` distributes it intact.

```
prompt-structure-auditor/
├── SKILL.md                     # skill contract (authored later; not this ADR)
├── references/                  # links back to RFC/ADR excerpts, loaded on demand
└── scripts/
    ├── pyproject.toml           # package metadata, entry point `psa`
    ├── psa/
    │   ├── __init__.py
    │   ├── __main__.py          # `python -m psa`
    │   ├── cli.py               # argparse command surface (§10 CLI)
    │   │
    │   ├── core/                # THE CORE ENGINE — deterministic, read-only (§3.0)
    │   │   ├── pipeline.py      # analyze(): Discovery→Model→Rules→Findings→Recommend
    │   │   ├── config.py        # load/validate config; hashable ConfigView
    │   │   ├── ids.py           # stable ID hashing (§7.2)
    │   │   ├── canon.py         # canonical JSON (de)serialization (§7.3)
    │   │   └── ports.py         # RepoFS read-only port (D11)
    │   │
    │   ├── discovery/           # source adapters (RFC §5)
    │   │   ├── base.py          # SourceAdapter protocol + registry
    │   │   └── adapters/        # claude.py, agents.py, cursor_rules.py, ...
    │   │
    │   ├── model/               # Prompt Model construction (RFC §6)
    │   │   ├── types.py         # frozen Segment/Unit/Edge/PromptModel
    │   │   ├── builder.py       # sources -> immutable PromptModel graph
    │   │   ├── classify.py      # stability/content_kind/volatility signals (§6.4)
    │   │   └── relate.py        # edge construction (§6.7) — the ONLY edge writer
    │   │
    │   ├── rules/               # rule packs (RFC §7) — read-only over the model
    │   │   ├── base.py          # Rule protocol + RuleRegistry
    │   │   ├── ordering.py      # ORDER###
    │   │   ├── volatility.py    # VOL###
    │   │   ├── duplication.py   # DUP###
    │   │   ├── activation.py    # ACT###
    │   │   ├── style.py         # STYLE###
    │   │   ├── ownership.py     # OWN###
    │   │   └── contradiction.py # CONTRA###
    │   │
    │   ├── findings/            # findings model (RFC §8)
    │   │   ├── types.py         # frozen Finding
    │   │   └── normalize.py     # dedupe, order, assign stable ids (§8.4)
    │   │
    │   ├── recommend/           # recommendations + dependency graph (RFC §9.7)
    │   │   ├── types.py         # Recommendation, RecEdge, DependencyGraph
    │   │   ├── build.py         # findings -> recommendations
    │   │   └── graph.py         # dependency graph + topological roadmap
    │   │
    │   ├── report/              # rendering (RFC §9)
    │   │   ├── inventory.py     # Prompt Surface Inventory (§9.3)
    │   │   ├── human.py         # exec summary, detailed, roadmap (text/markdown)
    │   │   └── machine.py       # canonical JSON artifact (§9.8)
    │   │
    │   ├── lifecycle/           # baselines + audit diff (RFC §14)
    │   │   ├── baseline.py      # save/load baseline artifact
    │   │   └── diff.py          # resolved/introduced/unchanged (§14.3)
    │   │
    │   └── patch/               # SEPARATE, side-effecting workflow (RFC §12)
    │       ├── generate.py      # finding -> mechanical Patch (preview)
    │       ├── validate.py      # re-run core.analyze on scratch tree (§12.3)
    │       └── apply.py         # branch + one-commit apply + rollback info
    │
    └── tests/                   # see §11
        ├── fixtures/            # mini golden repos
        ├── unit/
        ├── golden/
        └── determinism/
```

**Dependency direction (enforced):** `discovery → model → rules → findings →
recommend → report/lifecycle`. `patch` depends on `core` (to validate) but nothing
in `core` may import `patch`. `rules` may import `model.types` but **not**
`model.relate` (rules cannot build edges).

---

## 4. Graph representation

The Prompt Model is a directed multigraph, stored as immutable value objects.

```python
@dataclass(frozen=True)
class Provenance:
    source_id: str          # adapter-assigned, stable
    path: str               # repo-relative, forward-slash normalized
    span: tuple[int, int] | None   # (start_line, end_line), 1-based; None if whole-file
    anchor: tuple[str, ...] # heading path, e.g. ("Setup", "CSV Format") — for stable ids

@dataclass(frozen=True)
class Segment:
    id: str                 # stable (see §7.2)
    provenance: Provenance
    order: int              # position within its source (cross-source order is inference)
    content_kind: str       # instruction|standard|role|example|retrieved|state|metadata
    stability: str          # stable|volatile|mixed|unknown
    volatility_signals: tuple[Evidence, ...]
    ownership: str          # user|tool|provider|unknown
    relocatability: str     # freely-movable|movable-within-source|fixed|unknown
    confidence: str         # high|medium|low
    evidence: tuple[Evidence, ...]

@dataclass(frozen=True)
class Edge:
    kind: str               # precedes|references|duplicates|contradicts|depends_on|derived_from|governs
    src: str                # Segment.id
    dst: str                # Segment.id
    observability: str      # observable|inference
    confidence: str
    evidence: tuple[Evidence, ...]

@dataclass(frozen=True)
class PromptModel:
    segments: tuple[Segment, ...]         # deterministic order
    edges: tuple[Edge, ...]               # deterministic order
    # precomputed read-only adjacency for rule convenience:
    _by_id: Mapping[str, Segment]         # types.MappingProxyType
    _out: Mapping[str, tuple[Edge, ...]]  # src -> edges
    _in:  Mapping[str, tuple[Edge, ...]]  # dst -> edges
```

- **Immutability:** all `frozen=True`; collections are tuples; adjacency maps are
  `MappingProxyType`. There is **no** mutating method. `model.relate` is the only
  code that constructs `Edge`s, and it runs during construction (before any rule
  sees the model).
- **Rule access:** rules receive a `ModelView` (read-only façade exposing
  `segments`, `edges`, `out(id)`, `in_(id)`, `get(id)`) — no setters exist.
- **Determinism:** segment order is `(source precedence, path sort, in-file order)`;
  edge order is `(kind, src, dst)`. Both are total orders (§7.1).

---

## 5. Internal data models

### 5.1 Evidence (shared)

```python
@dataclass(frozen=True)
class Evidence:
    path: str
    span: tuple[int, int] | None
    excerpt: str            # short, verbatim, for the reader to verify
```

### 5.2 Source (discovery output)

```python
@dataclass(frozen=True)
class Source:
    source_id: str          # e.g. "cursor_rules:.cursor/rules/impl.mdc"
    adapter: str            # adapter name
    subtype: str            # instruction|config|data   (Assumption A2, per validation feedback)
    path: str
    text: str               # raw contents (for instruction/config); data sources carry no text
    default_ownership: str  # user|tool|provider|unknown
    order_hint: int         # adapter precedence for deterministic ordering
```

### 5.3 Finding (RFC §8)

```python
@dataclass(frozen=True)
class Finding:
    id: str                 # stable (§7.2)
    rule_id: str            # namespaced, e.g. "ORDER001"
    title: str
    category: str           # pack
    priority: str           # High value|Medium value|Low value|Informational
    verification: str       # confirmed|requires-verification      (RFC §10.4)
    observability: str      # observable|inference
    confidence: str         # high|medium|low
    ownership: str          # user|tool|provider|unknown
    evidence: tuple[Evidence, ...]
    explanation: str
    recommendation: str
    related: tuple[str, ...] = ()
    patchable: bool = False
```

`priority` and `verification` are **separate fields** (RFC §10). No score,
percentage, or estimated-savings field exists anywhere in the type — fabricated
precision is impossible by construction.

### 5.4 Recommendation & dependency graph (RFC §9.7)

```python
@dataclass(frozen=True)
class Recommendation:
    finding_id: str
    action: str             # human-facing, mechanical description
    owner: str              # must equal the finding's ownership

@dataclass(frozen=True)
class RecEdge:
    src: str                # finding_id that should be applied first
    dst: str
    relation: str           # enables|supersedes|conflicts
    reason: str

@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[Recommendation, ...]
    edges: tuple[RecEdge, ...]
    # roadmap = deterministic topological order; cycles reported, never silently broken
```

### 5.5 Audit artifact, baseline, diff (RFC §9.8, §14)

```python
@dataclass(frozen=True)
class RunMeta:
    tool_version: str
    schema_version: str
    config_hash: str        # hash of the effective config (D7)
    inventory: tuple[InventoryRow, ...]
    baseline_ref: str | None

@dataclass(frozen=True)
class Audit:
    meta: RunMeta
    findings: tuple[Finding, ...]
    dependency_graph: DependencyGraph
    inventory: PromptSurfaceInventory

@dataclass(frozen=True)
class AuditDiff:
    resolved: tuple[str, ...]     # finding ids present in baseline, absent now
    introduced: tuple[str, ...]
    unchanged: tuple[str, ...]
    reprioritised: tuple[tuple[str, str, str], ...]  # (id, from_band, to_band)
```

---

## 6. Public API (library surface)

The CLI is a thin wrapper over these pure functions. The pipeline is callable
end-to-end or stage-by-stage (for testing each stage in isolation).

```python
# psa.core.pipeline
def analyze(repo: RepoFS, config: ConfigView, tool_version: str) -> Audit: ...

# individual stages (all pure)
def discover(repo: RepoFS, config: ConfigView) -> tuple[Source, ...]: ...
def build_model(sources: tuple[Source, ...], config: ConfigView) -> PromptModel: ...
def run_rules(model: PromptModel, config: ConfigView) -> tuple[Finding, ...]: ...
def normalize_findings(raw: tuple[Finding, ...]) -> tuple[Finding, ...]: ...
def build_recommendations(findings: tuple[Finding, ...],
                          model: PromptModel) -> DependencyGraph: ...

# psa.lifecycle
def save_baseline(audit: Audit, path: str) -> None: ...      # write-only helper (not in core)
def load_baseline(path: str) -> Audit: ...
def diff(current: Audit, baseline: Audit) -> AuditDiff: ...

# psa.report
def render_human(audit: Audit, diff: AuditDiff | None) -> str: ...
def render_machine(audit: Audit) -> str: ...                  # canonical JSON

# psa.patch  (separate, side-effecting workflow)
def preview(audit: Audit, finding_id: str, repo: RepoFS) -> Patch: ...
def validate(patch: Patch, repo: RepoFS, config: ConfigView,
             tool_version: str) -> ValidationResult: ...
def apply(patch: Patch, repo: WritableRepo, branch: str) -> ApplyResult: ...
```

**Purity contract:** `analyze` and every stage take a `RepoFS` (read-only port)
and a `ConfigView`; they return values and **never** touch the network, clock,
randomness, or filesystem writes. `tool_version` is passed in (not read from the
environment at call time) so results are reproducible in tests.

---

## 7. Determinism strategy

### 7.1 Ordering
Every collection that reaches output has a documented total order (segments,
edges, findings §8.4, rec-graph nodes/edges, inventory rows). Sorting keys are
strings/ints only — no locale-dependent or hash-seed-dependent comparisons.

### 7.2 Stable IDs (D8)
```
finding.id  = "f_" + blake2b( canonical(
                 rule_id, primary_evidence.path,
                 primary_evidence.anchor,            # prefer heading path over line no.
                 normalized(primary_evidence.excerpt)
              ), digest_size=8 ).hexdigest()
segment.id  = "s_" + blake2b( canonical(path, anchor, order, kind) ... )
```
Anchors (heading paths) are preferred over raw line numbers so that unrelated
edits elsewhere in a file do not churn IDs — this keeps baselines/diff/CI stable
(RFC §8.4). **Assumption A3:** when no heading anchor exists, fall back to a
normalized-excerpt hash; documented so both implementations agree.

### 7.3 Canonical serialization (D7)
`canon.dumps(obj)` → `json.dumps(obj, sort_keys=True, ensure_ascii=False,
separators=(",", ":")) + "\n"`. No floats are ever emitted (none exist in the
model). Identical `Audit` ⇒ byte-identical JSON.

### 7.4 Purity enforcement in tests
A determinism/purity harness (§11.4) runs analysis twice and asserts byte-equal
output, and executes `core` under a guard that fails if `socket`, `time`,
`random`, or `datetime.now` are invoked during analysis.

---

## 8. Rule interface (RFC §7)

```python
class Rule(Protocol):
    rule_id: str            # "ORDER001"
    category: str           # "ORDERING"
    title: str
    rationale: str
    default_priority: str
    default_verification: str      # confirmed | requires-verification
    ownership_hint: str
    observability: str             # observable | inference

    def check(self, model: ModelView, config: RuleConfig) -> Iterable[Finding]: ...
```

- **Read-only:** `check` receives a `ModelView` (façade over the immutable model)
  and returns findings; it cannot mutate anything or build edges. It consumes
  existing edges (built in `model.relate`) via `model.out(id)/in_(id)`.
- **Independent:** a rule sees only the model and its own `RuleConfig`; never
  other rules or their findings (recommendation dependencies come later, §9).
- **Deterministic & testable:** given a `ModelView`, output is fixed and ordered;
  each rule is unit-tested against small hand-built models.
- **Registration (D6):** a `RuleRegistry` holds an explicit ordered list; config
  enables/disables by id/pack. Unknown ids in config emit a warning (RFC §7.6).

**Assumption A4 (RFC Open Question 7):** v1 ships these edge kinds — `precedes`,
`duplicates`, `contradicts`, `references`, `governs` — and defers `depends_on`,
`derived_from` until the packs that need them (they are added in their phase
without touching earlier code).

---

## 9. Recommendation stage (independent of rules)

Runs **after** findings (constraint: recommendation deps ≠ rule deps).

1. Map each actionable finding → `Recommendation`, filtering by ownership:
   only `owner == user` findings yield an actionable recommendation; `tool`
   yields a configuration suggestion; `provider`/`unknown` yield an
   inference-labelled note (RFC §11.2). This is the "recommend only what the
   owner can perform" guarantee.
2. Derive `RecEdge`s from **Prompt Model edges** (`duplicates` ⇒ consolidate
   before reorder, etc.) and from finding `related` links (RFC §9.7).
3. Topologically sort into the roadmap. **Cycles are detected and reported**
   (never silently broken); ordering is stable via a deterministic tie-break on
   `finding.id`.
4. The roadmap is emitted **only** from this graph — never inferred from priority
   (brief: "Never infer ordering from priority alone").

---

## 10. Patch workflow (RFC §12) and CLI

### 10.1 CLI layout (D9)

```
psa audit [PATH] [--config FILE] [--format text|json] [--out FILE]
psa inventory [PATH]                       # surface inventory only
psa rules list [--pack NAME]
psa baseline save [PATH] --out baseline.json
psa diff [PATH] --baseline baseline.json [--format text|json]
psa patch preview  FINDING_ID [PATH]
psa patch validate FINDING_ID [PATH]
psa patch apply    FINDING_ID [PATH] [--branch NAME]
```

The flow `audit → findings → recommendations → preview → validate → apply` has
**no shortcut**: `patch apply` internally requires a passing `validate`, which
requires a `preview`, which requires an `audit`. `apply` refuses if validation
fails.

### 10.2 Preview
`patch.preview` turns one `patchable`, `owner == user` finding into a **mechanical**
transformation (move block / consolidate duplicate) and returns a unified diff.
It writes nothing.

### 10.3 Validate (mandatory, D12)
`patch.validate` materialises the repo + proposed diff into a **scratch temp
worktree**, runs `core.analyze` on it, and compares to the current audit:
- pass iff the target finding is resolved **and** no new finding is introduced
  **and** no finding moves to a worse priority band;
- otherwise return the offending findings and **abort** (no write).
This is exactly the RFC invariant: *applying a recommendation MUST NOT worsen the
audit* (RFC §12.3). Because `analyze` is pure, this check is exact and repeatable.

### 10.4 Apply
Only after validation passes: create/checkout a dedicated branch, apply the diff,
make **one commit** referencing `rule_id`+finding `id`, and print rollback
instructions. `apply` is the only function that touches tracked files, via a
`WritableRepo` port distinct from the read-only `RepoFS` used by `core`.

---

## 11. Testing strategy

Every phase ships all four test kinds before it is "done".

### 11.1 Unit tests
Per adapter, per classifier, per rule, per graph builder — using small,
hand-constructed inputs (e.g. a `PromptModel` fixture for a rule).

### 11.2 Golden output tests
Fixture mini-repos under `tests/fixtures/` (seeded from the three validation
repos, reduced to minimal reproductions). Each has committed golden `audit.json`
and `report.txt`; tests assert byte-equality.

### 11.3 Snapshot tests
`syrupy` snapshots for human-readable renderings, reviewed on change.

### 11.4 Determinism & purity harness
- **Repeatability:** run `analyze` twice on each fixture; assert identical bytes.
- **Machine-independence:** normalise nothing — IDs/paths must already be stable.
- **Purity guard:** patch `socket`, `time`, `random`, `datetime` during `core`
  execution to raise on use; any violation fails the suite.

### 11.5 Regression tests
The audit-diff of a fixture against its own committed baseline must be empty
(resolved/introduced/unchanged = 0/0/N). Patch tests assert the validation
invariant (a deliberately bad patch must be refused).

---

## 12. Vertical slice plan

Each phase yields a runnable tool.

**Refinement to the brief's suggested order (accepted):** Phase 1 is a
**rules-free walking skeleton** — Discovery → Prompt Graph → Inventory → JSON →
CLI, with *no rules and no findings*. This validates adapters, ordering, the
graph, serialization, stable IDs, and determinism **before** any rule complexity
exists, so the first end-to-end pipeline is almost guaranteed to work. `ORDER001`
becomes Phase 2. (The brief listed `ORDER001` in Phase 1; it explicitly invited
this reordering.)

| Phase | Deliverable | "Done" means |
|-------|-------------|--------------|
| **1 — Walking skeleton** | Discovery + adapters (Claude/AGENTS/Cursor) + immutable Prompt Graph + Prompt Surface Inventory + canonical JSON + `psa audit`/`psa inventory` CLI. **No rules, no findings.** | `psa audit`/`psa inventory` run on the three validation repos; inventory + empty-findings JSON emitted; **golden + determinism + purity + stable-ID tests pass** |
| **2 — First rule** | `ORDERING` pack (`ORDER001`) + finding generation + findings in text/JSON report | end-to-end audit *with* a finding on the fixtures; Phase 1 outputs otherwise unchanged |
| **3** | `VOLATILITY` (`VOL001`, `VOL002` references-vs-embeds) | new rules; only added findings |
| **4** | `DUPLICATION` (+`duplicates` edges) | duplicate pairs detected with edges |
| **5** | `ACTIVATION` (Cursor `.mdc`/skill frontmatter, dormant rules) | `ACT001/ACT002` on repo 2 |
| **6** | `STYLE` (instruction-as-worklog, hygiene) | `STYLE001` on repo 3 |
| **7** | `OWNERSHIP` (`OWN001` leakage) | ownership-boundary findings |
| **8** | `CONTRADICTION` (+`contradicts` edges) | conflicting-directive detection |
| **9** | Recommendation dependency graph + roadmap | roadmap is a topological sort; cycle test |
| **10** | Patch preview | mechanical diffs for `patchable` findings |
| **11** | Validation | invariant enforced; bad patch refused |
| **12** | Apply | branch + one-commit + rollback; post-apply re-audit clean |

Baselines/diff (RFC §14) land in **Phase 1** (needed for regression tests, and
trivial when findings are still empty) and are exercised further as packs are
added.

---

## 13. Assumptions & documented ambiguities

Per the guiding principle (identify ambiguity, document assumptions, propose
alternatives — do not redesign):

- **A1 — Language.** Python chosen (D1). If the maintainers prefer TypeScript for
  `npx skills` symmetry, the same module boundaries/interfaces port directly; only
  D3/D9/D10 change. *No RFC behaviour depends on this.*
- **A2 — Source subtype.** Discovery tags each source `instruction|config|data`
  (validation feedback / RFC §5.3); only `instruction` sources are audited.
- **A3 — ID anchoring.** Prefer heading-path anchors over line numbers for stable
  IDs; excerpt-hash fallback (§7.2).
- **A4 — Edge kinds in v1.** Ship five, defer two (§8).
- **A5 — Config format (RFC OQ2).** Single repo-local file `psa.toml` (or
  `[tool.psa]` in `pyproject.toml`); adapter+rule config share it. Config hash
  feeds determinism.
- **A6 — Baseline location (RFC OQ5).** Committed in-repo at
  `.psa/baseline.json` by default; `--baseline` overrides for CI.
- **A7 — Cycle handling (RFC OQ6).** Report cycles and leave to the user (no
  silent break); roadmap emits the acyclic portion plus a flagged cycle set.

None of these change observable RFC behaviour; each is an internal mechanism or a
default for a question the RFC explicitly left open.

## 14. Out of scope for this ADR

Writing `SKILL.md`, writing production code, and resolving RFC open questions as
*contract* changes. Those follow sign-off. This ADR is complete when the module
boundaries, interfaces, serialization, CLI, and test strategy above are accepted
as the plan of record.

---

## 15. Definition of Done — Project v1

Phase-level "done" (§12) is a checkpoint, not the finish line. **The project
reaches v1 when all of the following hold:**

- [ ] All core rule packs implemented (`ORDERING`, `VOLATILITY`, `DUPLICATION`,
      `ACTIVATION`, `STYLE`, `OWNERSHIP`, `CONTRADICTION`)
- [ ] Discovery adapters implemented (Claude, AGENTS, Cursor rules, Copilot,
      OpenCode, generic prompts, templates, builders, memory, MCP — per RFC §5.3)
- [ ] Prompt Graph implemented (immutable segments + typed edges, RFC §6)
- [ ] Recommendation Graph implemented (dependencies + topological roadmap, §9.7)
- [ ] Audit lifecycle implemented (audit → baseline → improve → re-audit →
      compare, RFC §14)
- [ ] Baseline / diff implemented (resolved / introduced / unchanged, §14.3)
- [ ] Patch Preview implemented (mechanical, single-finding, RFC §12)
- [ ] Validation implemented (re-audit on scratch tree; invariant enforced)
- [ ] Apply implemented (branch + one commit + rollback)
- [ ] RFC examples reproduced (the illustrative outputs in RFC §8/§9/§14)
- [ ] Validation repositories pass (the three repos in `0001-validation.md`
      produce the expected findings, terminology-updated)
- [ ] Documentation complete (README, rule catalogue, config reference)
- [ ] `SKILL.md` complete (frontmatter + instructions, per repo authoring rules)
- [ ] CI running (deterministic audit + golden/snapshot/determinism/purity suites)
- [ ] Public release prepared (versioned, installable via `npx skills`)

Every item is objectively checkable; none depends on a fabricated metric. This is
the finish line contributors work toward.
