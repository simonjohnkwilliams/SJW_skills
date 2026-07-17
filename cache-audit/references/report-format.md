# Report Format

Use this structure (adapt numbers and findings to the audit):

```text
Cache Audit Report

Overall Score
92 / 100

Stable Prefix
91%

Risk
LOW

Findings

✓ Architecture first

✓ Standards first

⚠ Current sprint appears early

⚠ Current date appears before architecture

Recommendations

1. Move current sprint below project standards.

2. Move timestamps to the end of the prompt.

3. Keep all dynamic information together.

Expected outcome

Longer reusable cache prefix.

Higher cache hit ratio.

Lower effective inference cost.
```

## Scoring fields to include

- Overall Cache Score (0–100)
- Stable Prefix %
- Estimated Cache Friendliness
- Risk Level (map Excellent / Good / Moderate / Poor to a clear Risk line such as LOW / MODERATE / HIGH as appropriate)

## Recommendation rules

- Every recommendation must explain **why** it improves cache reuse.
- Never rewrite files automatically; only recommend changes.
- Do not speculate beyond the available prompt context. If confidence is low, state that clearly.
