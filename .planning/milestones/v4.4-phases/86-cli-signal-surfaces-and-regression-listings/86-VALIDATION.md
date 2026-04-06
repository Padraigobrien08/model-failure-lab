# Phase 86 Validation

- `failure-lab compare A B --score` emits raw signal JSON with verdict, scores, and top drivers.
- `failure-lab compare A B --summary` emits deterministic human-readable signal output with
  evidence-linked case ids.
- `failure-lab compare A B --alert` emits for directional signals above threshold and stays silent
  for neutral comparisons.
- `failure-lab regressions --direction <...>` lists saved comparison signal rows ordered by
  severity from the query index mirror.
