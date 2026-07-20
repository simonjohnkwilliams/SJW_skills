---
name: prompt-structure-auditor
description: >-
  Audits the repository prompt-construction surface (CLAUDE.md, AGENTS.md,
  Cursor rules, and related sources) for structural issues: ordering, volatility,
  duplication, activation metadata, and style. Produces evidence-backed findings
  with no fabricated cache scores. Use when the user runs /prompt-structure-auditor,
  asks to audit prompt structure, or reviews agent instruction files for
  maintainability and cache friendliness.
disable-model-invocation: true
---

# Prompt Structure Auditor

Deterministic static analysis of the prompt surface. Follow the RFC honesty rules:
report only observables; label inference; never invent cache hit rates or cost savings.

## Commands

From `scripts/`:

```bash
pip install -e ".[dev]"
python -m psa inventory .
python -m psa audit .
python -m psa audit . --format json
```

## Workflow

1. Run inventory / audit (read-only).
2. Review findings (priority ⊥ verification).
3. Apply changes manually or via future patch mode.
4. Re-audit and compare.

Do **not** rewrite files unless the user explicitly asks for patch apply mode.
