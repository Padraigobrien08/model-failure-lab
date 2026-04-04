from __future__ import annotations

import json

from model_failure_lab.cli import main
from model_failure_lab.testing import materialize_insight_fixture


def test_cli_clusters_show_and_history_surface_recurring_cluster_details(
    tmp_path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")

    list_exit = main(
        [
            "clusters",
            "--root",
            str(workspace.root),
            "--kind",
            "comparison_delta",
            "--dataset",
            workspace.dataset_id,
            "--json",
        ]
    )
    list_payload = json.loads(capsys.readouterr().out)

    cluster_id = str(list_payload["rows"][0]["cluster_id"])

    show_exit = main(
        [
            "cluster",
            "show",
            cluster_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    show_payload = json.loads(capsys.readouterr().out)

    history_exit = main(
        [
            "cluster",
            "history",
            cluster_id,
            "--root",
            str(workspace.root),
        ]
    )
    history_output = capsys.readouterr().out

    assert list_exit == 0
    assert list_payload["query_kind"] == "failure_clusters"
    assert list_payload["filters"]["kind"] == "comparison_delta"
    assert list_payload["rows"]

    assert show_exit == 0
    assert show_payload["summary"]["cluster_id"] == cluster_id
    assert show_payload["summary"]["cluster_kind"] == "comparison_delta"
    assert show_payload["occurrences"]

    assert history_exit == 0
    assert "Failure Lab Cluster History" in history_output
    assert cluster_id in history_output
