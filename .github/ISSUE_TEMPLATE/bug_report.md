---
name: Bug report
about: Report something that doesn't work as documented
title: "[bug] "
labels: bug
assignees: ''
---

## What happened

A clear description of the bug.

## Steps to reproduce

```bash
# the exact commands you ran (prefer the demo or a minimal dataset)
failure-lab ...
```

## Expected behavior

What you expected to happen.

## Actual behavior

What actually happened (paste output/errors; redact any secrets or prompt contents).

## Environment

- Model Failure Lab version: <!-- pip show model-failure-lab | grep Version -->
- Install method: <!-- pip / clone + make install -->
- Python version: <!-- python --version -->
- OS:
- Model/adapter: <!-- demo / ollama:... / anthropic:... / openai -->

## Scope

- [ ] This involves the production CLI (`run`/`report`/`compare`/`harvest`).
- [ ] This involves the optional `[legacy]` ML stack.

## Anything else

Logs, screenshots, or context. If reproducible with the bundled `failure-lab demo` or
`examples/regression_demo/`, please say so — it speeds up triage.
