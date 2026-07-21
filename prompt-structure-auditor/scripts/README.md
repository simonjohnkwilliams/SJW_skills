# psa — Prompt Structure Auditor (Core Engine)

Implements [RFC 0001](../../docs/rfc/0001-prompt-structure-auditor.md) per
[ADR 0001](../../docs/adr/0001-implementation-plan.md).

```bash
pip install -e ".[dev]"
pytest
python -m psa audit PATH
python -m psa plan PATH
python -m psa preview PATH
python -m psa preview --step 1 PATH
python -m psa apply --step 1 PATH
python -m psa apply --dangerous PATH
python -m psa doctor PATH
python -m psa baseline save PATH --out .psa-baseline.json
python -m psa diff PATH --baseline .psa-baseline.json --fail-on-introduced
```

CI: repo workflow `.github/workflows/psa.yml` (pytest + CLI smoke).
Full release matrix (fixtures + live IdeaProjects when present):

```bash
pytest tests/acceptance/test_releases_r1_r6.py -v -s
```

See `../QUICKSTART.md` and `../MANUAL_TEST.md`.
