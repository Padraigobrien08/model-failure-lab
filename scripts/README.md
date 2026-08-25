# scripts/

Two surfaces live here, and only the first is part of the supported product.

## Production

| Script | Role |
|---|---|
| `query_bridge.py` | The operator console's engine bridge. `frontend/server/artifactBridge.ts` shells into it for every read endpoint that needs the engine, and for the three dataset write endpoints. Its payloads are a committed contract — see `tests/fixtures/bridge/` and `tests/unit/test_bridge_payload_contract.py`. |
| `generate_insight_fixture.py` | Regenerates the deterministic fixture workspace the tests and the bridge contract build against (`docs/fixture-workspace.md`). |
| `smoke_package_install.py` | Clean-install smoke check used when validating a build. |
| `run_react_ui.py` | Thin launcher for `npm --prefix frontend run dev`. The documented way to start the console is that npm command directly (`frontend/README.md`). |
| `_bootstrap.py` | Puts `src/` on `sys.path` so a script can run from a checkout without installing. |

## Legacy research stack (reference only)

Everything else drives the DistilBERT/CivilComments benchmark work described in
`docs/legacy.md`. These read the `utils/paths.py` artifact layout — **not** the production
`storage/layout.py` one — and need the optional `[legacy]` extra installed:

`build_artifact_index.py`, `build_final_gate.py`, `build_perturbation_report.py`,
`build_report.py`, `build_robustness_report.py`, `build_stability_report.py`,
`check_environment.py`, `check_phase17_seed_cohorts.py`, `download_data.py`,
`finalize_phase17_distilbert_runs.sh`, `run_baseline.py`, `run_mitigation.py`,
`run_perturbation_eval.py`, `run_phase17_distilbert_seeds.sh`, `run_results_ui.py`,
`run_shift_eval.py`, `validate_artifact_index.py`.

They are kept for historical context. New production features do not go here — see
`docs/code-map.md`.
