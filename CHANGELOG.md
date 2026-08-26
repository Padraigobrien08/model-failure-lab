# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Public OSS releases start
at `0.9.0` (see `docs/decisions/0003-public-versioning-starts-at-v0.9.0.md`); earlier `v1.0`–`v5.3`
git tags are internal development milestones, not public releases.

## [0.13.0] - 2026-08-26

A third audit pass, this one re-run against the `0.12.0` remediation branch. Four of the
seven findings were defects that remediation introduced, and one is the worst kind this
project can have: **the `0.12.0` CHANGELOG claimed a fix that was never made.** Every fix
here is a predicate over the whole surface rather than a correction to one example — that
is what the previous round got wrong.

### Fixed
- **A waiver turned the console green and left CI red.** `regressions waive` wrote a waiver
  that `regressions gate` and the console honoured and `compare --gate` ignored — and
  `compare --gate` is what `action.yml` wraps and the README puts in CI. Following the
  console's own printed remedy produced a green gate screen over a red build. All three
  surfaces resolve waivers through `resolve_waiver` now, and `compare --gate` reports what it
  suppressed (`Gate: PASS (waived by padraig: …) [would block: …]`) rather than a bare PASS.
  An expired waiver is named, not silently ignored.
  `test_gate_surface_parity.py` asks all three the same question and compares their answers
  **to each other**, so a surface that grows an input nobody else reads fails there.
- **Six printed remedies did not run** — `harvest --report <comparison>` (missing `--out`),
  `dataset promote <draft>` in four places (missing `--dataset-id`), `run <dataset>`
  (positional where the CLI wants `--dataset`), `dataset evolve … --comparison` (the flag is
  `--from-comparison`), and `baselines set <name>` (`--name`). The `0.12.0` CHANGELOG said
  the first of those was fixed; the entry was written and the string never touched.
  `test_console_commands_are_runnable.py` now extracts every `failure-lab …` literal the
  console prints and parses it against the real argparse tree.
- **The legacy import error was wrong.** `reporting.__getattr__` turned any
  `ModuleNotFoundError` into "not shipped in the installed package", so a checkout missing
  the `[legacy]` extra — what `make install-dev` gives you — got a false message instead of
  `No module named 'matplotlib'`, and two scripts failed to import. It discriminates on
  `exc.name` now. The guarding test is deliberately **not** marked `legacy`: the bug only
  appears when the extra is absent, so a test that needs it is skipped exactly where the
  bug lives, which is how this shipped green.
- **The "shared" baseline registry was disposable.** It lived at
  `.failure_lab/baseline_registry.json` — the derived index directory, which `.gitignore`
  excludes and `make clean` deletes irrecoverably, since it is not derived. It is
  `governance/baselines.json` now, with a read-through so an existing workspace keeps its
  entries. `test_governance_state_is_durable.py` runs the governance surfaces and asserts
  nothing they wrote lands somewhere `make clean` removes.
- **`ExplorerPage` kept a private copy of the regression transition set**, through the
  consolidation that removed the other four — `transitions.test.ts` pins the module, not its
  use. A degrading *trend* also rendered red, where DESIGN.md assigns amber to degraded
  state, and two of that function's three substring branches (`worsen`, `rising`) matched
  nothing the engine emits. `consoleVocabulary.test.tsx` asserts the literals appear in
  exactly one non-test file.
- **`regressions waive <typo>` reported `Action: created`** and told you to re-check the
  gate, which stayed red. It warns when the id names no saved comparison, and still writes —
  waiving ahead of a rerun is legitimate.
- **`waived by null`** on the comparison detail, because `--owner` is optional and was
  interpolated unguarded.
- `baselines list` / `baselines set` accept `--root` where every other subcommand takes it.
  It was only on the parent parser, so the usual placement died on "unrecognized arguments".

### Added
- **The promotion ledger.** `metadata.integrity` catches an edit and `lifecycle: "curated"`
  catches deleting the stamp, but deleting *both* defeated them, and no witness kept inside
  the artifact can do better. `governance/promotions.json` records outside the pack that a
  dataset id was promoted and what its digest was, so a stripped pack is now a disagreement
  between two committed files. It also catches the re-stamp: editing the cases and
  recomputing the digest leaves a self-consistent pack that the ledger still contradicts.
