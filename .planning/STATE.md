---
gsd_state_version: 1.0
milestone: v1.7
milestone_name: Trace-First Failure Debugger Rebuild
current_phase: 36
current_plan: 2
status: ready_for_verification
stopped_at: Completed 36-02-PLAN.md
last_updated: "2026-03-26T11:07:28.914Z"
last_activity: 2026-03-26
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 2
  completed_plans: 2
  percent: 100
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-03-26)

**Core value:** Make failure under distribution shift measurable, reproducible, and easy to compare so robustness tradeoffs are explicit instead of hidden behind aggregate accuracy.
**Current focus:** Phase 36 complete — ready for the Phase 37 summary route build

## Current Position

Phase: 36 (trace-shell-and-route-scaffold) — COMPLETE
Plan: 2 of 2
Current Phase: 36
Current Plan: 2
Total Plans in Phase: 2
Status: Completed 36-02-PLAN.md; ready for Phase 37 planning or verification
Last Activity: 2026-03-26
**Progress:** [██████████] 100%

## Snapshot

- Archived milestone: [v1.0 roadmap](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.0-ROADMAP.md)
- Archived milestone: [v1.1 roadmap](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.1-ROADMAP.md)
- Archived milestone requirements: [v1.1 requirements](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.1-REQUIREMENTS.md)
- Archived milestone: [v1.2 roadmap](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.2-ROADMAP.md)
- Archived milestone requirements: [v1.2 requirements](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.2-REQUIREMENTS.md)
- Archived milestone: [v1.3 roadmap](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.3-ROADMAP.md)
- Archived milestone requirements: [v1.3 requirements](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.3-REQUIREMENTS.md)
- Archived milestone: [v1.4 roadmap](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.4-ROADMAP.md)
- Archived milestone requirements: [v1.4 requirements](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.4-REQUIREMENTS.md)
- Archived milestone audit: [v1.4 audit](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.4-MILESTONE-AUDIT.md)
- Archived milestone: [v1.5 roadmap](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.5-ROADMAP.md)
- Archived milestone requirements: [v1.5 requirements](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.5-REQUIREMENTS.md)
- Archived milestone audit: [v1.5 audit](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.5-MILESTONE-AUDIT.md)
- Current roadmap: [ROADMAP.md](/Users/padraigobrien/model-failure-lab/.planning/ROADMAP.md)
- Current requirements: [REQUIREMENTS.md](/Users/padraigobrien/model-failure-lab/.planning/REQUIREMENTS.md)
- Research summary: [SUMMARY.md](/Users/padraigobrien/model-failure-lab/.planning/research/SUMMARY.md)
- Milestone history: [MILESTONES.md](/Users/padraigobrien/model-failure-lab/.planning/MILESTONES.md)

## Current Focus

- `v1.7` is now active as **Trace-First Failure Debugger Rebuild**.
- This milestone supersedes the unfinished `v1.6` workbench direction and restarts the frontend around one strict route chain:
  - `Verdict`
  - `Lane`
  - `Method`
  - `Run`
  - `Artifact`
- The rebuild constraints are now explicit:
  - not a dashboard
  - not a marketing UI
  - progressive disclosure across routes
  - one question per screen
  - inspector-driven evidence visibility
  - minimal shadcn usage
- The phase sequence is intentionally narrow and route-first:
  - Phase 36: shell and routes
  - Phase 37: summary
  - Phase 38: lane
  - Phase 39: method
  - Phase 40: run
  - Phase 41: raw debug plus shared inspector
  - Phase 42: scope filtering
  - Phase 43: audit and tightening
- Mocked data is acceptable in the early phases; real backend or manifest rewiring is not required to start this rebuild.
- Phase 36 discussion is now complete and the shell reset contract is locked:
  - minimal new shell
  - header-only navigation
  - no visible inspector column yet
  - scope state in context plus `?scope=official|all`
  - no legacy route redirects
- Phase 36 is now planned in two execution waves:
  - `36-01` resets `App.tsx`, the route contract, and the shared `official|all` scope context while replacing the heavy shell with a sticky-header-only frame
  - `36-02` adds dedicated placeholder pages for `/`, `/lane/:laneId`, `/lane/:laneId/:methodId`, `/run/:runId`, and `/debug/raw/:entityId` plus route-level regression coverage
