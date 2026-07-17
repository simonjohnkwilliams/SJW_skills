---
name: cache-audit
description: >-
  Audits prompt context for prompt-cache reuse by classifying stable vs volatile
  content, detecting early volatility and cache-poisoning patterns, and producing
  an actionable Cache Audit Report. Use when the user runs /cache-audit, asks to
  audit prompt cache friendliness, or reviews CLAUDE.md, project instructions,
  workspace rules, agent memories, or MCP instructions for cache structure.
disable-model-invocation: true
---

# Cache Audit

Analyse the prompt context available to the agent and report how well it is
structured for prompt cache reuse.

**Goal:** maximise the reusable stable prefix by identifying volatile content
that appears too early. Do **not** optimise for minimum token count.

**Hard rule:** never rewrite files automatically; only recommend changes.

## Core principle

Prompt caches reuse the prompt from the beginning until the first change.

- Stable information should appear first.
- Frequently changing information should appear last.

Preferred order: Stable → Stable → Stable → Volatile → Volatile

Poor order: Stable → Volatile → Stable → Volatile

## Workflow

Copy this checklist and track progress:

```
Cache Audit Progress:
- [ ] 1. Inventory context sources
- [ ] 2. Classify stable vs volatile
- [ ] 3. Run required tests (1–8)
- [ ] 4. Score
- [ ] 5. Write Cache Audit Report
```

### 1. Inventory context sources

Inspect every source available in this session, including where present:

- CLAUDE.md
- Project instructions
- System prompt
- Repository instructions
- Agent memories
- Workspace rules
- MCP instructions
- Any persistent prompt fragments
- Additional injected context

Do not speculate beyond available prompt context. If confidence is low, say so.

### 2. Classify content

Use the rules in [references/classification.md](references/classification.md).

### 3. Run required tests

Run all eight tests in [references/tests.md](references/tests.md):

1. Stable Prefix
2. Early Volatility
3. Dynamic Value Detection
4. Retrieval Detection
5. Agent State Detection
6. Ordering Analysis
7. Cache Poison Detection
8. Duplicate Detection

### 4. Score

Produce:

- Overall Cache Score (0–100)
- Stable Prefix %
- Estimated Cache Friendliness
- Risk Level: Excellent | Good | Moderate | Poor

### 5. Report

Output using the exact structure in [references/report-format.md](references/report-format.md).

Every recommendation must explain **why** it improves cache reuse.

## Success criteria

The report must let a developer answer:

- Is my prompt cache friendly?
- Where does cache reuse stop?
- Which sections are reducing cache reuse?
- What changes should I make first?
- Which recommendations will have the biggest impact?
