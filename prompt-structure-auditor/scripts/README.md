# psa — Prompt Structure Auditor (Core Engine)

Implements [RFC 0001](../../docs/rfc/0001-prompt-structure-auditor.md) per
[ADR 0001](../../docs/adr/0001-implementation-plan.md).

```bash
pip install -e ".[dev]"
pytest
python -m psa inventory PATH
python -m psa audit PATH
```