- `36-01` is complete and recorded in `.planning/phases/36-trace-shell-and-route-scaffold/36-01-SUMMARY.md`.
- `36-02` is now complete and recorded in `.planning/phases/36-trace-shell-and-route-scaffold/36-02-SUMMARY.md`.
- Phase 36 now satisfies the full scaffold requirement:
  - every required path renders a dedicated placeholder surface
  - placeholder links preserve `?scope=official|all`
  - route-level regression tests cover direct navigation and scope persistence
- The next workflow step is Phase 37 planning or execution for the real summary entry route at `/`.

## Accumulated Context

### Decisions

- `v1.5` should introduce a React frontend as the new primary UI over the existing manifest-driven artifact contract.
- Streamlit should remain temporarily available as a fallback and validation surface while React reaches parity.
- `v1.5` is a presentation-layer milestone only: no new runs, datasets, or backend services belong in scope.
- `v1.0` is archived locally and remains the validated architecture baseline.
- `v1.1` should operationalize the shipped script-first workflow rather than expand model or dataset scope.
- CivilComments remains the only benchmark dataset in scope for this milestone.
- The fixed Logistic Regression and DistilBERT pair remain the benchmark baseline pair.
- Real-run evidence now matters more than new feature breadth.
- `v1.2` should validate stability before widening benchmark scope.
- `temperature_scaling` remains the official reference mitigation, and `reweighting` becomes the second real mitigation lane to validate.
- Phase 17 official seed set is fixed at `13`, `42`, and `87` for both baseline models.
- Official DistilBERT seed runs must all use the constrained tier with no canonical/constrained mixing.
- Official Phase 17 baseline cohorts use per-model experiment groups plus strict `official` and `seed_<n>` tagging.
- Every official baseline seed run must produce its own saved shift-eval bundle in Phase 17.
- The official Logistic Regression seeded cohort is complete for seeds `13`, `42`, and `87`, each with its own shift-eval bundle.
- The official DistilBERT seeded cohort is complete for seeds `13`, `42`, and `87`, each with constrained-tier runtime metadata and a saved local shift-eval bundle.
- Phase 18 requires full seeded `temperature_scaling` child coverage for seeds `13`, `42`, and `87`; no partial official child cohort is acceptable.
- Official Phase 18 `temperature_scaling` children will use shared experiment group `temperature_scaling_v1_2` plus strict `official`, `seed_<n>`, and `parent_<run_id>` tags.
- Official Phase 18 reports should use explicit parent and child eval-ID selection, even though child discovery may still use experiment group plus `official` tag.
- Phase 18 must produce both per-seed parent-versus-child reports and one seeded aggregate comparison package.
- Honest mixed outcomes are acceptable in Phase 18 as long as all seeded verdicts and the aggregate stability interpretation are explicit.
- Phase 18 should reuse the completed Phase 17 parent eval bundles by default rather than regenerating them.
- The official seeded `temperature_scaling` child cohort is now complete for DistilBERT seeds `13`, `42`, and `87`, and each child has its own saved shift-eval bundle.
- The official seeded aggregate mitigation package [phase18_temperature_scaling_seeded](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase18_temperature_scaling_seeded/20260321_143714_report_0eea/report.md) classifies the original `v1.1` temperature-scaling story as `stable` with `win=3`, `tradeoff=0`, and `failure=0`.
- Phase 19 fixes the official reweighting recipe as shipped: `group_id`, `inverse_sqrt_frequency`, `max_weight=5.0`, `normalize_mean=1.0`.
- Official reweighting evidence must cover seeds `13`, `42`, and `87`, not just one parent seed.
- Phase 19 must produce both pairwise parent-versus-reweighting reports and three-way baseline / `temperature_scaling` / `reweighting` reports, plus one seeded aggregate package built from explicit eval IDs.
- Reweighting may land as a `win`, `tradeoff`, or `failure`; the milestone gate is honest seeded evidence, not a forced positive outcome.
- Official reweighting children must use the same constrained DistilBERT runtime budget as the seeded parent cohort, with no hyperparameter drift beyond the weighting mechanism itself.
- Phase 19 planning confirmed that reweighting children already inherit the parent resolved runtime config through `build_inherited_mitigation_config(...)`; the execution risk is proving parity and then running the three seeded child jobs.
- Phase 19 planning also identified one reporting upgrade: multi-method seeded aggregate packages need method-aware verdict summaries so `reweighting` is not collapsed into the already-stable `temperature_scaling` counts.
- Phase 19 task 1 is now complete and committed as `7bed3b7` (`test: pin seeded reweighting child contract`).
- The reweighting contract tests now pin constrained parent inheritance, `reweighting_v1_2`, official seeded tags, parent tags, and baseline-tag stripping for official children.
- The official seeded `reweighting` child cohort is now complete for DistilBERT seeds `13`, `42`, and `87`, and each child has its own saved shift-eval bundle.
- The Phase 19 aggregate package [phase19_reweighting_seeded](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase19_reweighting_seeded/20260321_224830_report_12f3/report.md) classifies `reweighting` as `stable` across the constrained three-seed cohort with `win=2`, `tradeoff=1`, and `failure=0`, while `temperature_scaling` remains the cleaner `3/3` stable reference lane.
- Phase 19 committed `f3a1cf6` (`feat: add method-aware seeded mitigation summaries`) so multi-method aggregate packages now preserve per-method verdict counts and seeded interpretations.
- Phase 19 committed `b3b68da` (`fix: compare eval bundles by schema contract`) so saved evaluation bundles compare by the actual eval schema contract instead of git-hash drift across test-only commits.
- Phase 20 official cohort scope is fixed to the full official set: Logistic baseline, DistilBERT baseline, seeded `temperature_scaling`, and seeded `reweighting`.
- Phase 20 statistics must include per-seed rows, mean, standard deviation, and matched mitigation deltas for `temperature_scaling` and `reweighting`.
- Phase 20 should produce one aggregate stability report plus machine-readable CSV/JSON outputs, not a new family of seed-local reports.
- Phase 20 interpretations must label conclusions as `stable`, `mixed`, or `noisy`, and end with a milestone-level recommendation on whether dataset expansion remains deferred.
- Phase 20 committed `5dbd551` (`feat: add seeded stability reporting`) so the repo now has a dedicated seeded stability aggregation/report surface plus a public `build_stability_report.py` entrypoint.
- The official Phase 20 aggregate package lives at [phase20_stability](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md) with machine-readable outputs in [stability_summary.json](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/stability_summary.json), [baseline_stability.csv](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/tables/baseline_stability.csv), [temperature_scaling_deltas.csv](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/tables/temperature_scaling_deltas.csv), and [reweighting_deltas.csv](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/tables/reweighting_deltas.csv).
- The final Phase 20 labels are now locked in saved artifacts:
  - Logistic baseline: `stable`
  - DistilBERT baseline: `stable`
  - `temperature_scaling`: `stable`
  - `reweighting`: `mixed`
  - Logistic vs DistilBERT baseline comparison: `mixed`
  - original `v1.1` findings under seed variation: `stable`
  - dataset expansion recommendation: `defer`
