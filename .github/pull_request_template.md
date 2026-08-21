## What this changes

A short description of the change and the problem it solves. Link any related issue (`Closes #...`).

## Type of change

- [ ] Bug fix
- [ ] Documentation
- [ ] Feature (please confirm it fits `docs/roadmap.md` scope)
- [ ] Refactor / internal
- [ ] Breaking change (CLI flags or artifact schema)

## Checklist

Run the same checks CI runs (see `.github/workflows/production.yml` / `CONTRIBUTING.md`):

- [ ] `ruff check .` passes
- [ ] `pytest -q` passes
- [ ] `python -c "import model_failure_lab"` succeeds
- [ ] Tests added or updated for behavior changes
- [ ] Docs updated when CLI flows or artifact contracts change
- [ ] No new dependency added to the production install path without discussion
- [ ] Breaking CLI/artifact changes are called out above with migration notes

## Notes for reviewers

Anything that needs special attention (trade-offs, follow-ups, out-of-scope deferrals).
