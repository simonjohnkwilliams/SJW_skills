# SJW Skills

A repository of [Agent Skills](https://agentskills.io/specification) for Cursor and compatible agents.

Skills teach the agent how to perform specialized workflows. Each skill is a directory with a required `SKILL.md` (YAML frontmatter + instructions) and optional supporting files.

## Skills

| Skill | Definition |
|-------|------------|
| [cache-audit](./cache-audit/) | Audits prompt context for prompt-cache reuse and reports early volatility. |
| [prompt-structure-auditor](./prompt-structure-auditor/) | Deterministic prompt-architecture lint (inventory, audit, prioritise, ORDER001 preview). See [QUICKSTART](./prompt-structure-auditor/QUICKSTART.md). |

## Quickstart

Install skills the same way as other agent skill packs — with [`npx skills`](https://github.com/vercel-labs/skills), no full repo clone required.

**List available skills**

```bash
npx skills add simonjohnkwilliams/SJW_skills --list
```

**Install one skill into the current project (Cursor)**

```bash
npx skills add simonjohnkwilliams/SJW_skills --skill cache-audit -a cursor -y
```

**Install globally** (all your projects)

```bash
npx skills add simonjohnkwilliams/SJW_skills --skill cache-audit -g -a cursor -y
```

**Install every skill from this repo**

```bash
npx skills add simonjohnkwilliams/SJW_skills --skill '*' -a cursor -y
```

Requires Node.js. The CLI copies skills into `.cursor/skills/` (project) or `~/.cursor/skills/` (global with `-g`). Do not install into `~/.cursor/skills-cursor/` — that path is reserved for Cursor’s built-in skills.

Invoke a skill by mentioning it (for example `@cache-audit`) or asking for `/cache-audit`.

## Directory layout

```
SJW_skills/
├── README.md                 # This file
└── <skill-name>/             # One directory per skill
    ├── SKILL.md              # Required: metadata + instructions
    ├── scripts/              # Optional: executable helpers
    ├── references/           # Optional: docs loaded on demand
    └── assets/               # Optional: templates and static resources
```

This follows the [Agent Skills specification](https://agentskills.io/specification):

| Piece | Role |
|-------|------|
| `name` / `description` in frontmatter | Loaded at startup for discovery (~100 tokens) |
| `SKILL.md` body | Loaded when the skill is activated |
| `scripts/`, `references/`, `assets/` | Loaded only when needed |

The skill directory name must match the `name` field in frontmatter (lowercase letters, numbers, and hyphens only).

## Using skills in Cursor

### Project skills (shared with the repo)

Copy or symlink a skill into the consuming project:

```text
.cursor/skills/<skill-name>/SKILL.md
```

Anyone who clones that project gets the skill.

### Personal skills (all your projects)

Install under your user skills folder:

```text
~/.cursor/skills/<skill-name>/
```

### Invocation

- **Explicit:** mention the skill (for example `@cache-audit`) or ask for `/cache-audit`.
- **Automatic:** if the skill omits `disable-model-invocation`, the agent may activate it when the `description` matches the task.

## Authoring guidelines

When adding or editing a skill:

1. **Frontmatter** — required `name` and `description` (what it does **and** when to use it; third person; concrete trigger terms).
2. **Concise body** — keep `SKILL.md` under ~500 lines; put detail in `references/`.
3. **Progressive disclosure** — link one level deep from `SKILL.md` to reference files; avoid nested chains.
4. **Relative paths** — use paths from the skill root (`references/REPORT.md`, not Windows-style paths).
5. **Degrees of freedom** — tight scripts for fragile ops; templates for preferred patterns; prose when judgment is needed.
6. **Never rewrite automatically** unless the skill explicitly says to — prefer recommend-only workflows when auditing.

Validate frontmatter and naming with [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) when available:

```bash
skills-ref validate ./cache-audit
```

## References

- [Agent Skills specification](https://agentskills.io/specification)
- Cursor: Creating Skills (create-skill guidelines) — structure, descriptions, progressive disclosure, and anti-patterns
