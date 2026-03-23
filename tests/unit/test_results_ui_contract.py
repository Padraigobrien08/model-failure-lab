from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_failure_lab.results_ui import (
    build_overview_snapshot,
    get_default_visible_entities,
    get_mitigation_comparison_views,
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

    assert [run["id"] for run in default_runs] == ["run_official"]
    assert {run["id"] for run in all_runs} == {"run_official", "run_exploratory"}


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


def test_overview_snapshot_surfaces_phase20_story(results_ui_manifest: Path):
    payload = load_results_ui_index(results_ui_manifest)

    snapshot = build_overview_snapshot(payload)
    stability = get_primary_stability_package(payload)

    assert snapshot["mitigation_labels"]["temperature_scaling"] == "stable"
    assert snapshot["mitigation_labels"]["reweighting"] == "mixed"
    assert snapshot["dataset_expansion_recommendation"] == "defer"
    assert stability["milestone_assessment"]["v1_1_findings_status"] == "stable"
