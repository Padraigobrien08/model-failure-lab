# Model Failure Lab

Model Failure Lab is a CLI-first system for structured LLM failure analysis.

It lets you run prompt datasets against a model, classify failures with simple heuristic logic,
save deterministic local artifacts, and compare runs without needing a database or extra
infrastructure.

## Quickstart

Use Python 3.11 or newer.

```bash
python3 -m pip install .
failure-lab demo
failure-lab run --dataset reasoning-failures-v1 --model demo
failure-lab report --run <run-id>
failure-lab compare <baseline-run-id> <candidate-run-id>
```

Use the Run ID from `failure-lab demo` as `<baseline-run-id>` and the Run ID from the bundled
`run` command as `<candidate-run-id>` in the later commands.

That standard install path exercises the real `failure-lab` console script: the demo writes a
bundled dataset snapshot plus one run and report, the bundled `run` command gives you a second run
to inspect, `report` rebuilds summaries from saved artifacts, and `compare` writes a saved
comparison artifact for those two run IDs. Because the demo dataset and the reasoning dataset are
different, that final quickstart comparison is expected to report `incompatible_dataset` while
still writing the comparison files; rerun `failure-lab run` against the same dataset twice when
you want a fully compatible comparison.

By default, `failure-lab` writes `datasets/`, `runs/`, and `reports/` under your current working
directory. Pass `--root /path/to/workspace` when you want the artifacts somewhere else.

If your shell does not expose the console script on `PATH`, use the module entrypoint instead:

```bash
python3 -m model_failure_lab demo
```

## What You Can Do

List bundled datasets shipped with the installed package:

```bash
failure-lab datasets list
```

All commands accept explicit paths and `--root` as well, so you can keep datasets, runs, and
reports in an isolated workspace instead of the current directory.

## Optional Extras

The base install above is enough for the shipped artifact-backed engine loop:

- bundled datasets
- `failure-lab demo`
- `failure-lab run`
- `failure-lab report`
- `failure-lab compare`
- local Ollama routing such as `--model ollama:llama3.2`

Install extras only when you need those optional surfaces from a repo checkout:

| Need | Install |
|------|---------|
| OpenAI adapter support | `python3 -m pip install '.[openai]'` |
| Legacy benchmark, training, and old reporting surfaces | `python3 -m pip install '.[legacy]'` |
| Legacy Streamlit results explorer | `python3 -m pip install '.[ui]'` |
| Test and lint tools | `python3 -m pip install '.[dev]'` |

If you are installing from a built wheel or published distribution instead of a local checkout, the
equivalent package form is `model-failure-lab[openai]`, `model-failure-lab[legacy]`, or
`model-failure-lab[ui]`.

## Bundled Datasets

The repo currently ships bundled packs for:

- `reasoning-failures-v1`
- `hallucination-failures-v1`
- `rag-failures-v1`

Bundled datasets default to the `core` slice for fast local runs. Use `--full` to include the
extended tail:

```bash
failure-lab run --dataset rag-failures-v1 --model demo --full
```

## Artifact Model

The engine writes simple filesystem artifacts:

```text
datasets/
runs/<run-id>/
  run.json
  results.json
reports/<report-id>/
  report.json
  report_details.json
```

The main contracts are:

- `PromptCase`
- `Run`
- `Result`
- `Report`

Everything stays inspectable by hand. There is no database layer.

## React Debugger Handoff

The React debugger reads an existing artifact workspace through one supported seam:
`FAILURE_LAB_ARTIFACT_ROOT`.

Point it at the directory that contains `runs/`, `reports/`, and optional `datasets/`:

```bash
export FAILURE_LAB_ARTIFACT_ROOT=/path/to/failure-lab-workspace
npm --prefix frontend run dev
```

That contract is the same whether the artifacts were written from this repo checkout, from a normal
installed-package workflow, or from an Ollama-backed run. The debugger does not have an in-app
artifact-root picker; the server-side environment variable is the supported handoff.

## Model Surface

`failure-lab run` supports:

- `demo` for deterministic local execution
- OpenAI model names such as `gpt-4.1-mini` after installing `.[openai]`
- Ollama models through explicit routing such as `ollama:llama3.2`
- explicit adapter routing with `<adapter>:<model>`

One explicit local Ollama example:

```bash
failure-lab run \
  --dataset reasoning-failures-v1 \
  --model ollama:llama3.2 \
  --ollama-host http://localhost:11434 \
  --system-prompt "Be concise." \
  --model-option temperature=0
```

That same surface supports the normal saved-artifact loop:

```bash
failure-lab run --dataset reasoning-failures-v1 --model ollama:baseline-model --ollama-host http://localhost:11434 --system-prompt "Be concise." --model-option temperature=0
failure-lab run --dataset reasoning-failures-v1 --model ollama:candidate-model --ollama-host http://localhost:11434 --system-prompt "Be concise." --model-option temperature=0
failure-lab report --run <baseline-run-id>
failure-lab compare <baseline-run-id> <candidate-run-id>
```

The package also exposes simple registration seams for future extension:

- `register_model(...)`
- `register_classifier(...)`

## Development Setup

Editable install:

```bash
python3 -m pip install -e '.[dev]'
```

Add extras as needed from a checkout:

```bash
python3 -m pip install -e '.[openai]'
python3 -m pip install -e '.[ui]'
python3 -m pip install -e '.[legacy]'
```

If you need the old benchmark and research surfaces while developing, install both dev tooling and
the legacy runtime stack together:

```bash
python3 -m pip install -e '.[dev,legacy]'
```

Focused checks:

```bash
python3 -m pytest -q
python3 -m ruff check src tests
```

## Legacy Benchmark And UI Surfaces

This repo still contains the earlier benchmark and UI work that focused on CivilComments,
distribution shift, and the React failure debugger. That material remains useful as legacy
reference, but the current product direction is the engine-first `failure-lab` workflow above.

Useful legacy references:

- [v1.4 closeout](docs/v1_4_closeout.md)
- [UI parity guide](docs/ui_parity.md)
- [Runtime setup reference](docs/runtime-setup.md)
- [Cloud GPU run guide](docs/cloud-gpu-run.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Configuration layout](configs/README.md)
