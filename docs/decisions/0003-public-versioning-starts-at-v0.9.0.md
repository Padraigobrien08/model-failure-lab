# 3. Public versioning starts at v0.9.0

- Status: Accepted
- Date: 2026-06-30

## Context

The repository carries 25 git tags (`v1.0` through `v5.3`, created during March–April 2026). These are
**internal development-phase milestones**, not public releases. GitHub treats the highest semantic
tag (`v5.3`) as the "latest release", which conflicts with a first public release and confuses new
visitors. The package version was `0.1.0`, and the first public beta is planned as `0.9.0`.

## Decision

- The **first public release is `v0.9.0`**, framed as a public beta. Pre-1.0 semantics apply: CLI
  flags and artifact schemas may still change before `1.0.0`.
- The existing `v1.0`–`v5.3` tags are **not public releases**. They will be re-namespaced (e.g. under
  `internal/`) or removed so `v0.9.0` is the visible latest release. Tag cleanup is a deliberate,
  destructive maintainer action — it is **not** performed automatically and only after confirming no
  external clone/fork/CI depends on them (see `docs/release.md`, `docs/release-checklist.md`).
- The `0.1.0` → `0.9.0` jump is intentional: it signals "near-1.0 / feature-complete beta" rather than
  an early prototype. `1.0.0` will mark the stability commitment for the CLI and artifact schema.

## Consequences

- New users see a single coherent release (`v0.9.0`) on PyPI and GitHub.
- The CHANGELOG starts at `0.9.0`; earlier internal milestones are not documented as releases.
- The version string must be updated in both `pyproject.toml` and `src/model_failure_lab/__init__.py`
  at release time (tracked in `docs/release-checklist.md`); collapsing to a single source is a Later
  item in `docs/roadmap.md`.
