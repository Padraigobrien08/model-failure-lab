# Model Failure Lab

Model Failure Lab is an artifact-driven research repo for measuring how text-classification models
fail under distribution shift. The current benchmark centers on CivilComments from WILDS and keeps
baseline, mitigation, evaluation, reporting, and UI surfaces reproducible from saved artifacts.

## Start Here

The primary entrypoint is the read-only results explorer:

```bash
python3 -m pip install -e .[ui]
python3 scripts/run_results_ui.py
```

The UI reads only from the generated manifest at
`artifacts/contracts/artifact_index/v1/index.json`.

For the written interpretation layer, read:

- [v1.3 findings](docs/v1_3_findings.md)

## v1.3 Snapshot

- The seeded baseline story held: Logistic TF-IDF and DistilBERT baseline behavior remained stable
  across seeds, and DistilBERT still beat Logistic on OOD Macro F1.
- `temperature_scaling` is the clean calibration lane: `3/3` seeded wins with stable ECE/Brier
  improvement and no robustness gain.
- `reweighting` is still the best current robustness lane, but it remains mixed: `2/3` wins,
  `1/3` tradeoff.
- The `group_dro` challenger scout was run, evaluated, and rejected; it remains exploratory rather
  than official milestone evidence.
- Dataset expansion remains `defer` until the robustness story is more consistent and easier to
  explain.

## Official Evidence

The default-visible `v1.3` evidence package is anchored on these saved reports:

- [Phase 18 seeded temperature-scaling package](artifacts/reports/comparisons/phase18_temperature_scaling_seeded/20260321_143714_report_0eea/report.md)
- [Phase 19 seeded reweighting package](artifacts/reports/comparisons/phase19_reweighting_seeded/20260321_224830_report_12f3/report.md)
- [Phase 20 seeded stability package](artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

Exploratory but documented:

- [Phase 23 `group_dro` scout report](artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md)

## Setup

Use Python 3.11 or newer.

```bash
python3 -m pip install -e .[dev]
python3 scripts/check_environment.py
python3 scripts/download_data.py
```

If you only want the runtime setup details first, see:

- [Runtime setup reference](docs/runtime-setup.md)

## Docs

- [v1.3 findings](docs/v1_3_findings.md)
- [v1.1 findings](docs/v1_1_findings.md)
- [v1.1 reproducibility walkthrough](docs/v1_1_reproducibility.md)
- [Runtime setup reference](docs/runtime-setup.md)
- [Cloud GPU run guide](docs/cloud-gpu-run.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Configuration layout](configs/README.md)
