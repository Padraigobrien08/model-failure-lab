# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Public OSS releases start
at `0.9.0` (see `docs/decisions/0003-public-versioning-starts-at-v0.9.0.md`); earlier `v1.0`–`v5.3`
git tags are internal development milestones, not public releases.

## [0.10.1] - 2026-08-24

Fixes shipped after `0.10.0`. This is the first release to include the dev-server bridge and
regression-gate hardening — anyone consuming `0.10.0` from PyPI or via the composite action should
upgrade. The composite action now defaults to installing `model-failure-lab==0.10.1`.

### Fixed
- Regression gate no longer masks genuine regressions. The comparison verdict now flips to
  `regression` on any net-new failing or erroring shared case, even when offsetting rate
  improvements make the net score positive; severity is floored at the case-regression fraction so a
  real regression can never round to a zero severity the minimum-severity floor would wave through
  (`reporting/signals.py`).
- Unified the gate contract across every surface. `compare --gate`, `regressions gate`, and the
  operator console `gate` endpoint now all block CI on any un-waived regression verdict; the
  minimum-severity floor governs only whether to create/evolve a dataset family, not whether CI turns
  green (`governance/gates.py`). Each gate decision now carries the signal `verdict`.
- Dev-server bridge and gate hardening: closed command/flag injection and path traversal on the
  bridge, added CSRF checks on the write endpoints, and made the gate fail closed on dropped baseline
  failing cases, execution-success drops, and incompatible comparisons.
- The operator console gate now resolves the same committed `governance/waivers.yml` and
  `governance/policy.{yml,yaml,json}` as the CLI, and surfaces which policy/waivers are in effect, so
  the console can no longer show a gate state that contradicts CI.
- `failure-lab index validate` now re-reads every source artifact through the strict contract checks
  instead of only confirming the derived index's tables exist.
- Baseline registry entries without a timestamp serialize as `null` rather than `""`, so one legacy
  row no longer crashes the console's baselines panel.
- Frontend contract validators fail safe instead of open: a missing comparison signal renders as an
  explicit `unknown` verdict (neutral tone, never green) rather than a fabricated `neutral`, and a
  malformed drivers block is rejected rather than silently dropped. Removed the duplicate TypeScript
  verdict computation in the bridge so verdict scoring has a single source of truth.

### Changed
- Composite action (`action.yml`) defaults `package` to `model-failure-lab==0.10.1` and passes inputs
  via environment variables instead of interpolating them into the shell.

### Docs
- Rewrote `docs/artifact-model.md` to match the actual artifact writers (field names, IDs, paths, and
  the `report_details.json` payloads), captured from a real run.

## [0.10.0] - 2026-08-23

The operator console release. Replaces the React debugger with a dense operator console for the full
local-first loop — run → compare → evidence → harvest → promote → gate — over the same deterministic
artifact contract.

### Added
- Operator console (`frontend/`): Runs inventory, Run detail, Comparison detail (verdict-first with a
  CI-gate banner), Evidence, Evidence explorer over the derived SQLite index, Datasets (immutable
  families plus drafts awaiting promotion), Gate (PASS/FAIL with policy, waivers, and baseline
  registry), and a harvest dialog with deterministic write receipts.
- Six read-only bridge endpoints (`dataset-families`, `dataset-drafts`, `gate`, `baselines`,
  `history`, `cluster-detail`) and per-run metrics on the run inventory.
- Typed, validating contract layer for every bridge payload; two committed themes behind a persisted
  toggle; self-hosted fonts so the console works fully offline.

### Changed
- Removed the legacy React debugger, its manifest stack, and all unrouted screens.
- Semantic color is enforced: red means regression only, green improvement only, amber degraded;
  incompatible comparisons render a neutral "not evaluated" gate rather than a false PASS.

## [0.9.0] - 2026-08-22

First public beta. Establishes the supported `run → report → compare → harvest → promote` workflow as
the product, with the optional research/ML stack quarantined behind extras.

### Added
- CI regression gate: `failure-lab compare --gate` exits non-zero on a regression verdict, and
  `--format markdown` renders a PR-comment-ready verdict table. A composite GitHub Action
  (`action.yml`) wraps both and writes the verdict to the job summary.
- Single-file HTML export: `report --html` and `compare --html` write a self-contained,
  deterministic HTML report (inline CSS, no JS, no external assets).
- `failure-lab init` scaffolds a runnable starter dataset (or imports prompts from JSONL with
  `--from-jsonl`) and prints the run → report → compare next steps.
- `openai-compat` adapter: `--model openai-compat:<model>` targets any OpenAI-compatible
  chat-completions server (vLLM, llama.cpp, LM Studio, Together, Groq, OpenRouter, …) with only
  the stdlib; bearer tokens come from `OPENAI_COMPAT_API_KEY` and are never persisted.
- React debugger screenshots (`docs/screens/`) captured from a real workspace, and a Visual
  debugger section in the README.
- Frontend CI job (vitest + typecheck + build) and a dogfooded regression-gate job in
  `production.yml`.
- `failure-lab --version` prints the installed package version.
- Offline, deterministic regression demo (`examples/regression_demo/`) showing a real regression
  caught and harvested — no Ollama/OpenAI/Anthropic/network required. The demo ships in the source
  tree and sdist; the offline single-run `failure-lab demo` command works from any install.
- Production CI workflow (Python 3.11 and 3.12, dev-only install) separate from the legacy/full suite.
- Regression guard ensuring the production CLI imports none of the legacy ML dependencies.
- User-facing documentation set under `docs/` (architecture, setup, API, artifact model,
  adapter extension guide, decisions/ADRs).
- Community health files: issue/PR templates, `.env.example`, and this changelog.

### Changed
- README rebuilt around the workflow ("catch LLM regressions before your users do") with a real
  regression as the flagship example.
- `pyproject.toml` metadata: advertise Python 3.12, add a maintainer field, publish MIT as a PEP 639
  license expression.
- Version set to `0.9.0` (public beta) in `pyproject.toml` and `src/model_failure_lab/__init__.py`.
- The production test suite runs green without the optional `[legacy]` ML stack installed; legacy
  tests auto-skip when their dependencies are unavailable.

### Notes
- Pre-1.0: CLI flags and artifact schemas may still change before `1.0.0`.

[0.10.1]: https://github.com/Padraigobrien08/model-failure-lab/releases/tag/v0.10.1
[0.10.0]: https://github.com/Padraigobrien08/model-failure-lab/releases/tag/v0.10.0
[0.9.0]: https://github.com/Padraigobrien08/model-failure-lab/releases/tag/v0.9.0
