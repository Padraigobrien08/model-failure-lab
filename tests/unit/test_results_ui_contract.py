from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_failure_lab.results_ui import (
    build_overview_snapshot,
    get_default_visible_entities,
    get_mitigation_comparison_views,
    get_primary_research_closeout,
    get_primary_stability_package,
    get_seeded_cohorts,
    load_results_ui_index,
)


def test_load_results_ui_index_validates_schema(results_ui_manifest: Path):
    payload = load_results_ui_index(results_ui_manifest)
    assert payload["schema_version"] == "artifact_index_v1"


def test_load_results_ui_index_rejects_unknown_schema(results_ui_manifest: Path):
    payload = json.loads(results_ui_manifest.read_text(encoding="utf-8"))
    payload["schema_version"] = "artifact_index_v2"
    results_ui_manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_results_ui_index(results_ui_manifest)


def test_results_ui_selectors_default_to_official_visible_entities(results_ui_manifest: Path):
    payload = load_results_ui_index(results_ui_manifest)

    default_runs = get_default_visible_entities(payload, "runs")
    all_runs = get_default_visible_entities(payload, "runs", include_exploratory=True)
    default_reports = get_default_visible_entities(payload, "reports")

    assert [run["id"] for run in default_runs] == ["run_official"]
    assert {run["id"] for run in all_runs} == {"run_official", "run_exploratory"}
    assert "phase26_report" in {report["id"] for report in default_reports}
    assert "phase23_scout_report" not in {report["id"] for report in default_reports}


def test_results_ui_selectors_keep_cohort_and_mitigation_order(results_ui_manifest: Path):
    payload = load_results_ui_index(results_ui_manifest)

    cohorts = get_seeded_cohorts(payload)
    mitigation_views = get_mitigation_comparison_views(payload)

    assert [cohort["cohort_id"] for cohort in cohorts] == [
        "logistic_baseline",
        "distilbert_baseline",
        "temperature_scaling",
        "reweighting",
    ]
    assert [view["mitigation_method"] for view in mitigation_views] == [
        "temperature_scaling",
        "reweighting",
    ]
    assert all(cohort["summary_actions"] for cohort in cohorts)
    assert all(view["summary_actions"] for view in mitigation_views)
    assert all("group_dro" not in view["mitigation_method"] for view in mitigation_views)


def test_overview_snapshot_surfaces_phase27_closeout_story(results_ui_manifest: Path):
    payload = load_results_ui_index(results_ui_manifest)

    snapshot = build_overview_snapshot(payload)
    stability = get_primary_stability_package(payload)
    closeout = get_primary_research_closeout(payload)

    assert snapshot["mitigation_labels"]["temperature_scaling"] == "stable"
    assert snapshot["mitigation_labels"]["reweighting"] == "mixed"
    assert snapshot["final_robustness_verdict"] == "still_mixed"
    assert snapshot["dataset_expansion_recommendation"] == "defer_now_reopen_under_conditions"
    assert stability["milestone_assessment"]["v1_1_findings_status"] == "stable"
    assert closeout is not None
    assert closeout["summary_actions"]
    assert (
        snapshot["headline_actions"]["temperature_scaling"][0]["label"]
        == "View supporting report"
    )
    assert snapshot["headline_actions"]["findings_doc"][0]["path"] == "docs/v1_4_closeout.md"
    assert snapshot["headline_actions"]["research_closeout"][0]["label"] == "View final gate JSON"
    assert stability["summary_actions"][0]["label"] == "View supporting report"
    assert stability["reference_actions"]