- `v1.3` should prioritize an artifact-driven read-only UI and a stronger robustness story before any second-dataset expansion work.
- The default milestone-initialization choice for `v1.3` is to skip fresh domain research and use the existing seeded artifact context directly.
- Phase 21 should default the artifact index to curated official milestone evidence and only expose exploratory artifacts through an explicit opt-in filter.
- Phase 21 should use generated, versioned JSON manifests as the authoritative UI contract; the later UI must not scan the filesystem directly.
- The Phase 21 contract must encode runs, evals, reports, seeded cohort summaries, mitigation lineage, and milestone stability conclusions as first-class manifest entities.
- Phase 21 should use an explicit build script plus a validator command rather than automatic rebuilds on UI load.
- Phase 21 manifest paths must stay relative and portable, and the schema must be compatible with later dataset expansion without breaking consumers.
- Phase 21 research recommends a single authoritative `index.json` at `artifacts/contracts/artifact_index/v1/index.json`, built from saved `metadata.json` plus existing JSON payloads instead of treating `experiments.jsonl` as the contract authority.
- Phase 21 planning treats absolute-path normalization, official-report closure, and the distinction between seeded comparison summaries and Phase 20 stability labels as the key contract risks to verify before the UI phase.
- Phase 21 is now complete with an official validated manifest at [index.json](/Users/padraigobrien/model-failure-lab/artifacts/contracts/artifact_index/v1/index.json).
- The official Phase 21 contract currently exposes `16` runs, `21` evaluations, `14` reports, four seeded cohort views, two mitigation comparison views, and one stability package view.
- The default-visible report story is now locked to the three official synthesis packages:
  - `phase18_temperature_scaling_seeded`
  - `phase19_reweighting_seeded`
  - `phase20_stability`
