# OSS Readiness Audit — v0.1 Public Release

> Audit date 2026-06-29. Scope: discoverability, contributor experience, docs, packaging, branding,
> examples, API consistency, licensing, versioning, first-time UX. Implementation internals are out
> of scope except where they affect adoption. This is an audit + checklist; **no fixes are applied
> here.**

## Verdict

The supported product (the `run → report → compare` CLI) is solid: it installs, the offline `demo`
works, the production test suite is green, `twine check` passes, and MIT licensing is in place. But
the repository is **not yet safe to announce publicly** — primarily because of a **versioning/tag
conflict** (25 internal `v1.0`–`v5.3` tags vs. a `0.1.0` package) and **missing maintainer contact**
for security/conduct reports. Fix the P0 list first; the P1 list is what makes a first-time visitor
trust and adopt it.

Legend: ☐ todo · **P0** release blocker · **P1** do before announcing · **P2** polish.
Effort: S (<1h) · M (a few hours) · L (a day+).

---

## P0 — Release blockers

> **Status (P0 pass, 2026-06-29):** the in-repo portion of every P0 item has been addressed on the
> `oss-hardening` branch. Items that require a **human maintainer** (deleting/pushing tags, real
> contact addresses, an actual TestPyPI upload) are explicitly called out below and remain open.
> ✅ = done in-repo · ⏳ = requires maintainer action.

| State | Item | Area | Why it blocks |
|---|---|---|---|
| ⏳ | **Reconcile git tags with the public version.** Documented below + strategy in `docs/release.md`. Tags are **not** deleted by the audit; a maintainer must run the cleanup. | Versioning | A visitor seeing "v5.3 latest" + "0.1.0 on PyPI" loses trust immediately. |
| ✅/⏳ | **Security contact.** `SECURITY.md` rewritten with a reporting channel + `0.x` supported-versions policy. Uses placeholder `security@example.com` — ⏳ replace with a real channel / enable GitHub Security Advisories. | Governance | No private disclosure path is a hard no for public repos. |
| ✅/⏳ | **Code of Conduct contact.** `CODE_OF_CONDUCT.md` now has an enforcement contact. Uses placeholder `conduct@example.com` — ⏳ replace before release. | Contributor | Enforcement clause is unactionable without a contact. |
| ✅/⏳ | **PyPI packaging metadata.** `pyproject.toml` now advertises Python 3.12 and a maintainer; MIT is published as a PEP 639 `License-Expression` (see note below). Maintainer email is placeholder `maintainer@example.com` — ⏳ replace before release. | Packaging | These render on the PyPI page and affect search/filtering. |
| ✅/⏳ | **PyPI name + TestPyPI dry run.** Runbook added at `docs/release.md` (name-availability check, TestPyPI upload, verify-install). ⏳ The actual TestPyPI upload must be run by a maintainer with credentials. | Packaging | A failed/squatted first publish is painful to undo. |
| ✅ | **Broken screenshot references.** `README` had none; `docs/product-screens.md` image embeds replaced with text placeholders (no invented images). | Branding/Docs | Broken images read as abandonment. |

### Note: MIT license classifier vs. license expression

The original P0 item suggested adding a `License :: OSI Approved :: MIT License` **classifier**. That
was **not** done, intentionally: setuptools ≥77 (the build uses 82.0.1) **rejects** a license
classifier when a PEP 639 license expression is present — it fails `python -m build` with
`InvalidConfigError: License classifiers have been superseded by license expressions`. The package
already publishes `License-Expression: MIT` in its METADATA (which PyPI displays), so the adoption
goal — MIT clearly shown on PyPI — is met without the deprecated classifier.

### Version/tag conflict (detail)

The repo carries **25 internal milestone tags** competing with the intended `v0.1.0` public release:

```
v1.0 v1.1 v1.2 v1.3 v1.4 v1.5 v1.7 v1.8 v1.9 v2.1 v3.0
v4.0 v4.1 v4.2 v4.3 v4.4 v4.5 v4.6 v4.7 v4.8 v4.9
v5.0 v5.1 v5.2 v5.3            (created 2026-03-20 → 2026-04-06)
```

These are internal development-phase markers (cf. `.planning/v5.3-MILESTONE-AUDIT.md`), not public
releases. GitHub treats the highest semver tag (`v5.3`) as the "latest release," which contradicts a
`0.1.0` package and a v0.1 announcement. **The recommended cleanup (re-namespace under `internal/`,
or delete, then tag `v0.1.0`) and the rationale are in `docs/release.md`.** The audit does **not**
delete or move any tags — that is a destructive, history-affecting action reserved for a maintainer
who has confirmed no external clone/fork/CI depends on them.

---

## P1 — Strongly recommended before announcing

### Discoverability
| ☐ | Item | Effort |
|---|---|---|
| ☐ | Set the GitHub **repo description + topics** (e.g. `llm`, `rag`, `evaluation`, `regression-testing`, `prompt-engineering`, `cli`) — topics drive GitHub search. (Repo settings, not in-repo.) | S |
| ☐ | Add live **badges** to README: production CI status, and (post-publish) PyPI version + Python versions. Currently only static `python`/`license` shields. | S |
| ☐ | Add a **social preview image** (repo settings) so shared links render a card. | S |

