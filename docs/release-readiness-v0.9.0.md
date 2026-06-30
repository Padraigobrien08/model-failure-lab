# Release Readiness Checklist — v0.9.0

> ↩ Part of the release planning set. See [`docs/roadmap.md`](roadmap.md) for the prioritized roadmap, and [`docs/release-checklist.md`](release-checklist.md) for the actionable release steps.

> Checkpoint 2026-06-30, release targeted for tomorrow. Audited against the actual repo state.
> Legend: ✅ done · 🟡 done locally but **unpushed** (`oss-hardening` branch, 5 commits ahead of
> `origin/main`) · ☐ not done. Every ☐ item lists **why it matters / effort / risk**.
> Effort: S (<1h) · M (a few h) · L (a day+). Risk: Low / Med / High / **Critical**.

## ⚠️ Overarching blocker

Almost all release-quality work (new README, CI, P0 fixes, demo, docs) lives on the **unpushed
`oss-hardening` branch**. `origin/main` (commit `ac4b886`) is the *old* state: old README, no
`examples/`, no production CI, version `0.1.0`. **If you tag/release from `origin/main` tomorrow, the
release is the old project.** Treat "merge & push the branch" as item 0.

---

## 0. Release-blocking summary (do these or slip the date)

| # | Item | Effort | Risk |
|---|---|---|---|
| ☐ | Merge `oss-hardening` → `main` and push (see Branch strategy) | M | **Critical** |
| ☐ | Bump version `0.1.0` → `0.9.0` in **both** `pyproject.toml` and `src/model_failure_lab/__init__.py` | S | **Critical** |
| ☐ | Reconcile the `v1.0`–`v5.3` tags so `v0.9.0` is the visible "latest release" | M | **Critical** |
| ☐ | Replace placeholder contacts `security@`/`conduct@`/`maintainer@example.com` with real ones | S | High |
| ☐ | Write `CHANGELOG.md` with the `0.9.0` entry | M | High |
| ☐ | TestPyPI dry-run, then publish `0.9.0` to PyPI | M | High |
| ☐ | Create the GitHub Release for `v0.9.0` with notes | S | Med |

---

## 1. Packaging

- 🟡 `pyproject.toml` metadata complete (SPDX `License-Expression: MIT`, 3.11/3.12 classifiers, maintainer, URLs); `python -m build` + `twine check` pass *(on branch)*.
- ☐ **Bump version to `0.9.0` in both source-of-truth files.**
  - *Why:* `pyproject.toml:7` and `__init__.py:5` are both `0.1.0`; a release must declare `0.9.0` or PyPI and the package report the wrong number.
  - *Effort:* S · *Risk:* **Critical** (wrong version shipped is unfixable for that version number).
- ☐ **Collapse the dual version source** (derive `__version__` from package metadata, or have one canonical location).
  - *Why:* two hand-edited version strings drift; a future bump will update one and not the other.
  - *Effort:* S · *Risk:* Med.
