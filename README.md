# Model Failure Lab

![CI](https://github.com/Padraigobrien08/model-failure-lab/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Model Failure Lab is a local-first evaluation and failure-analysis toolkit for LLM and RAG systems.
It helps teams run prompt datasets, classify failures, compare model versions, and turn regressions
into reusable test cases.

## What It Is

Model Failure Lab focuses on one production loop:

`failure -> report -> compare -> harvest -> promote -> rerun`

The primary value is not only executing evals, but preserving deterministic artifact history so teams
can turn regressions into durable datasets and governance decisions.

## Quickstart

Use Python 3.11 or newer.

From a local clone:

```bash
git clone <repo-url>
cd model-failure-lab
python3 -m pip install .
failure-lab demo
```

Then run the canonical workflow:

```bash
failure-lab run --dataset reasoning-failures-v1 --model demo
failure-lab report --run <run-id>
failure-lab run --dataset reasoning-failures-v1 --model ollama:llama3.2
failure-lab compare <baseline-run-id> <candidate-run-id>
failure-lab harvest --comparison <comparison-id> --delta regression --out datasets/harvested/regression-pack.json
failure-lab dataset promote datasets/harvested/regression-pack.json --dataset-id reasoning-regressions-v1
failure-lab run --dataset reasoning-regressions-v1 --model demo
```

If your shell does not expose the console script on `PATH`, use:

```bash
python3 -m model_failure_lab demo
```

## Example Output

Prompt case:

```text
"What is 37 * 48?"
```

Run result:

- model output: incorrect
- failure type: reasoning_error
- classification confidence: high

Comparison summary:

- regression rate: +12%
- new failure clusters: arithmetic carry errors

## Core Workflow

`failure-lab` writes artifact folders under the active root (default: current working directory):

- `datasets/`
- `runs/`
- `reports/`

Comparison outputs are persisted as report artifacts under `reports/`.

Use `--root` on commands to target a specific workspace.

For detailed artifact contracts and examples, see `docs/artifact-model.md`.

## Model Adapters

`failure-lab run --model` supports:

- `demo` for deterministic local execution
- `ollama:<model>`
- `anthropic:<model>` (after installing optional dependencies)
- OpenAI model names (after installing optional dependencies)

Optional extras:

- `python3 -m pip install '.[anthropic]'`
- `python3 -m pip install '.[openai]'`
- `python3 -m pip install '.[dev]'`
- `python3 -m pip install '.[legacy]'` (legacy-only surfaces)
- `python3 -m pip install '.[ui]'` (legacy Streamlit UI)

If installing from a published distribution in the future, the equivalent form is
`model-failure-lab[anthropic]`, `model-failure-lab[openai]`, `model-failure-lab[legacy]`,
and `model-failure-lab[ui]`.

## React Debugger

The React debugger reads existing artifact workspaces via:

- `FAILURE_LAB_ARTIFACT_ROOT`

Example:

```bash
export FAILURE_LAB_ARTIFACT_ROOT=/path/to/failure-lab-workspace
npm --prefix frontend run dev
```

## Development

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest -q
python3 -m ruff check src tests
```

## Versioning

This project follows semantic versioning before `v1.0` in the practical sense:

- patch: bug fixes and docs
- minor: CLI-compatible feature additions
- breaking: CLI or artifact schema changes

## Legacy Surfaces

Legacy surfaces are retained for reference only and are not part of the supported production
workflow.

See:

- `docs/legacy.md`
- `docs/ui_parity.md`
- `docs/v1_4_closeout.md`

## Documentation

Detailed docs moved out of this README:

- Harvest replay: `docs/harvest-replay.md`
- Legacy surfaces: `docs/legacy.md`
- Fixture workspace: `docs/fixture-workspace.md`
- Artifact schema/model: `docs/artifact-model.md`
- Adapter extension guide: `docs/adapter-extension-guide.md`

## License

This project is licensed under the MIT License. See `LICENSE`.
