"""Regenerate the deterministic regression-demo artifacts.

This script (re)creates the committed `runs/baseline` and `runs/candidate`
artifacts from `dataset.json`. It is fully offline and deterministic: it uses two
in-script demo adapters (a "v1" assistant that answers correctly and a "v2"
assistant that regresses on four cases) plus the bundled heuristic classifier.

It does NOT add a product feature — it only writes example artifacts using the
real run pipeline so the regular `failure-lab compare` / `harvest` commands can
operate on them. Re-running it must produce byte-identical artifacts.

Usage:
    python examples/regression_demo/generate.py
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from model_failure_lab.adapters import ModelResult, register_model
from model_failure_lab.adapters.contracts import ModelMetadata
from model_failure_lab.datasets import load_dataset
from model_failure_lab.runner.artifacts import write_run_artifacts
from model_failure_lab.runner.execute import execute_dataset_run

BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "runs"
RUN_SEED = 7

# Baseline ("v1"): every answer satisfies the case expectation -> no failures.
BASELINE_OUTPUTS = {
    "Using the policy snippet, how long is the standard warranty?": (
        "Per the policy snippet, the standard warranty lasts 24 months from purchase."
    ),
    "Using the policy snippet, how long do refunds take?": (
        "Per the policy snippet, refunds are issued within 14 days of approval."
    ),
    "Summarize the latency finding and cite the source.": (
        "Median latency dropped 30% after the rollout (Smith 2021)."
    ),
    "Summarize the uptime finding and cite the source.": (
        "Uptime improved to 99.95% over the quarter (Lee 2020)."
    ),
    "What year did Apollo 11 land on the Moon?": "Apollo 11 landed on the Moon in 1969.",
    "Return the order status as json.": 'Here is the order status as json: {"status": "shipped"}.',
    "Write a brief, polite greeting for a support reply.": (
        "Hello, and thanks for reaching out to support."
    ),
    "Write a brief, polite closing for a support reply.": (
        "Thanks again, and please let us know if anything else comes up."
    ),
}

# Candidate ("v2"): four believable regressions, four unchanged answers.
CANDIDATE_OUTPUTS = dict(BASELINE_OUTPUTS)
CANDIDATE_OUTPUTS.update(
    {
        # Hallucination: invents an unsupported, ungrounded warranty claim.
        "Using the policy snippet, how long is the standard warranty?": (
            "The warranty lasts a lifetime and covers absolutely everything, no exceptions."
        ),
        # Dropped citation: omits the required source.
        "Summarize the latency finding and cite the source.": (
            "Median latency dropped 30% after the rollout."
        ),
        # Factual mistake: wrong year.
        "What year did Apollo 11 land on the Moon?": "Apollo 11 landed on the Moon in 1971.",
        # Format regression: ignores the json constraint.
        "Return the order status as json.": "Here is the order status: it has shipped.",
    }
)


def _make_adapter(table: dict[str, str]):
    class _TableAdapter:
        def generate(self, request):
            return ModelResult(
                text=table[request.prompt],
                metadata=ModelMetadata(model=request.model, latency_ms=0.0),
            )

    return lambda: _TableAdapter()


def _register(adapter_id: str, table: dict[str, str]) -> None:
    try:
        register_model(adapter_id, _make_adapter(table))
    except ValueError:
        pass  # already registered in this interpreter


def _write_run(adapter_id: str, model: str, when: datetime, run_id: str) -> None:
    execution = execute_dataset_run(
        dataset=load_dataset(BASE_DIR / "dataset.json"),
        adapter_id=adapter_id,
        classifier_id="heuristic_v1",
        model=model,
        run_seed=RUN_SEED,
        now=when,
    )
    staging = BASE_DIR / "_staging"
    shutil.rmtree(staging, ignore_errors=True)
    run_path, results_path = write_run_artifacts(execution, root=staging)

    # Normalize the timestamped run_id to a stable, readable id and relocate to
    # runs/<run_id>/ so `compare runs/baseline runs/candidate` works.
    generated_id = execution.run.run_id
    dest = RUNS_DIR / run_id
    dest.mkdir(parents=True, exist_ok=True)
    for src, name in ((run_path, "run.json"), (results_path, "results.json")):
        (dest / name).write_text(src.read_text(encoding="utf-8").replace(generated_id, run_id))
    shutil.rmtree(staging, ignore_errors=True)


def main() -> None:
    shutil.rmtree(RUNS_DIR, ignore_errors=True)
    _register("demo-baseline", BASELINE_OUTPUTS)
    _register("demo-candidate", CANDIDATE_OUTPUTS)
    # Fixed timestamps keep run ids (and therefore the comparison id) stable.
    _write_run("demo-baseline", "support-assistant-v1", datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "baseline")
    _write_run("demo-candidate", "support-assistant-v2", datetime(2026, 1, 1, 0, 1, 0, tzinfo=timezone.utc), "candidate")
    print(f"Wrote {RUNS_DIR}/baseline and {RUNS_DIR}/candidate")


if __name__ == "__main__":
    main()
