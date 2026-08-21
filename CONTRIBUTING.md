# Contributing

Thanks for contributing to Model Failure Lab.

## Development setup

```bash
python -m pip install -e .[dev]
```

## Before opening a PR

Run exactly what CI runs (`.github/workflows/production.yml`, Python 3.11 and 3.12):

```bash
ruff check .
pytest -q
python -c "import model_failure_lab"
```

Optional sanity check of the offline workflow:

```bash
failure-lab demo
```

The optional `[legacy]` ML tests are not part of the production suite; they auto-skip unless that
stack is installed. To run them: `python -m pip install -e .[dev,legacy]` then `make test-legacy`.

## Contribution expectations

- Keep changes focused and reviewable.
- Add or update tests for behavior changes.
- Update docs when CLI flows or artifact contracts change.
- Avoid breaking CLI flags and artifact schemas without documenting migration notes.
- New features should fit the supported `run -> report -> compare -> harvest` workflow; prefer plugins/extension points over core.
