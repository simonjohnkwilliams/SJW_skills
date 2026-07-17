# Required Tests

## Test 1 — Stable Prefix

Measure the percentage of context expected to remain identical between sessions.

Output:

- Stable prefix %
- Estimated reusable prefix

## Test 2 — Early Volatility

Detect volatile information appearing before stable project information.

Severity:

- Critical
- Warning
- Minor

Recommend moving the content later.

## Test 3 — Dynamic Value Detection

Search for:

- today
- current
- latest
- now
- timestamp
- date
- time
- sprint
- ticket
- branch
- release
- build
- session
- counter

## Test 4 — Retrieval Detection

Detect:

- Retrieved documentation
- Search results
- RAG snippets
- Temporary context
- Recently loaded information

Recommend placing these near the end.

## Test 5 — Agent State Detection

Identify:

- Current progress
- TODO lists
- Active task
- Conversation summaries
- Working memory

Flag early placement.

## Test 6 — Ordering Analysis

Validate the overall layout.

Preferred:

Stable → Stable → Stable → Volatile → Volatile

Poor:

Stable → Volatile → Stable → Volatile

## Test 7 — Cache Poison Detection

Highlight any volatile section located inside the first 30% of the prompt.

Include:

- section
- approximate location
- reason
- severity
- recommendation

## Test 8 — Duplicate Detection

Detect repeated:

- architecture
- standards
- conventions
- repeated instructions

Recommend consolidation where appropriate.