- The contract preserves both report-local seeded comparison semantics and milestone stability semantics:
  - `reweighting` seeded interpretation: `stable`
  - `reweighting` milestone stability label: `mixed`
  - dataset expansion recommendation: `defer`
- Phase 22 should default to a milestone-story-first landing page rather than an artifact browser or dense comparison table.
- Phase 22 should use a sidebar-style app with top-level views for:
  - Overview
  - Cohort Analysis
  - Mitigation Comparison
  - Stability
  - Artifacts
- Comparison views should be aggregate-first with optional per-seed expansion.
- Raw artifact access should stay always visible through lightweight actions like `View Report`, `Open Eval Bundle`, and `View Metadata`.
- The visual tone should be analytical and research-dashboard oriented, with light polish rather than branding-heavy presentation.
- Phase 22 UI must remain read-only and consume only `artifacts/contracts/artifact_index/v1/index.json`.
- Phase 22 planning recommends a Python-native `streamlit` app plus a repo-native `scripts/run_results_ui.py` launch surface instead of introducing a fresh JS toolchain in this phase.
- Phase 22 is now complete with a manifest-driven read-only explorer that renders:
  - `Overview`
  - `Cohort Analysis`
  - `Mitigation Comparison`
  - `Stability`
  - `Artifacts`
- The new UI keeps aggregate conclusions first, with per-seed details behind explicit expansion.
- Raw artifact drill-through is now available from the UI through lightweight `View Report`, `Open Bundle`, and `View Metadata` actions.
- Phase 23 should introduce exactly one new robustness-focused challenger lane instead of iterating on `reweighting`.
- Phase 23 should use a gated scout-first workflow: one scout seed first, then promote to the full official `13/42/87` cohort only if the challenger looks promising.
- The challenger should prioritize worst-group improvement first, OOD Macro F1 second, with guardrails against unacceptable ID or calibration regressions.
- Phase 23 promotion requires improvement over prior `reweighting` plus a clearer robustness story; strong promotion also means staying competitive with `temperature_scaling` on overall reliability.
- Phase 23 planning recommends `group_dro` as the single challenger lane because it best fits the current inherited DistilBERT retraining contract while targeting worst-group robustness directly.
- The scout run should use seed `13` first, then either promote cleanly to the full `13/42/87` cohort or stop without extra GPU spend.
- The artifact contract must branch on the challenger outcome: promoted `group_dro` becomes first-class and default-visible, while a failed scout remains exploratory-only.
- Phase 23 task 1 is now complete and committed as `e7c741a` (`feat: add group dro mitigation lane`).
- The repo now has a real `group_dro` mitigation preset, trainer, dispatch path, and focused scout-tag lineage tests.
- A blocking Phase 23 deviation is now committed as `2e45df8` (`fix: classify group dro as robustness lane`) so the future scout reports can classify `group_dro` honestly instead of defaulting to failure.
- A second Phase 23 deviation is now committed as `0ff3985` (`fix: tolerate unseen eval groups in group dro`) so saved validation/export splits do not crash when they contain groups that were unseen during training.
- The real seed-13 `group_dro` scout child is now complete at [metadata.json](/Users/padraigobrien/model-failure-lab/artifacts/mitigations/group_dro/distilbert/20260324_110658_group_dro_4d0e/metadata.json) with scout eval [metadata.json](/Users/padraigobrien/model-failure-lab/artifacts/mitigations/group_dro/distilbert/20260324_110658_group_dro_4d0e/evaluations/20260324_125802_shift_eval_8b02/metadata.json).
- The Phase 23 scout reports are now saved at [report.md](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md) and [report.md](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase23_four_way_scout_seed_13/20260324_130155_report_f31e/report.md).
- The Phase 23 scout outcome is explicit: `group_dro` is a `failure` versus the seed-13 parent baseline with OOD Macro F1 delta `-0.037`, worst-group F1 delta `-0.215`, and ECE delta `+0.033`.
- The promotion decision is `do_not_promote`, so no seed-42 or seed-87 challenger children were executed.
- A report-selection compatibility fix is now committed as `893aca1` (`fix: normalize legacy eval schema selection`) so legacy parent eval bundles without explicit `evaluation_schema_version` compare cleanly with newer scout eval bundles.
- The artifact-contract fix is now committed as `9214356` (`fix: keep scout mitigation artifacts exploratory`) so failed scouts remain exploratory-only and do not leak into the default milestone story.
- Phase 23 is now complete on the scout-stop branch: `temperature_scaling` remains the stable reference lane, `reweighting` remains mixed-but-usable, and `group_dro` is not worth promoting.
- Phase 24 should ship both a polished UI surface and a written findings package, with `README.md` routing readers to the UI first and the `v1.3` findings doc second.
- Phase 24 should upgrade UI auditability through contextual drillthrough on cards and charts rather than a heavy global evidence panel.
- The final `v1.3` narrative should foreground the comparative conclusion:
  - stable calibration via `temperature_scaling`
  - still-mixed robustness via `reweighting`
  - rejected `group_dro` scout