- **A write token on the bridge.** The same-origin check trusts a request that sends neither
  `Origin` nor `Sec-Fetch-Site`, on the grounds that such a caller is the local developer —
  which stops being true under `--host`, where any machine on the network can curl a
  header-less POST at the three write endpoints. The server mints a token per start and
  injects it into the page; only something that loaded the page can read it.
- **CI builds and checks the sdist.** The README says the walkthrough "ships in the source
  tree (clone, or an unpacked sdist)", and the sdist is the only artifact that claim rests
  on. Nothing built it.

### Changed
- `build_parser` was 1,164 lines; it is 33, delegating to one `_add_*_parser` per command
  group. Pure code motion, verified by diffing the resolved argparse tree before and after.

## [0.12.0] - 2026-08-25

A second external-audit pass, this time through three lenses (a skim, a pre-merge review, and an
adversarial critique). Every finding here was reproduced by executing the tool, not by reading it.
Two carry **behavior changes** — see Changed.

### Fixed
- **Two screens gave opposite answers about the same comparison.** The comparison detail
  short-circuited an `incompatible` verdict to "CI gate: not evaluated" *before* it read its gate
  row — so the comparison that was the sole reason CI failed reported, on its own page, that the
  gate had not been evaluated on it. Meanwhile `ConsoleShell` painted the rail chip red on any
  block, so a fail-closed "runs are not comparable" showed a red FAIL badge 100px from an amber
  banner describing the same state. `frontend/src/lib/artifacts/gateTone.ts` is now the only place
  that decides, and `gateConsistency.test.tsx` asserts agreement across surfaces rather than
  correctness of one. "not evaluated" now means exactly one thing: this comparison is not in the
  gate's window.
- **"Immutable" had a one-line bypass.** Deleting `metadata.integrity` from a curated pack restored
  every pre-digest behavior: a pack with two of its four cases removed loaded silently and
  `index validate` reported ok. `lifecycle: "curated"` distinguishes the cases — only
  `dataset promote` and `dataset evolve` set it, and both stamp a digest — so a curated pack with a
  missing *or* wrong digest is now a reported finding, with the path and a re-stamp command.
- **The wheel shipped the legacy ML stack that `pyproject.toml` said it excluded.** The exclude list
  missed `utils`, `tracking`, `artifact_index` and `config`, and `reporting` was one package holding
  both surfaces, so setuptools could exclude it whole or not at all. Nineteen of the wheel's 94
  Python files imported torch / pandas / numpy / scikit-learn / matplotlib and raised ImportError
  for anyone who installed the package. The legacy reporting modules moved to `reporting.legacy`;
  the wheel is 67 files and `test_wheel_excludes_legacy.py` walks the built package set to keep it
  that way.
- **A deliberate 404 branch in the bridge was unreachable.** Both detail handlers classified by
  searching `bridgeErrorMessage`'s *return* value for "ENOENT", and that function always returns its
  sanitized fallback, so every missing run answered 500. A crafted artifact id answered 500 too,
  making a rejected path traversal indistinguishable from a crash; it is a 400 now, as is a
  malformed POST body.
- **The bridge answered requests addressed to any host.** It runs ahead of Vite's own
  `allowedHosts` check — it has to, or the SPA fallback claims `/__failure_lab__/*.json` — so an
  arbitrary `Host` was served, and a DNS-rebinding page reaching it on 127.0.0.1 is *genuinely*
  same-origin, which makes the CSRF check pass by construction. The bridge now checks for itself.
- **A nullable bridge payload was typed non-null**, so a legacy comparison artifact whose signal
  lives only in `report_details.json` would have thrown a TypeError instead of reaching the explicit
  fail-safe two lines below it. Found by turning on `strict` for the Node-side TypeScript.
- **A failed harvest left an orphan reservation.** The bridge reserves its output name with
  `O_CREAT|O_EXCL` so two console tabs cannot collide; a harvest that then failed left a zero-byte
  pack behind, which the drafts listing skips, so they accumulated invisibly and pushed each real
  harvest's name to `-2`, `-3`, `-4`.
