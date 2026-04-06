# Phase 96 Context

## Goal

Prove the full governance loop from persisted comparison signal to deterministic recommendation to
applied dataset action over local artifacts.

## Locked Decisions

- Governance recommendations remain deterministic, local, and policy-driven.
- Debugger recommendation surfaces render backend-provided payloads instead of recomputing policy.
- Dataset-family actions remain explicit and inspectable before writes.
- Final verification must prove both CLI governance flow and debugger-facing governance payload
  availability over saved artifacts.

## Verification Focus

1. Fresh `compare` artifacts can flow directly into `regressions recommend`, `regressions review`,
   and `regressions apply`.
2. Repeated governance application remains stable and reproducible.
3. Debugger smoke over a real artifact root sees persisted governance recommendation payloads on
   signal and comparison-detail routes.