- The failed `group_dro` scout should be documented in the written findings, but remain outside default UI views and visible only through exploratory access.
- Phase 24 should refresh both `README.md` and add `docs/v1_3_findings.md` so the repo landing path finally matches the strongest saved evidence package.
- Phase 24 is now complete:
  - the UI exposes contextual drillthrough from official summary surfaces into saved reports, eval bundles, and raw tables
  - [README.md](/Users/padraigobrien/model-failure-lab/README.md) routes to the UI first and [v1_3_findings.md](/Users/padraigobrien/model-failure-lab/docs/v1_3_findings.md) second
  - the final public story is now locked as stable calibration, mixed robustness, rejected challenger, and continued dataset-expansion deferral
- Milestone `v1.3` is now archived locally in [v1.3-ROADMAP.md](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.3-ROADMAP.md) and [v1.3-REQUIREMENTS.md](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.3-REQUIREMENTS.md).
- Phase 25 task 1 is complete and committed as `0f43995` (`feat: add group balanced sampling mitigation lane`).
- The final bounded candidate lives in [group_balanced_sampling.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/mitigations/group_balanced_sampling.py) and persists an interpretable [sampling_weights.csv](/Users/padraigobrien/model-failure-lab/artifacts/mitigations/group_balanced_sampling/distilbert/20260324_203555_group_balanced_sampling_39ab/sampling_weights.csv) artifact that makes the capped blend-to-uniform recipe explicit.
- The real seed-13 `group_balanced_sampling` scout child is complete at [metadata.json](/Users/padraigobrien/model-failure-lab/artifacts/mitigations/group_balanced_sampling/distilbert/20260324_203555_group_balanced_sampling_39ab/metadata.json) with eval bundle [metadata.json](/Users/padraigobrien/model-failure-lab/artifacts/mitigations/group_balanced_sampling/distilbert/20260324_203555_group_balanced_sampling_39ab/evaluations/20260324_212817_shift_eval_75b2/metadata.json).
- The required Phase 25 scout reports now exist at [report.md](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase25_group_balanced_sampling_scout_seed_13/20260324_212920_report_7c22/report.md) and [report.md](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase25_four_way_scout_seed_13/20260324_212958_report_bcaa/report.md).
- The Phase 25 scout outcome is explicit: `group_balanced_sampling` is `do_not_promote`. It improved worst-group F1 over the seed-13 parent (`+0.153`) but regressed ID Macro F1 (`-0.118`), OOD Macro F1 (`-0.096`), ECE (`+0.116`), and Brier (`+0.092`), which is a weaker and less interpretable robustness story than the current `reweighting` reference.
- Phase 26 stays on the scout-stop branch and did not promote `group_balanced_sampling` to seeds `42/87`.
- Phase 26 shipped the dedicated final builder in commit `10a761c` (`feat: add final robustness report builder`).
- Phase 26 shipped the manifest ingest fix in commit `8e99ccc` (`fix: include robustness reports in artifact index`).
- The formal promotion audit now exists at [phase25_group_balanced_sampling.md](/Users/padraigobrien/model-failure-lab/artifacts/reports/robustness_promotion_audit/phase25_group_balanced_sampling.md) and records `do_not_promote`.
- The canonical final robustness package now exists at [report.md](/Users/padraigobrien/model-failure-lab/artifacts/reports/comparisons/phase26_robustness_final/20260324_221348_report_bfbb/report.md).
- The saved final robustness verdict is `still_mixed`, not `stronger`.
- The refreshed artifact contract now exposes `phase26_robustness_final` as official/default-visible while keeping `group_dro` and `group_balanced_sampling` scout entities exploratory-only.
- Phase 27 should close the research cycle through:
  - `README.md` -> UI first, `v1.4` closeout findings second
  - one machine-readable final gate saved as `defer_now_reopen_under_conditions`
  - small manifest-driven Overview messaging rather than a new UI view
