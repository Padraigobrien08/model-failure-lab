"""Dataset runner orchestration for the new failure-analysis engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from model_failure_lab.adapters import ModelRequest, resolve_model
from model_failure_lab.classifiers import ClassifierInput, resolve_classifier
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.schemas import JsonValue, Run

from .contracts import (
    CaseClassification,
    CaseError,
    CaseExecution,
    CaseExpectationAssessment,
    CaseOutput,
    ExecutionMetadata,
    PromptSnapshot,
)
from .identity import build_run_id, derive_case_seed


@dataclass(slots=True, frozen=True)
class DatasetRunExecution:
    """Completed dataset execution plus emitted per-case result records."""

    run: Run
    adapter_id: str
    classifier_id: str
    run_seed: int
    status: str
    case_results: tuple[CaseExecution, ...]

    @property
    def total_cases(self) -> int:
        return len(self.case_results)

    @property
    def error_count(self) -> int:
        return sum(1 for case in self.case_results if case.error is not None)


def execute_dataset_run(
    *,
    dataset: FailureDataset,
    adapter_id: str,
    classifier_id: str,
    model: str,
    run_seed: int,
    run_config: dict[str, JsonValue] | None = None,
    now: datetime | None = None,
) -> DatasetRunExecution:
    """Execute all prompt cases in one dataset through one adapter and classifier."""

    adapter = resolve_model(adapter_id)
    classifier = resolve_classifier(classifier_id)
    current_time = now or datetime.now(timezone.utc)
    created_at = current_time.isoformat().replace("+00:00", "Z")
    config = dict(run_config or {})
    system_prompt = _system_prompt_from_config(config)
    model_options = _model_options_from_config(config)

    case_results: list[CaseExecution] = []
    for prompt_case in dataset.cases:
        prompt = PromptSnapshot.from_prompt_case(prompt_case)
        case_seed = derive_case_seed(
            run_seed=run_seed,
            dataset_id=dataset.dataset_id,
            case_id=prompt_case.id,
            adapter_id=adapter_id,
        )
        execution = ExecutionMetadata(
            adapter_id=adapter_id,
            model=model,
            classifier_id=classifier_id,
            run_seed=run_seed,
            case_seed=case_seed,
        )
        request = ModelRequest(
            model=model,
            prompt=prompt_case.prompt,
            seed=case_seed,
            system_prompt=system_prompt,
            options=model_options,
        )

        try:
            model_result = adapter.generate(request)
        except Exception as exc:
            case_results.append(
                CaseExecution(
                    case_id=prompt_case.id,
                    prompt=prompt,
                    execution=execution,
                    error=CaseError.from_exception(stage="model_invoke", exc=exc),
                )
            )
            continue

        execution = ExecutionMetadata.from_model_result(
            adapter_id=adapter_id,
            classifier_id=classifier_id,
            run_seed=run_seed,
            case_seed=case_seed,
            result=model_result,
        )
        output = CaseOutput.from_model_result(model_result)

        try:
            classifier_input = ClassifierInput(
                output=model_result,
                expectations=prompt.to_classifier_expectations(),
            )
            classification_result = classifier(classifier_input)
            classification = CaseClassification.from_classifier_result(classification_result)
        except Exception as exc:
            case_results.append(
                CaseExecution(
                    case_id=prompt_case.id,
                    prompt=prompt,
                    execution=execution,
                    output=output,
                    error=CaseError.from_exception(stage="classify", exc=exc),
                    expectation=CaseExpectationAssessment.from_prompt_and_classification(
                        prompt=prompt,
                        classification=None,
                    ),
                )
            )
            continue

        case_results.append(
            CaseExecution(
                case_id=prompt_case.id,
                prompt=prompt,
                execution=execution,
                output=output,
                classification=classification,
                expectation=CaseExpectationAssessment.from_prompt_and_classification(
                    prompt=prompt,
                    classification=classification,
                ),
            )
        )

    status = "completed_with_errors" if any(case.error for case in case_results) else "completed"
    run_id = build_run_id(
        dataset_id=dataset.dataset_id,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
        model=model,
        run_seed=run_seed,
        run_config=config,
        now=current_time,
    )
    run_metadata: dict[str, JsonValue] = {
        "adapter_id": adapter_id,
        "classifier_id": classifier_id,
        "run_seed": run_seed,
        "status": status,
        "total_cases": len(case_results),
        "error_count": sum(1 for case in case_results if case.error is not None),
        "dataset_name": dataset.name,
        "dataset_version": dataset.version,
    }
    if dataset.description is not None:
        run_metadata["dataset_description"] = dataset.description
    if dataset.metadata:
        run_metadata["dataset_metadata"] = dict(dataset.metadata)

    run = Run(
        run_id=run_id,
        model=model,
        dataset=dataset.dataset_id,
        created_at=created_at,
        config=config,
        metadata=run_metadata,
    )
    return DatasetRunExecution(
        run=run,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
        run_seed=run_seed,
        status=status,
        case_results=tuple(case_results),
    )


def _system_prompt_from_config(config: dict[str, JsonValue]) -> str | None:
    system_prompt = config.get("system_prompt")
    return system_prompt if isinstance(system_prompt, str) and system_prompt.strip() else None


def _model_options_from_config(config: dict[str, JsonValue]) -> dict[str, JsonValue]:
    options = config.get("model_options")
    if isinstance(options, dict):
        return {key: value for key, value in options.items() if isinstance(key, str)}
    return {}