### Contributor experience
| ☐ | Item | Effort |
|---|---|---|
| ☐ | Add **issue templates** (`.github/ISSUE_TEMPLATE/bug_report.yml`, `feature_request.yml`, `config.yml`) and a **PR template**. None exist today. | M |
| ☐ | Fix `CONTRIBUTING.md` drift: it says `ruff check src tests` but the production workflow uses `ruff check .`; reference the `make` targets, the `[dev]` vs `[legacy]` split, and how to run `make test-legacy`. | S |
| ☐ | Document the **branching/release flow** and a PR checklist (tests + lint + `failure-lab demo`). | S |
| ☐ | Label a few **"good first issue"** items to invite contributions. | S |

### Documentation quality
| ☐ | Item | Effort |
|---|---|---|
| ☐ | Add a **`CHANGELOG.md`** (Keep a Changelog format) with a `0.1.0` entry — the announcement should link to it. | M |
| ☐ | Add a short **docs index** (`docs/README.md`) — there are 20+ docs with no map for newcomers. | S |
| ☐ | Note that the README **Mermaid diagram won't render on PyPI**; consider a static image fallback in the PyPI long description. | S |

### Examples & first-time UX
| ☐ | Item | Effort |
|---|---|---|
| ☐ | Make the **quickstart fully offline.** Step 3 uses `ollama:llama3.2`, which needs a local Ollama install; a first-timer can't run `compare` without it. Show a zero-dependency `compare` using `--model demo` twice (works today), and present Ollama/API models as the next step. | S |
| ☐ | Add an **`examples/`** directory or a single annotated end-to-end walkthrough (run → report → compare → harvest → promote) a user can copy-paste. | M |
| ☐ | Add a **`.env.example`** (`ANTHROPIC_API_KEY=`, `OPENAI_API_KEY=`). `.gitignore` already whitelists it (`!.env.example`) but the file is missing, and the API adapters need these keys. | S |
| ☐ | Verify **missing-extra error messages** guide users (e.g. `--model anthropic:…` without the extra → a message telling them to `pip install '.[anthropic]'`). | S |

### API consistency
| ☐ | Item | Effort |
|---|---|---|
| ☐ | **Resolve the import-name footgun.** The distribution is `model-failure-lab`, the import is `model_failure_lab`, and the CLI is `failure-lab`/`model-failure-lab`. This already caused a wrong `import failure_lab` assumption. Document the canonical names prominently, and decide whether to ship a `failure_lab` import alias. | M |
| ☐ | Pick **one canonical CLI invocation** in all docs (recommend `failure-lab`) and present the others as alternatives. | S |
| ☐ | Frame the **command surface for newcomers**: 13 top-level commands + ~21 `dataset` subcommands is a lot for v0.1. Mark core (`run`/`report`/`compare`/`harvest`) vs advanced (governance/portfolio) in docs so the surface doesn't overwhelm. (Docs only — no removal.) | S |

---

## P2 — Polish / nice-to-have

| ☐ | Item | Area | Effort |
|---|---|---|---|
| ☐ | Add **`CITATION.cff`** — this is a research-adjacent eval tool; citation-friendliness helps academic adoption. | Branding | S |
| ☐ | Add **`py.typed`** marker so downstream users get the (extensive) type hints. | Packaging | S |
| ☐ | Add release/CI automation: **Dependabot**, **CodeQL**, and a tag-triggered **publish-to-PyPI** workflow (the `Makefile publish` target exists but isn't wired to CI). | Contributor | M |
| ☐ | Decide whether the **`dist/` build artifacts** should be committed at all (currently `0.1.0` wheel/sdist are in-tree and may go stale vs. the README). Prefer building in CI. | Packaging | S |
| ☐ | Add a **NOTICE / third-party acknowledgments** for the `[legacy]` stack (torch/transformers/wilds, all permissive) — optional but tidy. | Licensing | S |
| ☐ | Add a brief **roadmap / "what's not done"** section linking `docs/future-ideas.md`, and an FAQ / alternatives comparison. | Docs | M |
| ☐ | Consider a **logo / wordmark** for the README header. | Branding | M |
| ☐ | Optional **`.github/FUNDING.yml`** if sponsorship is desired. | Branding | S |

---

## What's already in good shape (no action)

- ✅ MIT `LICENSE` present (`docs/dependencies.md` confirms the optional ML deps are all permissive).
- ✅ Offline `failure-lab demo` gives a working first-run with zero external services (fast
  time-to-first-success).
- ✅ Production install is lean (`PyYAML` only); heavy/research deps are opt-in extras.
- ✅ `twine check dist/*` passes; the long description renders.
- ✅ Production CI (`production.yml`, 3.11/3.12) and a separate, non-required legacy suite exist.
- ✅ Baseline docs set (`overview`, `architecture`, `setup`, `api`, etc.) already written.

## Suggested sequencing

1. **Versioning + contacts + metadata** (P0 A–D) — the trust-critical, irreversible items.
2. **Kill broken images, fix CONTRIBUTING drift, offline quickstart, `.env.example`** — cheap, high-impact first-impression fixes.
3. **CHANGELOG + issue/PR templates + examples + badges** — the contributor/adopter on-ramp.
4. **Import-name decision + command-surface framing** — reduce first-use friction.
5. Tag `v0.1.0`, publish to PyPI, then announce.