- Phase 27 must document `group_dro` and `group_balanced_sampling` honestly in the closeout findings while keeping both exploratory-only in default UI views.
- The final dataset-expansion gate should reopen only if:
  - robustness becomes stably better rather than mixed
  - at least one mitigation shows consistent seeded gains
  - robustness-versus-calibration tradeoffs are materially reduced or better understood
- Phase 27 shipped the dedicated final-gate builder in commit `7f222db` (`feat: add final closeout gate surface`).
- The canonical closeout artifact now exists at [final_gate.json](/Users/padraigobrien/model-failure-lab/artifacts/reports/closeout/phase27_gate/final_gate.json).
- The final gate records:
  - final robustness verdict: `still_mixed`
  - dataset expansion decision: `defer_now_reopen_under_conditions`
  - explicit reopen conditions for any future second-dataset expansion
- The refreshed artifact contract now exposes one official/default-visible `research_closeout` view in [index.json](/Users/padraigobrien/model-failure-lab/artifacts/contracts/artifact_index/v1/index.json).
- The public repo entrypoints now match the final research state:
  - [README.md](/Users/padraigobrien/model-failure-lab/README.md) routes to the UI first and `v1.4` closeout second
  - [v1_4_closeout.md](/Users/padraigobrien/model-failure-lab/docs/v1_4_closeout.md) is the final written closeout
- The research cycle is now complete for this milestone:
  - stable calibration
  - still-mixed robustness
  - rejected exploratory challengers
  - deferred dataset expansion under explicit reopen conditions
- Phase 28 shipped the React frontend foundation in commits `3f337ee` (`feat(28-01): scaffold react frontend foundation`) and `a59c446` (`feat(28-01): add react manifest bridge`).
- The frontend now has a real manifest-backed route shell in [App.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/App.tsx) and [AppShell.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/layout/AppShell.tsx), with the locked top-level React navigation and explicit official/exploratory scope controls.
- The first real React route now exists at [OverviewPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/OverviewPage.tsx) and renders the final robustness verdict, expansion gate, official evidence counts, and `Inspect Failure Traces` CTA from the manifest.
- The manifest bridge is now parity-checked at [sync_react_ui_manifest.py](/Users/padraigobrien/model-failure-lab/scripts/sync_react_ui_manifest.py), and `python3 scripts/sync_react_ui_manifest.py --check` confirms the frontend-served contract matches the source artifact index exactly.
- Phase 29 shipped the manifest-linked report payload bridge in:
  - [reportData.ts](/Users/padraigobrien/model-failure-lab/frontend/src/lib/manifest/reportData.ts)
  - [load.ts](/Users/padraigobrien/model-failure-lab/frontend/src/lib/manifest/load.ts)
  - [selectors.ts](/Users/padraigobrien/model-failure-lab/frontend/src/lib/manifest/selectors.ts)
  so the React app can load saved `report_data.json` and `report_summary.json` content without hard-coded paths or client-side recomputation.

- The `Comparisons` route now exists at [ComparisonsPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonsPage.tsx) and leads with a ranked official-method canvas for `temperature_scaling`, `reweighting`, and baseline context.
- The `Failure Explorer` route now exists at [FailureExplorerPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/FailureExplorerPage.tsx) and exposes the four locked domains:
  - `Worst Group`
  - `OOD`
  - `ID`
  - `Calibration`
- Phase 29 kept shared React state intentionally lightweight:
  - selected method
  - selected domain
  with no full pinned debugger-session store.

- The static manifest bridge in [sync_react_ui_manifest.py](/Users/padraigobrien/model-failure-lab/scripts/sync_react_ui_manifest.py) now syncs referenced payload artifacts into `frontend/public`, and `python3 scripts/sync_react_ui_manifest.py --check` still confirms parity with the source contract.
- Phase 30 shipped grouped run cards by method, seed, and evidence scope instead of a flat inventory or lineage-first graph.
- Phase 30 drillthrough now supports both:
  - a default right-side evidence drawer that keeps the user in context
  - an `Open in Runs view` path for deeper inspection
- Phase 30 run detail follows the locked balanced stack:
  - lineage
  - summary
  - artifacts
