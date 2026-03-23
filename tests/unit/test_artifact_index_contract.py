from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.artifact_index import build_artifact_index_payload
from model_failure_lab.utils.paths import (
    artifact_root,
    build_baseline_run_dir,
    build_evaluation_run_dir,
    build_mitigation_run_dir,
    build_report_run_dir,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _workspace_path(path: Path) -> str:
    relative = path.resolve().relative_to(artifact_root())
    return f"/workspace/model-failure-lab/artifacts/{relative.as_posix()}"


def _write_run(
    *,
    model_name: str,
    run_id: str,
    experiment_group: str,
    seed: int,
    tags: list[str],
    mitigation_method: str | None = None,
    parent_run_id: str | None = None,
) -> Path:
    if mitigation_method is None:
        run_dir = build_baseline_run_dir(model_name, run_id, create=True)
        experiment_type = "baseline"
    else:
        run_dir = build_mitigation_run_dir(mitigation_method, model_name, run_id, create=True)
        experiment_type = "mitigation"
    artifact_paths = {
        "checkpoint": _workspace_path(run_dir / "checkpoint"),
        "metrics_json": _workspace_path(run_dir / "metrics.json"),
        "plots": _workspace_path(run_dir / "figures"),
    }
    (run_dir / "checkpoint").mkdir(parents=True, exist_ok=True)
    (run_dir / "figures").mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "metrics.json", {"macro_f1": 0.8})
    _write_json(
        run_dir / "metadata.json",
        {
            "run_id": run_id,
            "experiment_type": experiment_type,
            "experiment_group": experiment_group,
            "model_name": model_name,
            "dataset_name": "civilcomments",
            "split_details": {"validation": "ood_test"},
            "random_seed": seed,
            "resolved_config": {"seed": seed, "experiment_group": experiment_group, "tags": tags},
            "command": "python",
            "artifact_paths": artifact_paths,
            "parent_run_id": parent_run_id,
            "tags": tags,
            "status": "completed",
            "mitigation_method": mitigation_method,
        },
    )
    return run_dir


def _write_eval(
    *,
    run_dir: Path,
    eval_id: str,
    experiment_group: str,
    seed: int,
    source_run_id: str,
    tags: list[str],
    headline_metrics: dict[str, float],
    source_parent_run_id: str | None = None,
    mitigation_method: str | None = None,
) -> None:
    eval_dir = build_evaluation_run_dir(run_dir, eval_id, create=True)
    ui_summary_path = eval_dir / "ui_summary.json"
    overall_metrics_path = eval_dir / "overall_metrics.json"
    _write_json(
        ui_summary_path,
        {
            "headline_metrics": headline_metrics,
            "split_metrics": [],
            "subgroups": [],
            "calibration_summary": [],
            "confidence_summary": {},
        },
    )
    _write_json(
        overall_metrics_path,
        {
            "headline_metrics": headline_metrics,
            "id": {"macro_f1": headline_metrics["id_macro_f1"]},
            "ood": {"macro_f1": headline_metrics["ood_macro_f1"]},
        },
    )
    _write_json(
        eval_dir / "metadata.json",
        {
            "eval_id": eval_id,
            "run_id": eval_id,
            "experiment_type": "shift_eval",
            "experiment_group": experiment_group,
            "model_name": "distilbert"
            if "distilbert" in experiment_group or mitigation_method
            else "logistic_tfidf",
            "dataset_name": "civilcomments",
            "random_seed": seed,
            "resolved_config": {"seed": seed, "experiment_group": experiment_group, "tags": tags},
            "source_run_id": source_run_id,
            "source_parent_run_id": source_parent_run_id,
            "mitigation_method": mitigation_method,
            "artifact_paths": {
                "ui_summary_json": _workspace_path(ui_summary_path),
                "overall_metrics_json": _workspace_path(overall_metrics_path),
            },
            "tags": tags,
            "status": "completed",
        },
    )


