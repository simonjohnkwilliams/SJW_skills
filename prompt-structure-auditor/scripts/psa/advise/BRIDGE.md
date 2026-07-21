# Advise AI bridge — R5 spike decision

## Winner: Hybrid

| Priority | Source |
|----------|--------|
| 1 | `--judgment PATH` (explicit file) |
| 2 | `PSA_ADVISE_CMD` — command receives brief JSON on stdin, prints judgment JSON on stdout |
| 3 | `PSA_ADVISE_JUDGMENT` — path to judgment JSON, or inline JSON string |
| 4 | Non-tty stdin — judgment JSON piped in |

If none are available, `psa advise` exits 2:

`Advise requires an embedded AI caller.`

## Why hybrid

- **Skill path:** agent builds judgment from `--brief-only`, then calls `psa advise --judgment …`
- **Terminal path:** operator sets `PSA_ADVISE_CMD` or pipes judgment
- **CI:** fixture judgment file; no live model
- **No PSA-owned LLM API** — judgment always comes from the embedded caller

## Post-Apply

Apply never fails for missing Advise. If a bridge is available, Apply may attach one thematic line from judgment `summary_theme`. Otherwise the Advise line is omitted.
