# 1. Local-first, file-based artifacts

- Status: Accepted
- Date: 2026-06-30

## Context

Model Failure Lab evaluates LLM/RAG systems and compares versions over time. Comparable tools split
between hosted platforms (state lives in a cloud service) and local libraries. The project's wedge is
**local, git-native regression testing**: results should live next to the code, be diffable in review,
and require no account or network to get started.

## Decision

Persist all primary state as **plain JSON artifacts on the local filesystem**, under the current
working directory (overridable with `--root`):

- `datasets/`, `runs/`, `reports/`, `governance/` hold canonical artifacts.
- A derived SQLite index (`.failure_lab/`) is a rebuildable projection over those artifacts, never the
  source of truth.

Artifacts are deterministic (stable IDs, sorted keys) so they diff cleanly and reproduce exactly.

## Consequences

- Users can commit evaluation history to git, review regressions in PRs, and run fully offline (the
  `demo` model needs no key or network).
- No server to operate, no account, no data leaving the machine.
- The artifact format is a public contract — schema changes are breaking and must be versioned.
- Cross-run analytics depend on the derived index, which is rebuildable from the JSON; at very large
  scale the rebuild model becomes the bottleneck (tracked in `docs/scalability-review.md`), not the
  storage choice itself.
- Artifacts may contain prompt/response content in plaintext; users must avoid putting secrets in
  prompts (noted in `docs/security-audit.md`).