- Phase 30 added page-level scope chips plus an explicit exploratory warning banner in the deeper run/evidence surfaces while preserving the existing global scope behavior.
- The React app can now move from ranked comparison or failure-domain summaries into run-level lineage and raw artifact refs without adding a backend or client-side recomputation.
- Phase 31 completed the repo handoff layer:
  - added one repo-root React launcher
  - rewrote `README.md` so React is the primary entrypoint
  - preserved Streamlit as the documented fallback
  - added a parity checklist in README plus `docs/ui_parity.md`
  - added a subtle primary/fallback note on the React Overview page
- Phase 32 shipped the workbench shell reframe in `c1077a8` (`feat(32-01): reframe shell as analytical workbench`).
- Phase 32 shipped the route-wide workbench propagation in `920fd6c` (`feat(32-02): propagate workbench ia across routes`).
- Phase 33 context is now locked in [33-CONTEXT.md](/Users/padraigobrien/model-failure-lab/.planning/phases/33-evidence-traceability-and-scope-surfaces/33-CONTEXT.md) around a lineage-first route model:
  - `Verdicts`
  - `Lanes`
  - `Runs`
  - `Evidence`
  - `Manifest`
- The approved Phase 33 UI contract in [33-UI-SPEC.md](/Users/padraigobrien/model-failure-lab/.planning/phases/33-evidence-traceability-and-scope-surfaces/33-UI-SPEC.md) makes `Verdicts` the default landing route, turns the right-side surface into a live inspector, and keeps official/exploratory scope globally persistent.
- The Phase 33 checker approved the UI contract with a non-blocking visual recommendation that is now folded into the spec: icon-only controls must provide `aria-label` plus tooltip or visible text fallback.
- Phase 33 is now planned in two execution waves:
  - `33-01` rewrites the route model to `Verdicts / Lanes / Runs / Evidence / Manifest`, adds URL-backed lineage selection, and preserves redirects from the old summary-mode paths
  - `33-02` turns the right-side dock into a live provenance inspector, adds the Manifest console, and reruns full frontend/build/parity verification
- Phase 32 now keeps persistent analytical state visible in [PersistentStateStrip.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/layout/PersistentStateStrip.tsx), including verdict, expansion gate, scope, focused lane, focused domain, and selected run.
- The React route inventory now shares one dense workbench hierarchy through [WorkbenchHeader.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/layout/WorkbenchHeader.tsx) and [WorkbenchSection.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/layout/WorkbenchSection.tsx) instead of falling back to route-local dashboard panels.
- The route surfaces [ComparisonsPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonsPage.tsx), [FailureExplorerPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/FailureExplorerPage.tsx), [RunsPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/RunsPage.tsx), and [EvidencePage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/EvidencePage.tsx) now read as one connected debugging workspace rather than separate summary pages.
- `python3 scripts/sync_react_ui_manifest.py --check` and [test_react_manifest_bridge.py](/Users/padraigobrien/model-failure-lab/tests/unit/test_react_manifest_bridge.py) still pass after the reframe, confirming that Phase 32 did not introduce a new backend or duplicated truth model.
- [Phase 36]: Phase 36 keeps scope in one router-backed context locked to ?scope=official and ?scope=all.
- [Phase 36]: The rebuilt shell is header-only, and the Verdict to Artifact chain comes from shared route metadata.
- [Phase 36]: Use one shared TraceRoutePlaceholder so every scaffold route exposes the same route label, question, params, and scope-preserving navigation contract.
- [Phase 36]: Treat the route-specific question as the page heading and keep route label and path as metadata, locking the one-question-per-screen scaffold behavior in tests.

### Blockers/Concerns

- New datasets remain intentionally deferred until the robustness-oriented mitigation story is stronger.
- This machine still lacks CUDA and MPS, so later repeated DistilBERT training or mitigation runs may continue to need cloud GPU support.

## Performance Metrics

| Phase | Duration | Tasks | Files |
|-------|----------|-------|-------|
| Phase 36 P01 | 7min | 2 tasks | 6 files |
| Phase 36 P02 | 13min | 2 tasks | 9 files |

## Session Continuity

Last session: 2026-03-26T11:07:28.911Z
Stopped at: Completed 36-02-PLAN.md
Resume file: None

## Next Step

Execute the trace-shell-and-route scaffold with `$gsd-execute-phase 36`