def _write_report(
    *,
    report_scope: str,
    report_id: str,
    source_eval_ids: list[str],
    report_data: dict[str, object] | None = None,
    report_summary: dict[str, object] | None = None,
    stability_summary: dict[str, object] | None = None,
    experiment_type: str | None = None,
) -> None:
    report_dir = build_report_run_dir(report_scope, report_id, create=True)
    report_experiment_type = (
        experiment_type
        if experiment_type is not None
        else "stability_report"
        if stability_summary is not None
        else "report"
    )
    artifact_paths: dict[str, str] = {"report_markdown": _workspace_path(report_dir / "report.md")}
    (report_dir / "report.md").write_text("# report\n", encoding="utf-8")
    if report_data is not None:
        artifact_paths["report_data_json"] = _workspace_path(report_dir / "report_data.json")
        _write_json(report_dir / "report_data.json", report_data)
    if report_summary is not None:
        artifact_paths["report_summary_json"] = _workspace_path(report_dir / "report_summary.json")
        _write_json(report_dir / "report_summary.json", report_summary)
    if stability_summary is not None:
        artifact_paths["stability_summary_json"] = _workspace_path(
            report_dir / "stability_summary.json"
        )
        _write_json(report_dir / "stability_summary.json", stability_summary)

    _write_json(
        report_dir / "metadata.json",
        {
            "report_id": report_id,
            "run_id": report_id,
            "experiment_type": report_experiment_type,
            "experiment_group": report_scope,
            "report_scope": report_scope,
            "selection_mode": "eval_ids",
            "source_eval_ids": source_eval_ids,
            "cohort_eval_ids": None,
            "artifact_paths": artifact_paths,
            "tags": ["baseline", "distilbert", "report"],
            "status": "completed",
        },
    )


