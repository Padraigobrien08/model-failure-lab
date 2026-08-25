# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Public OSS releases start
at `0.9.0` (see `docs/decisions/0003-public-versioning-starts-at-v0.9.0.md`); earlier `v1.0`–`v5.3`
git tags are internal development milestones, not public releases.

## [0.11.0] - 2026-08-25

A consumer-honesty release, from an external audit of `0.10.1`. Every change here is something a
reader, CLI user, or CI job could observe. Three carry **behavior changes** — see Changed.

`0.10.1` was never published to PyPI, so nobody is upgrading *from* it; the migration notes below
apply to anyone tracking `main` or the source tree.

### Fixed
- **The gate had three contracts, and the console could show PASS on a comparison that failed CI.**
  `compare --gate` blocked on five conditions (incompatible runs, regression verdict,
  execution-success drop, classification-coverage drop, dropped baseline failing cases);
  `regressions gate` and the operator console's `gate` endpoint blocked on the verdict alone. A
  candidate that simply deleted the cases it broke failed CI and showed a green PASS in the console.
  There is now one implementation, `governance.gates.evaluate_gate_conditions`, that every surface
  calls, and each gate decision carries a `block_reason` the console renders verbatim
  (`test_gate_surface_agreement.py`).
- **The gate screen always claimed "policy: built-in defaults · waivers: none."** The bridge's
  `gate` handler hand-picked its response fields and dropped `policy_source` / `waiver_source`, and
  the validator defaulted the absence rather than rejecting it — so the console denied a committed
  `governance/policy.yml` while displaying its values two rows below.
- **The console counted `error_stage_changed` as a regression; the engine does not.** A comparison
  whose only change was an error moving stage rendered a NEUTRAL banner and a green PASS directly
  above a red, regression-tinted transition group. The transition sets moved to
  `frontend/src/lib/artifacts/transitions.ts` and are pinned to the engine's constants from both
  sides (`tests/fixtures/contract/transitions.json`).
- **Red meant regression, except in five places.** The always-visible "contract issues" rail chip
  and four execution/write error boxes were red; DESIGN.md reserves red for regression and forbids
  it for validation. They are now amber. `expectationVerdictTone` tested for `"match"`/`"mismatch"`,
  values `schemas/taxonomy.py` has never emitted, so every expectation chip on the run detail
  rendered neutral and an `unexpected_failure` looked identical to a `no_failure_as_expected`.
- **`pip install model-failure-lab` gets `0.1.0`**, which predates `init`, `compare --gate`,
  `--html` and `openai-compat`. The README now leads with the clone install and says so, and
  `docs/release.md` records the real publish state instead of a `0.10.0` PyPI release that never
  existed.
- **The advertised GitHub Action could not install itself.** `action.yml` defaulted to
  `model-failure-lab>=0.10.1`, which pip cannot resolve, so `uses: …@main` failed for every
  consumer. It installs from its own checkout by default now, and CI dogfoods that path plus the
  failing exit code the README promises.
- **The README's "Real output" was spliced from two commands**, seven lines short, with re-padded
  driver rows and a `Top drivers:` section that `compare` does not print. It is now verbatim
  `compare --summary`, pinned by `test_documented_output_is_real.py`, as is
  `examples/regression_demo/expected_compare.txt` — committed as expected output and never checked.
- **Concurrent harvests overwrote each other**, each reporting a successful write. Output-name
  reservation is now atomic.
- **The dev-server bridge returned the absolute repo path and full argv** in 500 bodies. The detail
  goes to the server's stderr; the client gets a stable message.
- **`docs/api.md` had drifted**: `init`, `baselines` and `regressions pr-comment` shipped
  undocumented and the command counts were two releases stale. A test now walks the real argparse
  tree.
- `_optional_json_mapping` rejected top-level nulls in a dataset's `source`/`metadata` because it
  tested the mapping instead of the field, making an explicit "no comparison id" unloadable.
- CLI-harvested drafts recorded no `origin` / `comparison_report_id`, so the console's Datasets
  screen showed a blank source for them while console-created drafts showed both.
- `dataset review` was the only command in the loop without `--root`.
- The run-detail H1 overflowed its box and painted under the header actions on every real run id.
- Re-reading a run absent from the workspace raised a bare `No such file or directory`; it now
  explains that comparisons made from run paths outside a workspace record only the run id.
- Deleted `docs/product-screens.md`, which claimed no screenshots existed while sitting beside four
  and linked to a file removed months ago, and the tracked empty `frontend/.claude-launch-note`.

### Added
- **Dataset content digests.** `dataset promote` and `dataset evolve` stamp
  `metadata.integrity.content_digest` over a pack's id, version and ordered cases (excluding
  provenance, so re-stamping metadata is not tampering). `load_dataset` verifies it, so editing a
  promoted pack now fails at every consumer: `failure-lab run` exits 1 and `index validate` exits 1,
  naming the file and both digests. Previously a promoted pack could lose three of its four cases
  undetected while `index validate` reported `ok`.
- Runs record `metadata.dataset_content_digest`, so a run's artifact says which dataset *content* it
  executed. The run id's digest never covered that and still does not.
- `dataset promote --force`, `dataset review --root`.
- A golden bridge-payload contract (`tests/fixtures/bridge/`) pinned from both sides, closing the
  circularity that let the `gate` drift ship: the console's validators were tested only against
  fixtures written to match the validators.
- `upsert_baseline(now=…)`, matching the clock-injection seam every other artifact writer has.

### Changed
- **`dataset promote` refuses to overwrite an existing curated dataset.** It used to replace the
  version silently and exit 0, which is what made "immutable" a label rather than a guarantee.
  *Migration:* add new cases as the next version with `dataset evolve`, promote under a different
  `--dataset-id`, or pass `--force`.
- **`regressions gate` and the console `gate` endpoint now block on the same five conditions as
  `compare --gate`.** *Migration:* a job that passed while `compare --gate` failed on the same
  artifacts will now fail — that disagreement was the bug. Waive a known-acceptable comparison in
  `governance/waivers.yml`.
- **`action.yml` installs from the action's own checkout by default** (`package: ""`). *Migration:*
  pass `package: model-failure-lab==<version>` to pin a PyPI release instead.
- The console reads its version from `pyproject.toml` at build time; it was a hardcoded string that
  had already drifted. Screenshots in `docs/screens/` recaptured.

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
