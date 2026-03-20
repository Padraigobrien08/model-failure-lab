from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.utils.paths import build_baseline_run_dir, build_evaluation_run_dir
from scripts.check_phase17_seed_cohorts import main, run_command


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _create_seed_run(
    *,
    model_name: str,
    run_id: str,
    experiment_group: str,
    model_tag: str,
    seed: int,
    execution_tier: str | None = None,
    eval_ids: list[str] | None = None,
) -> None:
    run_dir = build_baseline_run_dir(model_name, run_id, create=True)
    metadata = {
        "run_id": run_id,
        "experiment_group": experiment_group,
        "tags": [
            "baseline",
            "official",
            "v1.2_baseline",
            model_tag,
            f"seed_{seed}",
        ],
        "status": "completed",
        "resolved_config": {
            "model": {
                "execution_tier": execution_tier,
            }
        },
    }
    _write_json(run_dir / "metadata.json", metadata)
    for eval_id in eval_ids or []:
        eval_dir = build_evaluation_run_dir(run_dir, eval_id, create=True)
        _write_json(eval_dir / "metadata.json", {"run_id": eval_id, "status": "completed"})


def test_phase17_seed_cohort_status_reports_complete_matrix(temp_artifact_root, capsys):
    for seed in (13, 42, 87):
        _create_seed_run(
            model_name="logistic_tfidf",
            run_id=f"logistic_{seed}",
            experiment_group="baselines_v1_2_logistic",
            model_tag="logistic",
            seed=seed,
            eval_ids=[f"logistic_eval_{seed}"],
        )
        _create_seed_run(
            model_name="distilbert",
            run_id=f"distilbert_{seed}",
            experiment_group="baselines_v1_2_distilbert",
            model_tag="distilbert",
            seed=seed,
            execution_tier="constrained",
            eval_ids=[f"distilbert_eval_{seed}"],
        )

    payload = run_command(["--json"])
    captured = capsys.readouterr()

    assert payload["complete"] is True
    assert payload["cohorts"]["distilbert"]["missing_seeds"] == []
    assert payload["cohorts"]["distilbert"]["eval_missing_seeds"] == []
    assert payload["cohorts"]["logistic"]["complete"] is True
    assert '"complete": true' in captured.out
    assert main(["--strict", "--json"]) == 0


def test_phase17_seed_cohort_status_flags_missing_and_unevaluated_runs(
    temp_artifact_root,
    capsys,
):
    _create_seed_run(
        model_name="distilbert",
        run_id="distilbert_13",
        experiment_group="baselines_v1_2_distilbert",
        model_tag="distilbert",
        seed=13,
        execution_tier="constrained",
        eval_ids=[],
    )

    payload = run_command(["--cohort", "distilbert"])
    captured = capsys.readouterr()

    assert payload["complete"] is False
    assert payload["cohorts"]["distilbert"]["missing_seeds"] == [42, 87]
    assert payload["cohorts"]["distilbert"]["eval_missing_seeds"] == [13]
    assert "missing seeds: 42, 87" in captured.out
    assert "missing eval bundles: 13" in captured.out
    assert main(["--cohort", "distilbert", "--strict"]) == 1
