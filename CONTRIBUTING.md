# Contributing

Thanks for contributing to Model Failure Lab.

## Development setup

```bash
python3 -m pip install -e '.[dev]'
```

## Before opening a PR

Run:

```bash
python3 -m pytest -q
python3 -m ruff check src tests
python3 -m pip install .
failure-lab demo
```

## Contribution expectations

- Keep changes focused and reviewable.
- Add or update tests for behavior changes.
- Update docs when CLI flows or artifact contracts change.
- Avoid breaking CLI flags and artifact schemas without documenting migration notes.
