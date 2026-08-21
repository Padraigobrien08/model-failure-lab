# Offline Regression Demo

A complete, **offline, deterministic** demonstration of the core workflow — no Ollama, OpenAI,
Anthropic, or network access required. It shows a model upgrade that *looks* fine but quietly breaks
4 of 8 cases, and how Model Failure Lab catches it and turns the regressions into a reusable dataset.

## Run it (one command)

```bash
bash examples/regression_demo/run.sh
```

Or step through it yourself from this directory:

```bash
cd examples/regression_demo

# 1. Compare the two model versions
failure-lab compare runs/baseline runs/candidate

# 2. Index the artifacts, then harvest the regressed cases into a dataset
failure-lab index rebuild
failure-lab harvest --comparison compare_8ba8496a_to_dda18a0e_66320e7c \
  --delta regression --out regression-pack.json
```

(`failure-lab` is the installed CLI; `python3 -m model_failure_lab` works too.)

## What you'll see

`compare` reports a real regression (full expected output is in
[`expected_compare.txt`](expected_compare.txt)):

```text
Status: regressed
Failure rate delta: +50.0%
Case changes: regressions=4
Top drivers:
- instruction_following +25.0% (regression) evidence=citation-latency, format-json
- hallucination        +12.5% (regression) evidence=grounding-warranty
- reasoning            +12.5% (regression) evidence=factual-apollo
```

`harvest` writes a 4-case `regression-pack.json` — the exact cases that broke, ready to keep as a
permanent test.

## What's in here

| Path | What it is |
|---|---|
| `dataset.json` | The 8-case demo dataset (a customer-support assistant). |
| `runs/baseline/` | Artifacts for **v1** of the assistant — all 8 cases pass. |
| `runs/candidate/` | Artifacts for **v2** — 4 cases regress. |
| `expected_compare.txt` | The deterministic, expected `compare` output (for reference/diffing). |
| `generate.py` | Regenerates the run artifacts deterministically (see below). |
| `run.sh` | Runs the whole compare → harvest flow. |

Generated files (`reports/`, `.failure_lab/`, `regression-pack.json`) are git-ignored.

## The four regressions (v1 → v2)

| Case | v1 (baseline) | v2 (candidate) | Detected as |
|---|---|---|---|
| `grounding-warranty` | grounded in the policy snippet | invents a "lifetime, covers everything" warranty | **hallucination** |
| `citation-latency` | cites `Smith 2021` | drops the citation | **instruction_following** (missing source) |
| `factual-apollo` | "1969" | "1971" | **reasoning** (factual error) |
| `format-json` | returns json | returns plain text | **instruction_following** (format) |

The other four cases (two grounded answers, one citation, and two control replies) are unchanged, so
the comparison shows a believable *partial* regression rather than everything breaking at once.

## How the artifacts are generated

`runs/baseline` and `runs/candidate` are produced by the real run pipeline, not hand-written. Two
in-script demo adapters return canned, deterministic answers (a correct "v1" and a regressed "v2"),
and the bundled `heuristic_v1` classifier labels them. Fixed seeds and timestamps make the output
byte-identical on every run. To regenerate:

```bash
python3 examples/regression_demo/generate.py
```

This is a documentation/demo helper only — it adds no product features.