- ☐ **`examples/` is not shipped in the wheel** (it's a top-level dir, not under `src/`).
  - *Why:* the README's flagship offline demo (`examples/regression_demo/`) is unavailable to `pip install` users — the documented first experience fails for them.
  - *Effort:* M (move under the package or expose via a `failure-lab demo` path; or document "clone for the demo"). · *Risk:* Med (first-impression failure for pip users).
- ☐ Add a `py.typed` marker.
  - *Why:* the package is heavily typed; without the marker downstream users get no types.
  - *Effort:* S · *Risk:* Low.

## 2. Semantic versioning

- ✅ SemVer policy stated (README "Project status" + `docs/release.md`).
- ☐ **Reconcile internal tags vs the public version.** 25 tags `v1.0`–`v5.3` exist; GitHub shows the highest semver (`v5.3`) as "latest release", which outranks and contradicts `v0.9.0`.
  - *Why:* visitors and tooling will treat `v5.3` as the current release; the announcement is undercut on arrival. (Strategy in `docs/release.md` / `docs/oss-readiness.md`.)
  - *Effort:* M (namespace under `internal/` or delete; **destructive — maintainer must confirm no external dependents**). · *Risk:* **Critical** to credibility; the tag deletion itself is Med-risk.
- ☐ **Justify the `0.1.0` → `0.9.0` jump.** Skipping `0.2`–`0.8` is legal in `0.x` but signals "near-1.0".
  - *Why:* users read `0.9.0` as feature-complete/RC; make sure API/CLI stability matches that promise, or pick a smaller bump.
  - *Effort:* S (a decision + a CHANGELOG note) · *Risk:* Med (expectation mismatch).
- ☐ State the pre-1.0 stability contract for `0.9` (what may still break before `1.0`).
  - *Why:* `0.9` implies few breaking changes remain; set expectations explicitly.
  - *Effort:* S · *Risk:* Low.

## 3. GitHub Releases

- ☐ **Create the `v0.9.0` Release** (none exists for any current tag).
  - *Why:* the Release page is where users land from "Releases"; without notes it looks unmaintained.
  - *Effort:* S · *Risk:* Med.
- ☐ Release notes drawn from the CHANGELOG; highlight the workflow + offline demo.
  - *Why:* notes are the human-readable "what's in it"; drives adoption.
  - *Effort:* S · *Risk:* Low.
- ☐ Ensure "latest release" resolves to `v0.9.0` (depends on tag reconciliation, §2).
  - *Why:* otherwise GitHub pins `v5.3`. · *Effort:* part of §2 · *Risk:* High.

## 4. PyPI

- ☐ **TestPyPI dry-run** (runbook in `docs/release.md`), then publish `0.9.0`.
  - *Why:* `0.1.0` is already on PyPI from old `main`; a per-version publish is irreversible, so verify install-from-TestPyPI first.
  - *Effort:* M · *Risk:* High (a bad first real publish of `0.9.0` can't be re-uploaded under the same version).
- ☐ Verify name ownership / that the published `0.1.0` is this project.
  - *Why:* README has no PyPI link; confirm you control the name before pushing `0.9.0`.
  - *Effort:* S · *Risk:* Med.
- ☐ Use **Trusted Publishing (OIDC)** or a scoped API token; never commit tokens.
  - *Why:* token leakage = supply-chain compromise; OIDC removes long-lived secrets.
  - *Effort:* M · *Risk:* High (security).
- 🟡 `twine check` passes; long description renders. *(Note: the README Mermaid diagram won't render on PyPI — cosmetic.)*

## 5. CI

- 🟡 `production.yml` (3.11/3.12: install `.[dev]`, `ruff check .`, `pytest -q`, import smoke) and `ci.yml` (legacy full suite) exist *(on branch)*.
- ☐ **Get CI running on `origin/main` + PRs** (it's only on the unpushed branch).
  - *Why:* until merged, no automated gate protects the release branch.
  - *Effort:* part of item 0 · *Risk:* **Critical**.
- ☐ Enable **branch protection** with `production` as a required check.
  - *Why:* with future contributors, unreviewed/red merges reach `main` and ship.
  - *Effort:* S (repo settings) · *Risk:* High.
- ☐ Add security CI: `pip-audit`, CodeQL, Dependabot.
  - *Why:* the dependency tree is unpinned (see `docs/security-audit.md` H2); nothing watches for vulnerable/breaking deps.
  - *Effort:* M · *Risk:* Med.

## 6. Release automation

- ✅ `Makefile` `build` / `verify-dist` / `publish` targets (manual, token-gated).
- ☐ **Tag-triggered publish workflow** (build → `twine check` → publish on `v*` tag).
  - *Why:* manual `make publish` from a laptop is error-prone and ties releases to one machine; automation makes them reproducible and OIDC-signable.
  - *Effort:* M · *Risk:* Med.
- ☐ Version-bump + changelog automation (e.g. release-please) — optional.
  - *Why:* removes the dual-file bump and manual changelog drift at scale.
  - *Effort:* M · *Risk:* Low (nice-to-have; don't block v0.9.0 on it).

## 7. Changelog

- ☐ **Create `CHANGELOG.md`** (Keep a Changelog) with a `0.9.0` section.
  - *Why:* there is none; users and the GitHub Release need a single authoritative "what changed". For a `0.9` it should also note the production/legacy split and any breaking CLI/artifact changes since `0.1.0`.
  - *Effort:* M · *Risk:* High (a release without notes erodes trust and hides breaking changes).

## 8. Branch strategy

- ☐ **Merge `oss-hardening` → `main` and push** (5 commits: docs, isolation/green tests, CI, P0 fixes, demo).
  - *Why:* the entire release lives here; `main` is otherwise the old project. This is the master blocker.
  - *Effort:* M · *Risk:* **Critical**.
- ☐ Document the branch model (main = releasable, feature branches, tags = releases).
  - *Why:* with many contributors, an undocumented model causes direct-to-main pushes and tag chaos (already visible in the `v1.x`–`v5.x` tags).
  - *Effort:* S · *Risk:* Med.
- ☐ Prune stale remote branches (`origin` has `v1.9-…`, `v2.0-…`, `v5.0-…`).
  - *Why:* clutter + confusion about what's current.
  - *Effort:* S · *Risk:* Low.

## 9. Contributor workflow

- 🟡 `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` exist *(on branch; the latter two carry placeholder contacts)*.
- ☐ **Replace placeholder contacts** (`security@example.com`, `conduct@example.com`, `maintainer@example.com`) with real, monitored addresses (or enable GitHub Security Advisories).
  - *Why:* a public release with `@example.com` security contact is both non-functional and an obvious credibility hit.
  - *Effort:* S · *Risk:* High.
- ☐ Add issue templates (bug/feature) + a PR template.
  - *Why:* a `0.9` release will attract issues; templates keep them triageable from day one.
  - *Effort:* M · *Risk:* Low.
- ☐ Fix `CONTRIBUTING.md` drift (`ruff check src tests` vs the workflow's `ruff check .`).
  - *Why:* contributors who follow it diverge from CI.
  - *Effort:* S · *Risk:* Low.
- ☐ Label a few "good first issues".
  - *Why:* converts release-day visitors into contributors.
  - *Effort:* S · *Risk:* Low.

## 10. Documentation completeness

- 🟡 README rewritten; broad `docs/` set present (overview, architecture, setup, api, dependencies, technical-debt, current-state, code-inventory, release, oss-readiness, adoption-strategy, security-audit, scalability) *(on branch)*.
- ☐ Add a `docs/README.md` index/map.
  - *Why:* ~15 docs with no entry point; newcomers can't navigate.
  - *Effort:* S · *Risk:* Low.
- ☐ Link `CHANGELOG.md` from the README and Release.
  - *Why:* discoverability of "what changed". · *Effort:* S · *Risk:* Low.
- ☐ Document (or fix) the "demo not in the pip wheel" gap for pip users (ties to Packaging §1).
  - *Why:* the documented quickstart fails for `pip install` users.
  - *Effort:* S (doc) / M (fix) · *Risk:* Med.

---

## Recommended day-of sequence
1. Replace placeholder contacts; write `CHANGELOG.md`; bump version to `0.9.0` (both files). *(commits)*
2. Merge `oss-hardening` → `main`; push; confirm `production` CI is green on `main`.
3. Reconcile tags (namespace/delete `v1.x`–`v5.x`); enable branch protection.
4. TestPyPI dry-run → verify install → publish `0.9.0` to PyPI (OIDC if possible).
5. Tag `v0.9.0`; create the GitHub Release with notes linked to the CHANGELOG.
6. Post-release: confirm `pip install model-failure-lab==0.9.0` works in a clean venv and `failure-lab --version` (once added) reports `0.9.0`.

## What's genuinely ready (no action)
- Packaging metadata + `build`/`twine check` (just needs the version bump).
- Production CI matrix + legacy/full split.
- Dependency-isolated production install; green production test suite.
- A real, offline, deterministic demo and a workflow-first README.
- A broad docs set including release runbook, security, and scalability reviews.

**Bottom line:** the *content* of a high-quality `0.9.0` exists, but it is **unshipped** — unpushed
branch, un-bumped version, no changelog, placeholder contacts, and tags that hide it. The blocking set
(§0) is ~half a day of work; do it before tagging.
