# Roadmap

> Converts the existing audits (`docs/oss-readiness.md`, `docs/release-readiness-v0.9.0.md`,
> `docs/adoption-strategy.md`, `docs/roadmap` strategy, `docs/failure-pre-mortem.md`,
> `docs/security-audit.md`, `docs/scalability-review.md`) into tracked work. Items are planning only —
> no features are implemented here.
>
> **Owner type:** maintainer (code/docs/git) · contributor (community-friendly) · external setting
> (GitHub/PyPI settings, off-repo). **Priority:** P0 (blocks release) · P1 (soon) · P2 (opportunistic).

## v0.9.0 Public Beta

Goal: make the project installable, trustworthy, and CI-gateable. Mostly release hygiene, not features.

| Item | User value | Owner | Priority | Acceptance criteria |
|---|---|---|---|---|
| Merge the release branch to `main` and push | Users get the documented project, not the old `main` | maintainer | P0 | `origin/main` contains the new README, `examples/`, CI; `production` workflow green on `main` |
| Bump version `0.1.0` → `0.9.0` | Correct version on PyPI / `--version` | maintainer | P0 | `pyproject.toml` and `src/model_failure_lab/__init__.py` both read `0.9.0`; `python -m build` shows `0.9.0` |
| Reconcile internal tags vs the public version | "Latest release" shows `v0.9.0`, not `v5.3` | maintainer | P0 | `v1.0`–`v5.3` namespaced/removed per `docs/release.md`; `v0.9.0` is the latest release tag |
| Replace placeholder contacts | Working security/conduct/maintainer channels | maintainer | P0 | No `@example.com` in `SECURITY.md`, `CODE_OF_CONDUCT.md`, `pyproject.toml`; GitHub Security Advisories enabled |
| `CHANGELOG.md` with a `0.9.0` entry | Users see what changed and what may break | contributor | P1 | `CHANGELOG.md` present, Keep-a-Changelog format, linked from README + release notes |
| Ship the offline demo for `pip` users | First-run "aha" without cloning | maintainer | P1 | `pip install` then `failure-lab demo` shows a real regression, **or** README clearly scopes the demo to clones |
| 15s terminal GIF / screenshot in README | Top-of-funnel conversion; visual proof | maintainer | P1 | A GIF of run→compare(regression)→harvest at the top of the README; no broken image refs |
| Pin/bound dependencies + split legacy | Reproducible, non-flaky installs | maintainer | P1 | Runtime deps have version bounds; `[legacy]` heavy stack is opt-in only; clean-venv install verified |
| CI on `main` + PRs, branch protection | Red/unreviewed code can't reach a release | external setting | P1 | `production` required check on `main`; PRs must pass before merge |
| TestPyPI dry-run → publish `0.9.0` | Users can `pip install model-failure-lab==0.9.0` | maintainer | P0 | Install-from-TestPyPI verified; `0.9.0` live on PyPI (see `docs/release-checklist.md`) |
| GitHub Release with notes | A credible Releases page | maintainer | P1 | `v0.9.0` Release published with notes linking the CHANGELOG |

## v1.0.0 Stable

Goal: make the wedge (local, git-native regression CI) undeniable and open the ecosystem. Features here
are **planned**, not built in this doc.

| Item | User value | Owner | Priority | Acceptance criteria |
|---|---|---|---|---|
| API/CLI + artifact-schema stability commitment | Users can depend on it without churn | maintainer | P0 | Documented stability policy; breaking changes gated behind majors |
| `compare --exit-code` (+ `--json`) | Gate CI on regressions — the core promise | maintainer | P1 | `compare` returns nonzero on a regression verdict; `--json` machine output documented and tested |
| GitHub Action + pytest plugin | Automated regression gate where engineers work | maintainer | P1 | An Action runs `compare` and comments the regression on a PR; a pytest plugin fails on regression |
| Plugin system (entry points: adapters + scorers) | Use your own provider/check without forking core | maintainer | P1 | Third-party packages register adapters/scorers via `importlib.metadata` entry points; documented |
| Pluggable scorer interface (exact/regex/JSON-schema/BYO judge) | Trust: *you* define what "failure" means | maintainer | P1 | A documented scorer contract + built-ins; the heuristic becomes one scorer among several |
| CLI consolidation (per `docs/` design review) | Lower learning curve and contributor friction | maintainer | P2 | Plural/singular twins merged; deep `dataset` verbs nested; global `--root/--json`; `--version` |
| Release automation (tag-triggered publish, OIDC) | Reproducible, signed releases | external setting | P1 | Pushing a `v*` tag builds, `twine check`s, and publishes via Trusted Publishing |
| `py.typed` + single-source version | Typed downstream use; no version drift | contributor | P2 | `py.typed` shipped; version defined once |

## Later

Build only when real usage demands it — do not pre-build.

| Item | User value | Owner | Priority | Acceptance criteria |
|---|---|---|---|---|
| Incremental indexing + cheap freshness check | Fast analytics at scale | maintainer | P2 | Gated on adopters >~10k runs (`docs/scalability-review.md`); rebuild becomes O(Δ); freshness check O(1) |
| Local, read-only artifact viewer (package the React debugger) | Visual regression diffs | maintainer | P2 | Local-only, read-only viewer over an artifact root; no service, no account |
| Curated first-party plugins (common providers/scorers) | Convenience for the 80% case | contributor | P2 | Built on the v1.0 plugin API; live outside core |
| Release provenance: signing + SBOM | Supply-chain trust for regulated adopters | external setting | P2 | PEP 740 attestations; published SBOM |
| Trim or graduate the governance/portfolio surface | Less complexity, or a real feature | maintainer | P2 | Decision driven by usage evidence; unused surface removed or polished |

## Explicitly Not Planned

Saying no protects the wedge and the maintainer. These are out of scope.

| Item | Why not |
|---|---|
| Hosted SaaS / cloud dashboard / accounts / telemetry backend | Contradicts the local, no-account wedge; LangSmith's space; unsustainable maintenance |
| Large built-in model-graded metric library | Lose-lose vs DeepEval/Ragas; instead interop via the plugin/scorer API |
| Red-teaming / jailbreak / safety-attack suite | promptfoo's turf; scope explosion |
| Training / fine-tuning / the legacy DistilBERT–WILDS benchmark as a product | Off-mission; spin out or archive |
| Agent framework / prompt IDE / prompt management UI | Each is its own product and a maintenance sink |
| Production monitoring / tracing / observability | Different product and a 24/7 reliability commitment |
| Multi-modal (image/audio/video) eval | Scope creep before text regression is won |
| Rust/Go rewrite or replacing SQLite with a server DB | Premature; the bottleneck is the rebuild model, not the language/store |
| Plugin marketplace / GUI installer | Premature ecosystem machinery |
