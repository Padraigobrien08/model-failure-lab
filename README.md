# Model Failure Lab

Model Failure Lab is a CLI-first system for structured LLM failure analysis.

It lets you run prompt datasets against a model, classify failures with simple heuristic logic,
save deterministic local artifacts, and compare runs without needing a database or extra
infrastructure.

## Quickstart

Use Python 3.11 or newer.

```bash
python3 -m pip install -e '.[dev]'
failure-lab demo
```

That zero-config demo runs the bundled deterministic dataset, writes normal artifacts, and prints a
compact summary.

If your shell does not expose the console script on `PATH`, use the module entrypoint instead:

```bash
python3 -m model_failure_lab demo
```

## What You Can Do

Run the built-in dataset discovery first:

```bash
failure-lab datasets list
```

Run one bundled dataset:

```bash
failure-lab run --dataset reasoning-failures-v1 --model demo
```

Build a report from a saved run:

```bash
failure-lab report --run <run-id>
```

Compare two runs directionally:

```bash
failure-lab compare <baseline-run-id> <candidate-run-id>
```

All commands also accept explicit paths and `--root` so you can keep datasets, runs, and reports in
an isolated workspace.

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

## Model Surface

`failure-lab run` supports:

- `demo` for deterministic local execution
- OpenAI model names such as `gpt-4.1-mini`
- explicit adapter routing with `<adapter>:<model>`

The package also exposes simple registration seams for future extension:

- `register_model(...)`
- `register_classifier(...)`

## Development Setup

Editable install:

```bash
python3 -m pip install -e '.[dev]'
```

Optional OpenAI adapter support:

```bash
python3 -m pip install -e '.[openai]'
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