def _build_minimal_artifact_world() -> None:
    logistic_run = _write_run(
        model_name="logistic_tfidf",
        run_id="logistic_seed_13",
        experiment_group="baselines_v1_2_logistic",
        seed=13,
        tags=["baseline", "official", "seed_13"],
    )
    _write_eval(
        run_dir=logistic_run,
        eval_id="logistic_eval_13",
        experiment_group="baselines_v1_2_logistic",
        seed=13,
        source_run_id="logistic_seed_13",
        tags=["baseline", "official", "seed_13", "shift_eval"],
        headline_metrics={
            "id_macro_f1": 0.80,
            "ood_macro_f1": 0.74,
            "robustness_gap_f1": 0.06,
            "worst_group_f1": 0.31,
            "ece": 0.16,
            "brier_score": 0.09,
        },
    )

    parent_run = _write_run(
        model_name="distilbert",
        run_id="distilbert_seed_13",
        experiment_group="baselines_v1_2_distilbert",
        seed=13,
        tags=["baseline", "official", "seed_13"],
    )
    _write_eval(
        run_dir=parent_run,
        eval_id="parent_eval_13",
        experiment_group="baselines_v1_2_distilbert",
        seed=13,
        source_run_id="distilbert_seed_13",
        tags=["baseline", "official", "seed_13", "shift_eval"],
        headline_metrics={
            "id_macro_f1": 0.87,
            "ood_macro_f1": 0.80,
            "robustness_gap_f1": 0.07,
            "worst_group_f1": 0.30,
            "ece": 0.03,
            "brier_score": 0.05,
        },
    )

    temp_run = _write_run(
        model_name="distilbert",
        run_id="temp_seed_13",
        experiment_group="temperature_scaling_v1_2",
        seed=13,
        tags=["mitigation", "official", "seed_13"],
        mitigation_method="temperature_scaling",
        parent_run_id="distilbert_seed_13",
    )
    _write_eval(
        run_dir=temp_run,
        eval_id="temp_eval_13",
        experiment_group="temperature_scaling_v1_2",
        seed=13,
        source_run_id="temp_seed_13",
        source_parent_run_id="distilbert_seed_13",
        tags=["mitigation", "official", "seed_13", "shift_eval"],
        mitigation_method="temperature_scaling",
        headline_metrics={
            "id_macro_f1": 0.87,
            "ood_macro_f1": 0.80,
            "robustness_gap_f1": 0.07,
            "worst_group_f1": 0.30,
            "ece": 0.02,
            "brier_score": 0.048,
        },
    )

    reweight_run = _write_run(
        model_name="distilbert",
        run_id="reweight_seed_13",
        experiment_group="reweighting_v1_2",
        seed=13,
        tags=["mitigation", "official", "seed_13"],
        mitigation_method="reweighting",
        parent_run_id="distilbert_seed_13",
    )
    _write_eval(
        run_dir=reweight_run,
        eval_id="reweight_eval_13",
        experiment_group="reweighting_v1_2",
        seed=13,
        source_run_id="reweight_seed_13",
        source_parent_run_id="distilbert_seed_13",
        tags=["mitigation", "official", "seed_13", "shift_eval"],
        mitigation_method="reweighting",
        headline_metrics={
            "id_macro_f1": 0.86,
            "ood_macro_f1": 0.801,
            "robustness_gap_f1": 0.059,
            "worst_group_f1": 0.36,
            "ece": 0.036,
            "brier_score": 0.056,
        },
    )

    exploratory_run = _write_run(
        model_name="distilbert",
        run_id="explore_seed_99",
        experiment_group="baselines_v1_2_exploratory",
        seed=99,
        tags=["baseline", "seed_99"],
    )
    _write_eval(
        run_dir=exploratory_run,
        eval_id="explore_eval_99",
        experiment_group="baselines_v1_2_exploratory",
        seed=99,
        source_run_id="explore_seed_99",
        tags=["baseline", "seed_99", "shift_eval"],
        headline_metrics={
            "id_macro_f1": 0.5,
            "ood_macro_f1": 0.4,
            "robustness_gap_f1": 0.1,
            "worst_group_f1": 0.2,
            "ece": 0.2,
            "brier_score": 0.2,
        },
    )

    _write_report(
        report_scope="phase18_temperature_scaling_seeded",
        report_id="temp_seeded_report",
        source_eval_ids=["parent_eval_13", "temp_eval_13"],
        report_data={
            "report_summary": {
                "seeded_interpretation": "stable",
                "mitigation_verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
            },
            "mitigation_comparison_table": [
                {
                    "parent_eval_id": "parent_eval_13",
                    "mitigation_eval_id": "temp_eval_13",
                    "mitigation_method": "temperature_scaling",
                    "verdict": "win",
                    "id_macro_f1_delta": 0.0,
                    "ood_macro_f1_delta": 0.0,
                    "robustness_gap_delta": 0.0,
                    "worst_group_f1_delta": 0.0,
                    "ece_delta": -0.01,
                    "brier_score_delta": -0.002,
                }
            ],
            "mitigation_method_summaries": {
                "temperature_scaling": {
                    "seeded_interpretation": "stable",
                    "verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
                }
            },
            "comparison_table": [],
            "subgroup_table": [],
            "calibration_table": [],
        },
        report_summary={
            "seeded_interpretation": "stable",
            "mitigation_verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
        },
    )
    _write_report(
        report_scope="phase19_reweighting_seeded",
        report_id="reweight_seeded_report",
        source_eval_ids=["parent_eval_13", "temp_eval_13", "reweight_eval_13"],
        report_data={
            "report_summary": {
                "seeded_interpretation": "stable",
                "mitigation_verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
                "mitigation_method_summaries": {
                    "reweighting": {
                        "seeded_interpretation": "stable",
                        "verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
                    },
                    "temperature_scaling": {
                        "seeded_interpretation": "stable",
                        "verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
                    },
                },
            },
            "mitigation_comparison_table": [
                {
                    "parent_eval_id": "parent_eval_13",
                    "mitigation_eval_id": "reweight_eval_13",
                    "mitigation_method": "reweighting",
                    "verdict": "tradeoff",
                    "id_macro_f1_delta": -0.01,
                    "ood_macro_f1_delta": 0.001,
                    "robustness_gap_delta": -0.011,
                    "worst_group_f1_delta": 0.06,
                    "ece_delta": 0.006,
                    "brier_score_delta": 0.007,
                }
            ],
            "mitigation_method_summaries": {
                "reweighting": {
                    "seeded_interpretation": "stable",
                    "verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
                },
                "temperature_scaling": {
                    "seeded_interpretation": "stable",
                    "verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
                },
            },
            "comparison_table": [],
            "subgroup_table": [],
            "calibration_table": [],
        },
        report_summary={
            "seeded_interpretation": "stable",
            "mitigation_verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
        },
    )
    _write_report(
        report_scope="phase19_reweighting_seed_13",
        report_id="reweight_seed_13_report",
        source_eval_ids=["parent_eval_13", "reweight_eval_13"],
        report_summary={"seeded_interpretation": "stable"},
    )
    _write_report(
        report_scope="phase19_three_way_seed_13",
        report_id="three_way_seed_13_report",
        source_eval_ids=["parent_eval_13", "temp_eval_13", "reweight_eval_13"],
        report_summary={"seeded_interpretation": "stable"},
    )
    _write_report(
        report_scope="phase20_stability",
        report_id="phase20_report",
        source_eval_ids=[
            "logistic_eval_13",
            "parent_eval_13",
            "temp_eval_13",
            "reweight_eval_13",
        ],
        report_data={
            "stability_summary": {
                "cohort_summaries": {
                    "logistic_baseline": {"label": "stable"},
                    "distilbert_baseline": {"label": "stable"},
                    "temperature_scaling": {
                        "label": "stable",
                        "verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
                    },
                    "reweighting": {
                        "label": "mixed",
                        "verdict_counts": {"win": 1, "tradeoff": 0, "failure": 0},
                    },
                },
                "baseline_model_comparison": {"label": "mixed"},
                "milestone_assessment": {
                    "v1_1_findings_status": "stable",
                    "dataset_expansion_recommendation": "defer",
                },
                "reference_reports": {
                    "temperature_scaling_seeded": _workspace_path(
                        build_report_run_dir(
                            "phase18_temperature_scaling_seeded",
                            "temp_seeded_report",
                        )
                        / "report.md"
                    ),
                    "reweighting_seeded": _workspace_path(
                        build_report_run_dir(
                            "phase19_reweighting_seeded",
                            "reweight_seeded_report",
                        )
                        / "report.md"
                    ),
                },
            },
            "baseline_stability_table": [],
            "temperature_scaling_deltas": [],
            "reweighting_deltas": [],
        },
        stability_summary={
            "cohort_summaries": {
                "logistic_baseline": {"label": "stable"},
                "distilbert_baseline": {"label": "stable"},
                "temperature_scaling": {"label": "stable"},
                "reweighting": {"label": "mixed"},
            },
            "baseline_model_comparison": {"label": "mixed"},
            "milestone_assessment": {
                "v1_1_findings_status": "stable",
                "dataset_expansion_recommendation": "defer",
            },
            "reference_reports": {
                "temperature_scaling_seeded": _workspace_path(
                    build_report_run_dir(
                        "phase18_temperature_scaling_seeded",
                        "temp_seeded_report",
                    )
                    / "report.md"
                ),
                "reweighting_seeded": _workspace_path(
                    build_report_run_dir(
                        "phase19_reweighting_seeded",
                        "reweight_seeded_report",
                    )
                    / "report.md"
                ),
            },
        },
    )
    _write_report(
        report_scope="phase13_temperature_scaling_perturbations",
        report_id="perturbation_report",
        source_eval_ids=["perturb_eval_13"],
        report_summary={"suite_status": "complete"},
        experiment_type="perturbation_report",
    )


