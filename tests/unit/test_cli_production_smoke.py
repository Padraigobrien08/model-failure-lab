from __future__ import annotations

from model_failure_lab.cli import main


def test_production_smoke_flow_from_clean_workspace(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["demo"]) == 0
    demo_output = capsys.readouterr().out
    assert "Failure Lab Demo" in demo_output

    assert main(["datasets", "list"]) == 0
    datasets_output = capsys.readouterr().out
    assert "reasoning-failures-v1" in datasets_output

    assert main(["run", "--dataset", "reasoning-failures-v1", "--model", "demo"]) == 0
    _ = capsys.readouterr()

    run_dirs = sorted((tmp_path / "runs").iterdir())
    run_id = run_dirs[-1].name
    assert (tmp_path / "runs" / run_id / "run.json").exists()

    assert main(["report", "--run", run_id]) == 0
    report_output = capsys.readouterr().out
    assert "Failure Lab Report" in report_output
