# Code Inventory

> Baseline audit, generated 2026-06-29. Counts are mechanical (grep/find). "Public functions" =
> module-level `def` not prefixed with `_`. Class lists are exhaustive for `src/`. Tag = audit
> classification (PROD = production path, LEG = legacy/reference, MIX = both).

## Package inventory (`src/model_failure_lab/`)

142 `.py` files, ~35,546 LOC.

| Package | Tag | Public fns* | Responsibility |
|---|---|---|---|
| (root) `cli.py` | PROD | 2 | Argparse CLI surface, 44 `_handle_*` handlers (4,157 LOC) |
| (root) `clusters.py` | PROD | 3 | Recurring failure cluster summaries |
| (root) `history.py` | PROD | 6 | Run/comparison/dataset history snapshots |
| (root) `__init__.py` / `__main__.py` | PROD | 11 | Package exports + `python -m` entry |
| `adapters/` | PROD | 4 | Model adapter protocol, registry, demo/ollama/anthropic/openai |
| `classifiers/` | PROD | 5 | Classifier type, registry, heuristic_v1 |
| `runner/` | PROD | 6 | Dataset execution + run/results artifacts |
| `storage/` | PROD | 22 | CWD-relative artifact layout + JSON IO |
| `schemas/` | PROD | 3 | Run/Result/Report/PromptCase dataclasses + taxonomy |
| `datasets/` | PROD | 15 | Load bundled/local datasets; evolution/versioning |
| `index/` | PROD | 16 | Derived SQLite query index (build/query/contracts) |
| `analysis/` | PROD | 9 | Grounded insight reports & comparison explainers |
| `governance/` | PROD | 35 | Policy, gates, lifecycle, portfolio, outcomes, baselines |
| `harvest/` | PROD | 4 | Harvest + duplicate review + promotion |
| `testing/` | PROD | 3 | Insight fixture workspace builders (test support) |
| `reporting/` | MIX | 74 | core/compare (PROD) + bundle/figures/stability/… (LEG, pandas/matplotlib) |
| `utils/` | MIX | 29 | `paths.py` (legacy roots), `runtime.py` |
| `config/` | LEG | 2 | YAML `RunConfig` loader/schema |
| `runners/` | LEG | 8 | `dispatch.py` benchmark run dispatch (943 LOC) |
| `tracking/` | LEG | 14 | Run-id/metrics/manifest tracking |
| `artifact_index/` | LEG | 9 | JSON manifest artifact index (build/load/validate) |
| `models/` | LEG | 9 | DistilBERT + logistic-TF-IDF baselines (torch/sklearn) |
| `mitigations/` | LEG | 12 | Group DRO, reweighting, temperature scaling, sampling |
| `perturbations/` | LEG | 17 | Perturbation suite generation/scoring/metrics |
| `evaluation/` | LEG | 16 | Aggregate/subgroup/calibration/robustness metrics |
| `data/` | LEG | 18 | CivilComments load + canonical materialization |
| `results_ui/` | LEG | 35 | Streamlit dashboard |

*Public top-level functions only; methods and private helpers excluded.

## Classes (exhaustive, `src/`)

> 45 modules use `@dataclass`. Grouped by area; `(E)` = Exception, `(P)` = Protocol, `(D)` = Dataset
> subclass (torch).