def test_build_artifact_index_emits_official_inventory_and_first_class_views(temp_artifact_root):
    _build_minimal_artifact_world()

    payload = build_artifact_index_payload()

    assert payload["schema_version"] == "artifact_index_v1"
    assert payload["default_filters"]["official_only"] is True

    run_lookup = {row["run_id"]: row for row in payload["entities"]["runs"]}
    eval_lookup = {row["eval_id"]: row for row in payload["entities"]["evaluations"]}
    report_lookup = {row["report_id"]: row for row in payload["entities"]["reports"]}

    assert run_lookup["distilbert_seed_13"]["is_official"] is True
    assert run_lookup["explore_seed_99"]["is_official"] is False
    assert run_lookup["explore_seed_99"]["default_visible"] is False
    assert run_lookup["distilbert_seed_13"]["artifact_refs"]["metrics_json"]["exists"] is True
    assert eval_lookup["parent_eval_13"]["artifact_refs"]["ui_summary_json"]["path"].startswith(
        "artifacts/"
    )
    assert eval_lookup["parent_eval_13"]["artifact_refs"]["ui_summary_json"]["exists"] is True
    assert "perturbation_report" not in report_lookup

    cohort_ids = [row["cohort_id"] for row in payload["views"]["seeded_cohorts"]]
    assert cohort_ids == [
        "logistic_baseline",
        "distilbert_baseline",
        "temperature_scaling",
        "reweighting",
    ]

    mitigation_views = {
        row["mitigation_method"]: row for row in payload["views"]["mitigation_comparisons"]
    }
    reweighting_view = mitigation_views["reweighting"]
    assert reweighting_view["comparison_summary"]["seeded_interpretation"] == "stable"
    assert reweighting_view["stability_assessment"]["label"] == "mixed"
    assert reweighting_view["per_seed_comparisons"][0]["related_report_ids"] == [
        "reweight_seed_13_report",
        "three_way_seed_13_report",
    ]

    stability_package = payload["views"]["stability_packages"][0]
    assert stability_package["milestone_assessment"]["dataset_expansion_recommendation"] == "defer"
    assert stability_package["reference_reports"]["reweighting_seeded"]["path"].startswith(
        "artifacts/"
    )