- **The console printed a remedy that did not work.** The gate offered `--waivers waivers.yml`, a
  path nothing discovers, at a time when no command wrote a waiver at all. The Datasets empty state
  printed `failure-lab harvest --report <comparison>`, which is missing the required `--out`.
- **The comparison heading was a constant.** `Baseline → candidate` was hardcoded regardless of the
  run ids; it only looked right because the bundled demo's runs carry those names.
  `frontend/README.md` says the console never invents data.
- Dead references: the feature-request template linked `docs/roadmap.md` (absent), `MANIFEST.in`
  cited `docs/release-checklist.md` (it is `docs/release.md`), and `docs/code-map.md` pointed
  contributors at `ci.yml` rather than the workflow that gates the supported path.

### Added
- **`failure-lab regressions waive <comparison-id> --reason "…"`.** The gate blocks fail-closed and
  evaluates every recent comparison, so one accidental cross-dataset `compare` left it permanently
  red — with no command to delete, prune or dismiss a saved comparison, and no command to write a
  waiver either. It writes the file the gate discovers, sorted by comparison id; `--remove` drops
  one; an `--expires-at` in the past is refused at write time.
- **`run` says when a dataset targets a failure type the classifier cannot emit.** `heuristic_v1`
  emits four of the taxonomy's eight, and `rag-failures-v1` ships targeting `retrieval` — one of the
  four it cannot produce — so a run over it reported `hallucination` and `instruction_following`
  with nothing explaining why the type the dataset exists to find never appeared.
- **The dev-server bridge has tests.** It was 2,342 lines inside `vite.config.ts`, the largest file
  in the frontend and the only one no test could import. It is now `frontend/server/artifactBridge.ts`
  and `server/__tests__/artifactBridge.test.ts` drives it over real HTTP: 42 tests across the guards,
  the status codes, and the two payloads composed in TypeScript rather than by the engine.
- **A consumer-install CI job.** `production` installs with `pip install -e .[dev]`, which is not the
  path a user takes — and that difference has already shipped one packaging bug. CI now builds the
  wheel, asserts it ships no legacy module, installs it clean, and runs the README quickstart and
  `examples/regression_demo/run.sh`, the headline command that had never been executed in CI.
- A dark-theme screenshot, `docs/screens/gate-dark.png`. The console ships two committed themes and
  the docs only ever showed one.

### Changed
- **`index validate` exits `2`, not `1`, on a tampered dataset.** Two is its documented
  "contracts do not hold" code; the tampered pack used to escape the rebuild as an unhandled
  exception, which a CI script cannot distinguish from the command itself crashing.
- **`index validate` now fails on a curated pack carrying no content digest.** Packs promoted before
  digests existed are affected: confirm the cases are the ones you promoted, then re-stamp with
  `failure-lab dataset promote <path> --dataset-id <id> --force`. Loading such a pack still works —
  only the command whose job is answering "do my contracts hold" reports it.
- Importing a legacy reporting symbol from an installed wheel raises an `AttributeError` naming the
  surface and pointing at `docs/legacy.md`, instead of a bare `ModuleNotFoundError`.
- `npm run build` runs one typecheck instead of two; the two TypeScript projects are now one.
- `docs/ci-governance.md` rewritten. It described a CI smoke flow the workflow does not run, pointed
  policy and waivers at `.failure_lab/` (the derived index directory, which `.gitignore` excludes)
  while discovery looks in `governance/`, and predated `compare --gate` entirely.
- The README's comparison table drops the "Local?" column — promptfoo, DeepEval and Ragas are all
  local — and names the actual differentiator instead: the comparison refuses to score itself when
  the comparison is unsound. Its plain-English `run` row named "bad format", a failure type no
  classifier emits.

### Removed
- `scripts/sync_react_ui_manifest.py` and its test. They served the manifest the pre-console React
  debugger consumed; nothing in `frontend/` has read it since the rewrite.
- `frontend/components.json` (a shadcn config for a console with no shadcn components) and the
  unused `class-variance-authority` dependency.

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
