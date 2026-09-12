# Contributing to D'AUBE // BRIDGE²

Thanks for helping make AI skills more portable.

## Good first contributions

- Add a provider compatibility fixture.
- Improve a generated adapter.
- Add a failing interoperability test for a real provider change.
- Improve quick-start documentation.
- Add an example skill that solves a concrete workflow.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest -q
daube-bridge compile examples/skill.yaml -o dist
```

## Pull requests

Keep PRs focused and include tests for behavior changes. For provider-format changes, link to authoritative documentation and avoid reverse-engineered or undocumented claims.

Generated artifacts should remain deterministic, readable, and free of secrets.
