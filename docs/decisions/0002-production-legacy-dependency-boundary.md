# 2. Production / legacy dependency boundary

- Status: Accepted
- Date: 2026-06-30

## Context

The repository contains two surfaces: the supported production workflow (`run → report → compare →
harvest → promote`) and a legacy DistilBERT/CivilComments research benchmark stack. The production
path needs only the standard library plus `PyYAML`; the legacy stack pulls heavy dependencies
(`torch`, `transformers`, `pandas`, `numpy`, `scikit-learn`, `wilds`, …). Previously these were
entangled enough that the full test suite could not run without the heavy stack, and a numpy/pandas
ABI mismatch broke installs.

## Decision

Keep a hard **dependency boundary** between the two surfaces:

- The production CLI must import **none** of the legacy ML dependencies at import time. This is
  enforced by a regression test (`tests/unit/test_production_cli_isolation.py`).
- The legacy stack is an **opt-in extra** (`pip install '.[legacy]'`), not part of the default
  install.
- The production test suite runs green without the legacy extra; legacy tests auto-skip when their
  dependencies are unavailable or broken.
- CI runs the production matrix (3.11/3.12, dev-only) separately from the legacy/full suite.

## Consequences

- `pip install model-failure-lab` stays small, fast, and low-risk; the large attack/maintenance
  surface is isolated.
- Contributors can develop and test the production path without installing the ML stack.
- The legacy stack is reference-only and a candidate for spin-out/removal (→
  Later / Explicitly Not Planned).
- Any new production code that needs a heavy dependency is a boundary violation and must instead live
  behind an extra or a plugin.