| Area | Classes |
|---|---|
| `adapters` | `ModelAdapter`(P), `ModelMetadata`, `ModelRequest`, `ModelResult`, `ModelUsage`, `DemoAdapter`, `OllamaAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `UnknownModelAdapterError`(E) |
| `classifiers` | `ClassifierExpectations`, `ClassifierInput`, `ClassifierResult`, `UnknownClassifierError`(E) |
| `schemas` | `PromptCase`, `PromptExpectations`, `PromptContextExpectations`, `Run`, `Result`, `Report`, `FailureLabel`, `PayloadValidationError`(E) |
| `runner` | `CaseClassification`, `CaseError`, `CaseExecution`, `CaseExpectationAssessment`, `CaseOutput`, `ExecutionMetadata`, `PromptSnapshot`, `DatasetRunExecution` |
| `datasets` | `BundledDatasetSpec`, `BundledDatasetSummary`, `UnknownBundledDatasetError`(E), `FailureDataset`, `LocalDatasetSummary`, `DatasetEvolutionSummary`, `DatasetVersionRecord`, `RegressionPackDraftSummary`, `RegressionPackPolicy`, `RegressionPackPreviewCase`, `RegressionPackSelectionSummary` |
| `analysis` | `InsightEvidenceRef`, `InsightPattern`, `InsightReport`, `InsightSampling` |
| `clusters` | `ClusterEvidenceRef`, `FailureClusterDetail`, `FailureClusterOccurrence`, `FailureClusterSummary` |
| `history` | `ComparisonHistoryRecord`, `DatasetHealthSummary`, `DatasetVersionHistoryRecord`, `HistorySnapshot`, `MetricTrend`, `RecurringFailurePattern`, `RunHistoryRecord`, `SignalHistoryContext` |
| `index` | `QueryIndexSummary`, `ArtifactContractValidation`, `QueryFilters` |
| `governance` | `BaselineEntry`; gates: `GateDecision`, `GateWaiver`, `RegressionGateResult`; policy: `GovernanceEscalation`, `GovernanceFamilyMatch`, `GovernancePolicy`, `GovernanceRecommendation`, `LifecycleRecommendation`; lifecycle: `LifecycleActionRecord`, `LifecycleApplyResult`; workflow: `DatasetFamilyHealth`, `DatasetLifecycleAlert`, `GovernanceApplyResult`; intelligence: `RootCauseSummary`; execution: `PortfolioExecutionFollowUp`, `PortfolioExecutionSnapshot`, `PortfolioPlanExecution`, `PortfolioPlanExecutionCheckpoint`, `PortfolioPlanExecutionReceipt`, `PortfolioPlanExecutionResult`, `PortfolioPlanPreflight`, `PortfolioPlanPreflightCheck`; outcomes: `PortfolioExecutionOutcome`, `PortfolioOutcomeAttestation`, `PortfolioOutcomeDeltaSummary`, `PortfolioOutcomeFeedbackSummary`, `PortfolioOutcomeSignalSummary`, `PortfolioOutcomeVerdict`; portfolio: `DatasetPlanningUnit`, `DatasetPortfolioItem`, `PlanningUnitMember`, `PortfolioComparisonReference`, `PortfolioFilters`, `PortfolioPlanAction`, `PortfolioPlanApplyResult`, `PortfolioPlanImpact`, `PortfolioPlanSaveResult`, `SavedPortfolioPlan`, `_FamilyPortfolioEvidence` |
| `harvest` | `HarvestDraftSummary`, `HarvestDuplicateGroup`, `HarvestPromotionSummary`, `HarvestReviewSummary` |
| `reporting` (PROD part) | `BuiltReport`, `CaseSummary`, `PerturbationReportCandidate`, `ReportCandidate`, `SavedRunArtifacts` |
| `testing` | `InsightFixtureAdapter`, `InsightFixtureClassifier`, `InsightFixtureComparison`, `InsightFixtureRun`, `InsightFixtureWorkspace` |
| `runners` (LEG) | `DispatchResult` |
| `data` (LEG) | `TfidfAdapterView`, `TransformerAdapterView`, `DataDependencyError`(E), `SplitRole`, `MaterializationResult`, `RuntimeDatasetResult`, `CanonicalDataset`, `CanonicalSample` |
| `models` (LEG) | `DistilBertBaselineArtifacts`, `TokenizedTextDataset`(D), `LogisticBaselineArtifacts` |
| `mitigations` (LEG) | `DistilBertGroupBalancedSamplingArtifacts`, `DistilBertGroupDroArtifacts`, `GroupDroTokenizedTextDataset`(D), `DistilBertReweightingArtifacts`, `WeightedTokenizedTextDataset`(D), `TemperatureScalingArtifacts` |
| `perturbations` (LEG) | `PerturbationSuite`, `PerturbedSample`, `SavedRunScorer` |
| `config` (LEG) | `RunConfig` |

## Scripts (`scripts/`)

| Script | Tag | Purpose (from `description=`/docstring) |
|---|---|---|
| `_bootstrap.py` | — | Ensure repo-root script execution can import project packages |
| `smoke_package_install.py` | PROD | Install-surface smoke proving the packaged CLI works end-to-end |
| `generate_insight_fixture.py` | PROD | Generate an insight fixture workspace |
| `query_bridge.py` | PROD | Bridge the query index for the React UI / tooling |
| `run_react_ui.py` | PROD | Launch the React failure debugger UI (shells out to npm) |
| `sync_react_ui_manifest.py` | PROD | Sync artifact-index contract into the React UI static path |
| `build_artifact_index.py` | MIX | Build the versioned artifact-index contract from saved artifacts |
| `validate_artifact_index.py` | MIX | Validate the generated artifact-index contract |
| `check_environment.py` | LEG | Verify benchmark runtime prerequisites |
| `download_data.py` | LEG | Bootstrap the CivilComments data-download workflow |
| `run_baseline.py` | LEG | Bootstrap a baseline experiment run |
| `run_mitigation.py` | LEG | Bootstrap a mitigation experiment run |
| `run_perturbation_eval.py` | LEG | Materialize a deterministic perturbation suite for a saved run |
| `run_shift_eval.py` | LEG | Evaluate a saved baseline or mitigation run |
| `build_report.py` | LEG | Bootstrap a report build run |
| `build_perturbation_report.py` | LEG | Bootstrap a perturbation report build run |
| `build_robustness_report.py` | LEG | Build a robustness report |
| `build_stability_report.py` | LEG | Build a seeded stability report from official eval bundles |
| `build_final_gate.py` | LEG | Build the final dataset-expansion gate artifact |
| `check_phase17_seed_cohorts.py` | LEG | Inspect Phase 17 baseline seed cohorts |
| `run_results_ui.py` | LEG | Launch the read-only Streamlit results explorer |
| `run_phase17_distilbert_seeds.sh` | LEG | Run Phase 17 DistilBERT seed cohorts (shell) |
| `finalize_phase17_distilbert_runs.sh` | LEG | Finalize Phase 17 DistilBERT runs (shell) |

## Configuration files

| File | Purpose |
|---|---|
| `pyproject.toml` | Package metadata, extras, scripts, ruff/pytest config |
| `Makefile` | Dev/build/test/publish targets |
| `.github/workflows/ci.yml` | CI: install `.[dev,legacy]`, pytest, ruff, CLI smoke |
| `.gitignore` | Ignores secrets, artifacts, build, node_modules, `.planning/`, `.codex/` |
| `configs/README.md` + `configs/{data,model,train,eval,experiments}/*.yaml` | **Legacy** CivilComments/DistilBERT experiment presets (17 YAML files) |
| `frontend/package.json`, `tsconfig*.json`, `vite.config.ts`, `vitest.config.ts`, `tailwind.config.ts`, `postcss.config.js`, `components.json` | Frontend build/test/styling config |
| `.codex/config.toml`, `.codex/gsd-file-manifest.json` | Tooling config (gitignored dir) |

## Assets / data

| Asset | Location | Notes |
|---|---|---|
| Bundled datasets (JSON) | `src/model_failure_lab/datasets/*.json` | `reasoning_failures`, `rag_failures`, `hallucination_failures`, `demo_dataset`, `customer_support_failures` (packaged via `package-data`) |
| Query index DB | `.failure_lab/query_index.sqlite3` | Derived, gitignored, rebuildable |
| Prebuilt distributions | `dist/model_failure_lab-0.1.0-{whl,tar.gz}` | |
| Screenshots | `docs/screens/` (referenced by README) | Image files not confirmed present in audit |

## Frontend inventory (`frontend/src/`)

| Area | Contents |
|---|---|
| App shell / routing | `app/App.tsx`, `app/router.tsx`, `app/scope.tsx`, `main.tsx` |
| Route pages | `app/routes/` — ~20 pages (Overview, Runs, RunDetail, Comparisons, ComparisonDetail, Analysis, FailureExplorer, Method, Lane, Summary, RawDebug, Evidence, Manifest, + placeholders) |
| Components | `components/ui/` (button/card/badge/tabs), `components/lane/`, `components/comparisons/`, `components/insights/` |
| Libraries | `lib/artifacts/` (load/navigation/types), `lib/manifest/` (load/selectors/types/reportData), route helpers, `lib/formatters.ts`, `lib/utils.ts` |
| Tests | 28 Vitest files under `app/__tests__/` and `lib/**/__tests__/` |

## Tests (`tests/unit/`)

60 test files. Largest: `test_script_entrypoints.py` (2,575 LOC), `test_cli_demo_compare.py` (1,273),
`test_cli.py` (844), `test_cli_governance.py` (767), `test_report_bundle.py` (748). See
`docs/code-map.md` for the change-to-test map.
