"""Generate deterministic multi-run artifacts for query and insight testing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from model_failure_lab.adapters import (
    ModelMetadata,
    ModelRequest,
    ModelResult,
    register_model,
)
from model_failure_lab.classifiers import (
    ClassifierInput,
    ClassifierResult,
    register_classifier,
)
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.index import (
    QueryIndexSummary,
    ensure_query_index,
    list_comparison_inventory,
    list_run_inventory,
    query_index_path,
    rebuild_query_index,
)
from model_failure_lab.reporting import (
    build_comparison_report,
    build_run_report,
    build_run_report_id,
    load_saved_run_artifacts,
    write_comparison_report_artifacts,
    write_report_artifacts,
)
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import (
    JsonValue,
    PromptCase,
    PromptContextExpectations,
    PromptExpectations,
)
from model_failure_lab.storage import dataset_file, write_json

FIXTURE_ADAPTER_ID = "insight_fixture_v1"
FIXTURE_CLASSIFIER_ID = "insight_fixture_classifier_v1"
FIXTURE_DATASET_ID = "insight-fixture-v1"

_FIXTURE_PROMPT_TOKENS = {
    "alpha_1": "fixture alpha 1",
    "alpha_2": "fixture alpha 2",
    "beta_1": "fixture beta 1",
    "beta_2": "fixture beta 2",
    "gamma_1": "fixture gamma 1",
    "gamma_2": "fixture gamma 2",
    "delta_1": "fixture delta 1",
    "delta_2": "fixture delta 2",
}

_FIXTURE_BEHAVIORS: dict[str, dict[str, tuple[str, str]]] = {
    "baseline-model": {
        "alpha_1": (
            "hallucination",
            "According to a study, the bridge hums because hidden copper currents resonate.",
        ),
        "alpha_2": (
            "hallucination",
            "According to a study, winter leaves ring like metal because frost hardens them.",
        ),
        "beta_1": ("reasoning", "Return code: red square."),
        "beta_2": ("reasoning", "Return code: amber diamond."),
        "gamma_1": ("instruction_following", "step 2"),
        "gamma_2": ("instruction_following", "source: spec-note"),
        "delta_1": ("no_failure", "source excerpt audit log: grounded summary only."),
        "delta_2": ("no_failure", "Grounded support reply with no invented details."),
    },
    "candidate-model": {
        "alpha_1": ("no_failure", "Grounded answer: maintenance resonance from the provided note."),
        "alpha_2": (
            "hallucination",
            "According to a study, winter leaves ring like metal because frost hardens them.",
        ),
        "beta_1": ("instruction_following", "I checked the request but skipped the exact code."),
        "beta_2": ("no_failure", "green circle"),
        "gamma_1": ("no_failure", "step 1\nstep 2"),
        "gamma_2": ("instruction_following", "source: runbook"),
        "delta_1": (
            "hallucination",
            "According to a study, the audit log proves the service will fail next quarter.",
        ),
        "delta_2": ("no_failure", "Grounded support reply with no invented details."),
    },
    "noisy-model": {
        "alpha_1": (
            "hallucination",
            "According to a study, the bridge hums because hidden copper currents resonate.",
        ),
        "alpha_2": (
            "hallucination",
            "According to a study, winter leaves ring like metal because frost hardens them.",
        ),
        "beta_1": ("reasoning", "Return code: black triangle."),
        "beta_2": ("reasoning", "Return code: silver circle."),
        "gamma_1": ("instruction_following", "step 2"),
        "gamma_2": ("instruction_following", "source: runbook"),
        "delta_1": (
            "hallucination",
            "According to a study, the audit log proves the service will fail next quarter.",
        ),
        "delta_2": (
            "hallucination",
            "According to a study, support tickets double whenever this workflow appears.",
        ),
    },
    "stable-model": {
        "alpha_1": ("no_failure", "Grounded answer: maintenance resonance from the provided note."),
        "alpha_2": ("no_failure", "Grounded answer: the note gives no support for the metal claim."),
        "beta_1": ("no_failure", "blue triangle"),
        "beta_2": ("no_failure", "green circle"),
        "gamma_1": ("no_failure", "step 1\nstep 2"),
        "gamma_2": ("no_failure", "source: spec-note\nsource: runbook"),
        "delta_1": ("no_failure", "source excerpt audit log: grounded summary only."),
        "delta_2": ("no_failure", "Grounded support reply with no invented details."),
    },
}

_RUN_SPECS = (
    ("baseline-model", datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc)),
    ("candidate-model", datetime(2026, 4, 2, 9, 10, tzinfo=timezone.utc)),
    ("noisy-model", datetime(2026, 4, 2, 9, 20, tzinfo=timezone.utc)),
    ("stable-model", datetime(2026, 4, 2, 9, 30, tzinfo=timezone.utc)),
)

_COMPARISON_MODEL_PAIRS = (
    ("baseline-model", "candidate-model"),
    ("candidate-model", "noisy-model"),
    ("baseline-model", "stable-model"),
)


@dataclass(slots=True, frozen=True)
class InsightFixtureRun:
    model: str
    run_id: str
    report_id: str
    created_at: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "model": self.model,
            "run_id": self.run_id,
            "report_id": self.report_id,
            "created_at": self.created_at,
        }


@dataclass(slots=True, frozen=True)
class InsightFixtureComparison:
    baseline_model: str
    candidate_model: str
    report_id: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "baseline_model": self.baseline_model,
            "candidate_model": self.candidate_model,
            "report_id": self.report_id,
        }


@dataclass(slots=True, frozen=True)
class InsightFixtureWorkspace:
    root: Path
    dataset_id: str
    dataset_path: Path
    runs: tuple[InsightFixtureRun, ...]
    comparisons: tuple[InsightFixtureComparison, ...]
    query_index: QueryIndexSummary

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "root": str(self.root),
            "dataset_id": self.dataset_id,
            "dataset_path": str(self.dataset_path),
            "runs": [run.to_payload() for run in self.runs],
            "comparisons": [comparison.to_payload() for comparison in self.comparisons],
            "query_index": {
                "path": str(self.query_index.path),
                "run_count": self.query_index.run_count,
                "case_count": self.query_index.case_count,
                "comparison_count": self.query_index.comparison_count,
                "case_delta_count": self.query_index.case_delta_count,
                "rebuilt": self.query_index.rebuilt,
            },
        }


class InsightFixtureAdapter:
    """Deterministic adapter that emits labeled outcomes per prompt and model."""

    def generate(self, request: ModelRequest) -> ModelResult:
        scenario = _scenario_key(request.prompt)
        try:
            failure_type, response = _FIXTURE_BEHAVIORS[request.model][scenario]
        except KeyError as exc:
            raise ValueError(
                f"unsupported fixture behavior for model={request.model!r}, scenario={scenario!r}"
            ) from exc
        return ModelResult(
            text=f"{failure_type}::{response}",
            metadata=ModelMetadata(
                model=request.model,
                latency_ms=0.0,
                raw={
                    "fixture_adapter": FIXTURE_ADAPTER_ID,
                    "scenario": scenario,
                    "failure_type": failure_type,
                },
            ),
        )


class InsightFixtureClassifier:
    """Read deterministic failure labels back out of fixture adapter outputs."""

    def __call__(self, classifier_input: ClassifierInput) -> ClassifierResult:
        text = classifier_input.output.text
        if text.startswith("hallucination::"):
            return ClassifierResult(
                failure_type="hallucination",
                confidence=0.93,
                explanation="Fixture output uses unsupported factual framing.",
            )
        if text.startswith("reasoning::"):
            return ClassifierResult(
                failure_type="reasoning",
                confidence=0.88,
                explanation="Fixture output misses the authored reference answer.",
            )
        if text.startswith("instruction_following::"):
            return ClassifierResult(
                failure_type="instruction_following",
                confidence=0.84,
                explanation="Fixture output misses a required constraint or source.",
            )
        return ClassifierResult(
            failure_type="no_failure",
            confidence=0.22,
            explanation="Fixture output stays within the authored expectations.",
        )


def build_insight_fixture_dataset() -> FailureDataset:
    return FailureDataset(
        dataset_id=FIXTURE_DATASET_ID,
        name="Insight Fixture Cases",
        description=(
            "Deterministic cases for query, summarize, compare, and debugger insight workflows."
        ),
        version="1",
        metadata={
            "purpose": "deterministic_insight_fixture",
            "recommended_scope": "cross_run_analysis",
        },
        cases=(
            PromptCase(
                id="case-alpha-001",
                prompt="Fixture alpha 1. According to a study, explain why the bridge hums at sunset.",
                tags=("cluster-alpha", "hallucination", "core"),
                expectations=PromptExpectations(
                    expected_failure="hallucination",
                    rubric=("Avoid unsupported factual framing.",),
                ),
            ),
            PromptCase(
                id="case-alpha-002",
                prompt="Fixture alpha 2. According to a study, explain why leaves ring like metal in winter.",
                tags=("cluster-alpha", "hallucination", "core"),
                expectations=PromptExpectations(
                    expected_failure="hallucination",
                    rubric=("Avoid unsupported factual framing.",),
                ),
            ),
            PromptCase(
                id="case-beta-001",
                prompt="Fixture beta 1. Return only the hidden validation code BLUE TRIANGLE.",
                tags=("cluster-beta", "reasoning", "core"),
                expectations=PromptExpectations(
                    expected_failure="reasoning",
                    reference_answer="blue triangle",
                ),
            ),
            PromptCase(
                id="case-beta-002",
                prompt="Fixture beta 2. Return only the hidden validation code GREEN CIRCLE.",
                tags=("cluster-beta", "reasoning", "core"),
                expectations=PromptExpectations(
                    expected_failure="reasoning",
                    reference_answer="green circle",
                ),
            ),
            PromptCase(
                id="case-gamma-001",
                prompt="Fixture gamma 1. Provide only step 1 followed by step 2.",
                tags=("cluster-gamma", "instruction", "core"),
                expectations=PromptExpectations(
                    expected_failure="instruction_following",
                    constraints=("step 1", "step 2"),
                ),
            ),
            PromptCase(
                id="case-gamma-002",
                prompt="Fixture gamma 2. Cite both source: spec-note and source: runbook.",
                tags=("cluster-gamma", "instruction", "core"),
                expectations=PromptExpectations(
                    expected_failure="instruction_following",
                    context=PromptContextExpectations(
                        required_sources=("spec-note", "runbook")
                    ),
                ),
            ),
            PromptCase(
                id="case-delta-001",
                prompt="Fixture delta 1. Summarize the excerpt using source excerpt and audit log only.",
                tags=("cluster-delta", "grounded", "core"),
                expectations=PromptExpectations(
                    expected_failure="no_failure",
                    context=PromptContextExpectations(
                        evidence_items=("source excerpt", "audit log")
                    ),
                ),
            ),
            PromptCase(
                id="case-delta-002",
                prompt="Fixture delta 2. Draft a grounded support reply with no invented details.",
                tags=("cluster-delta", "grounded", "core"),
                expectations=PromptExpectations(
                    expected_failure="no_failure",
                    rubric=("Remain grounded and concise.",),
                ),
            ),
        ),
    )


def materialize_insight_fixture(
    root: str | Path,
    *,
    reuse_existing: bool = False,
) -> InsightFixtureWorkspace:
    artifact_root = Path(root).resolve()
    if artifact_root.exists() and any(artifact_root.iterdir()):
        if reuse_existing and _is_existing_fixture_root(artifact_root):
            return load_existing_insight_fixture(artifact_root)
        _assert_safe_empty_root(artifact_root)
    _ensure_fixture_registry()

    dataset = build_insight_fixture_dataset()
    dataset_path = dataset_file(dataset.dataset_id, root=artifact_root, create=True)
    write_json(dataset_path, dataset.to_payload())

    run_artifacts: list[InsightFixtureRun] = []
    saved_runs_by_model = {}
    for model, run_time in _RUN_SPECS:
        execution = execute_dataset_run(
            dataset=dataset,
            adapter_id=FIXTURE_ADAPTER_ID,
            classifier_id=FIXTURE_CLASSIFIER_ID,
            model=model,
            run_seed=13,
            now=run_time,
        )
        write_run_artifacts(execution, root=artifact_root)
        saved_run = load_saved_run_artifacts(execution.run.run_id, root=artifact_root)
        saved_runs_by_model[model] = saved_run
        built_report = build_run_report(saved_run, now=run_time + timedelta(seconds=45))
        write_report_artifacts(built_report.report, built_report.details, root=artifact_root)
        run_artifacts.append(
            InsightFixtureRun(
                model=model,
                run_id=execution.run.run_id,
                report_id=built_report.report.report_id,
                created_at=execution.run.created_at,
            )
        )

    comparison_artifacts: list[InsightFixtureComparison] = []
    for index, (baseline_model, candidate_model) in enumerate(_COMPARISON_MODEL_PAIRS, start=1):
        comparison_time = _RUN_SPECS[-1][1] + timedelta(minutes=index)
        built_comparison = build_comparison_report(
            saved_runs_by_model[baseline_model],
            saved_runs_by_model[candidate_model],
            now=comparison_time,
        )
        write_comparison_report_artifacts(
            built_comparison.report,
            built_comparison.details,
            root=artifact_root,
        )
        comparison_artifacts.append(
            InsightFixtureComparison(
                baseline_model=baseline_model,
                candidate_model=candidate_model,
                report_id=built_comparison.report.report_id,
            )
        )

    query_index = rebuild_query_index(root=artifact_root)
    expected_index_path = query_index_path(root=artifact_root)
    if query_index.path != expected_index_path:
        raise RuntimeError("rebuilt query index path did not match the expected fixture root")

    return InsightFixtureWorkspace(
        root=artifact_root,
        dataset_id=dataset.dataset_id,
        dataset_path=dataset_path,
        runs=tuple(run_artifacts),
        comparisons=tuple(comparison_artifacts),
        query_index=query_index,
    )


def load_existing_insight_fixture(root: str | Path) -> InsightFixtureWorkspace:
    artifact_root = Path(root).resolve()
    dataset = build_insight_fixture_dataset()
    dataset_path = dataset_file(dataset.dataset_id, root=artifact_root, create=False)
    if not dataset_path.exists():
        raise FileNotFoundError(f"fixture dataset snapshot is missing: {dataset_path}")

    model_order = {model: index for index, (model, _) in enumerate(_RUN_SPECS)}
    run_inventory = list_run_inventory(root=artifact_root)
    runs_by_model = {
        row["model"]: InsightFixtureRun(
            model=row["model"],
            run_id=row["run_id"],
            report_id=build_run_report_id(row["run_id"]),
            created_at=row["created_at"],
        )
        for row in run_inventory
        if row["model"] in model_order
    }

    comparison_inventory = list_comparison_inventory(root=artifact_root)
    run_models_by_id = {row["run_id"]: row["model"] for row in run_inventory}
    pair_order = {
        pair: index for index, pair in enumerate(_COMPARISON_MODEL_PAIRS)
    }
    comparisons = sorted(
        (
            InsightFixtureComparison(
                baseline_model=run_models_by_id[row["baseline_run_id"]],
                candidate_model=run_models_by_id[row["candidate_run_id"]],
                report_id=row["report_id"],
            )
            for row in comparison_inventory
            if row["baseline_run_id"] in run_models_by_id
            and row["candidate_run_id"] in run_models_by_id
        ),
        key=lambda comparison: pair_order[
            (comparison.baseline_model, comparison.candidate_model)
        ],
    )
    query_index = ensure_query_index(root=artifact_root)
    return InsightFixtureWorkspace(
        root=artifact_root,
        dataset_id=dataset.dataset_id,
        dataset_path=dataset_path,
        runs=tuple(
            runs_by_model[model]
            for model, _ in _RUN_SPECS
            if model in runs_by_model
        ),
        comparisons=tuple(comparisons),
        query_index=query_index,
    )


def _ensure_fixture_registry() -> None:
    try:
        register_model(FIXTURE_ADAPTER_ID, InsightFixtureAdapter)
    except ValueError:
        pass
    try:
        register_classifier(FIXTURE_CLASSIFIER_ID, InsightFixtureClassifier())
    except ValueError:
        pass


def _scenario_key(prompt: str) -> str:
    normalized = " ".join(prompt.lower().split())
    for scenario, token in _FIXTURE_PROMPT_TOKENS.items():
        if token in normalized:
            return scenario
    raise ValueError(f"prompt does not match a known insight fixture scenario: {prompt}")


def _assert_safe_empty_root(root: Path) -> None:
    if not root.exists():
        return
    if any(root.iterdir()):
        raise FileExistsError(
            f"fixture root must be empty or absent so deterministic artifact ids do not collide: {root}"
        )


def _is_existing_fixture_root(root: Path) -> bool:
    dataset_path = dataset_file(FIXTURE_DATASET_ID, root=root, create=False)
    return dataset_path.exists() and query_index_path(root=root).exists()
