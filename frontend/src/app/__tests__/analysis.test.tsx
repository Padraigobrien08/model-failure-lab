import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  ComparisonInventoryState,
  RunDetail,
  RunInventoryState,
} from "@/lib/artifacts/types";

const DEFAULT_SOURCE = {
  label: "Repo root artifact store",
  path: "/tmp/model-failure-lab",
  runsPath: "/tmp/model-failure-lab/runs",
  reportsPath: "/tmp/model-failure-lab/reports",
};

function buildReadyArtifactState(): ArtifactShellState {
  return {
    status: "ready",
    overview: {
      status: "ready",
      source: DEFAULT_SOURCE,
      runs: { count: 2, ids: ["run_alpha", "run_beta"] },
      comparisons: { count: 1, ids: ["compare_alpha_to_beta"] },
      issues: [],
      message: null,
    },
  };
}

function buildReadyRunInventoryState(): RunInventoryState {
  return {
    status: "ready",
    inventory: {
      source: DEFAULT_SOURCE,
      runs: [
        {
          runId: "run_alpha",
          dataset: "query-fixture-v1",
          model: "baseline-model",
          createdAt: "2026-04-01T10:00:00Z",
          status: "completed",
        },
        {
          runId: "run_beta",
          dataset: "query-fixture-v1",
          model: "candidate-model",
          createdAt: "2026-04-01T10:05:00Z",
          status: "completed",
        },
      ],
    },
    message: null,
  };
}

function buildReadyComparisonInventoryState(): ComparisonInventoryState {
  return {
    status: "ready",
    inventory: {
      source: DEFAULT_SOURCE,
      comparisons: [
        {
          reportId: "compare_alpha_to_beta",
          baselineRunId: "run_alpha",
          candidateRunId: "run_beta",
          dataset: "query-fixture-v1",
          createdAt: "2026-04-01T10:10:00Z",
          status: "regressed",
          compatible: true,
          signalVerdict: "regression",
          regressionScore: 0.27,
          improvementScore: 0.08,
          netScore: 0.19,
          severity: 0.27,
          topDrivers: [
            {
              driverRank: 0,
              failureType: "hallucination",
              delta: 0.18,
              direction: "regression",
              caseIds: ["case-regression"],
            },
          ],
        },
      ],
    },
    message: null,
  };
}

function buildRunDetail(runId: string): RunDetail {
  return {
    source: DEFAULT_SOURCE,
    run: {
      runId,
      dataset: "query-fixture-v1",
      model: "candidate-model",
      createdAt: "2026-04-01T10:05:00Z",
      status: "completed",
      reportId: `${runId}_report`,
      adapterId: "query_test_adapter",
      classifierId: "query_test_classifier",
      runSeed: 13,
    },
    metrics: {
      attemptedCaseCount: 4,
      classifiedCaseCount: 4,
      executionErrorCount: 0,
      unclassifiedCount: 0,
      successfulModelInvocationCount: 4,
      failureCaseCount: 2,
      failureRate: 0.5,
      classificationCoverage: 1,
      executionSuccessRate: 1,
    },
    summary: {
      failureTypes: [
        {
          label: "hallucination",
          count: 1,
          share: 0.25,
          caseIds: ["case-regression"],
        },
      ],
      expectationVerdicts: [
        {
          label: "unexpected_failure",
          count: 1,
          share: 0.25,
          caseIds: ["case-regression"],
        },
      ],
      tagSlices: [
        {
          tag: "delta",
          attemptedCaseCount: 3,
          classifiedCaseCount: 3,
          failureCaseCount: 2,
          failureRate: 2 / 3,
          expectationVerdictCounts: { unexpected_failure: 1 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: ["case-regression"],
      notableCaseIds: ["case-regression"],
      allCaseIds: ["case-stable", "case-improvement", "case-regression", "case-swap"],
      errorCaseIds: [],
    },
    cases: [
      {
        caseId: "case-regression",
        promptId: "case-regression",
        prompt: "Regression case",
        tags: ["delta"],
        outputText: "hallucination::Regression case",
        expectation: {
          expectedFailure: null,
          observedFailure: { failureType: "hallucination", failureSubtype: null },
          verdict: "unexpected_failure",
        },
        classification: {
          failure: { failureType: "hallucination", failureSubtype: null },
          confidence: 0.91,
          explanation: "Unsupported factual claim detected.",
        },
        error: null,
      },
    ],
  };
}

function buildClusterSummaryPayload() {
  return {
    cluster_id: "cd_cluster_reasoning_recurrence",
    cluster_kind: "comparison_delta",
    label: "reasoning · no_failure to failure",
    summary:
      "Reasoning no_failure to failure recurred 2 times across 2 saved comparisons in query-fixture-v1.",
    occurrence_count: 2,
    scope_count: 2,
    first_seen_at: "2026-04-01T09:50:00Z",
    last_seen_at: "2026-04-01T10:10:00Z",
    datasets: ["query-fixture-v1"],
    models: ["baseline-model→candidate-model"],
    failure_types: ["reasoning"],
    transition_types: ["no_failure_to_failure"],
    recent_severity: 0.27,
    representative_evidence: [
      {
        kind: "comparison_case",
        label: "compare_alpha_to_beta:case-regression",
        run_id: null,
        report_id: "compare_alpha_to_beta",
        case_id: "case-regression",
        prompt_id: "case-regression",
        section: "transitions",
        transition_type: "no_failure_to_failure",
      },
    ],
  };
}

function mockAnalysisQueryAndRunDetail() {
  const fetchMock = vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    if (url.includes("/__failure_lab__/artifacts/query.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          mode: "cases",
          filters: {
            failureType: "hallucination",
            model: null,
            dataset: null,
            runId: null,
            reportId: null,
            baselineRunId: null,
            candidateRunId: null,
            delta: null,
            aggregateBy: null,
            lastN: 5,
            since: null,
            until: null,
            limit: 20,
          },
          facets: {
            models: ["baseline-model", "candidate-model"],
            datasets: ["query-fixture-v1"],
            failureTypes: ["hallucination", "instruction_following", "reasoning"],
            deltaTypes: ["regression", "improvement", "swap"],
          },
          insight_report: {
            analysis_mode: "heuristic",
            source_kind: "cases",
            title: "Case insight report",
            summary: "Hallucination remains the dominant recurring failure signal in this filtered result set.",
            generated_by: "heuristic_v1",
            sampling: {
              total_matches: 1,
              sampled_matches: 1,
              sample_limit: 20,
              truncated: false,
              strategy: "ranked_representative_groups",
            },
            patterns: [
              {
                kind: "failure_type",
                label: "hallucination",
                summary: "Hallucination remains the dominant recurring failure mode across the selected runs.",
                group_key: "hallucination",
                count: 1,
                share: 1,
                evidence_refs: [
                  {
                    kind: "run_case",
                    label: "run_beta:case-regression",
                    run_id: "run_beta",
                    report_id: null,
                    case_id: "case-regression",
                    prompt_id: "case-regression",
                    section: "evidence",
                    transition_type: null,
                  },
                ],
              },
            ],
            anomalies: [],
            evidence_links: [
              {
                kind: "run_case",
                label: "run_beta:case-regression",
                run_id: "run_beta",
                report_id: null,
                case_id: "case-regression",
                prompt_id: "case-regression",
                section: "evidence",
                transition_type: null,
              },
            ],
          },
          rows: [
            {
              run_id: "run_beta",
              dataset: "query-fixture-v1",
              model: "candidate-model",
              created_at: "2026-04-01T10:05:00Z",
              case_id: "case-regression",
              prompt_id: "case-regression",
              prompt: "Regression case",
              tags: ["delta"],
              failure_type: "hallucination",
              expectation_verdict: "unexpected_failure",
              explanation: "Unsupported factual claim detected.",
              confidence: 0.91,
              error_stage: null,
            },
          ],
        }),
      } as Response;
    }

    if (url.includes("/__failure_lab__/artifacts/run-detail.json?runId=run_beta")) {
      return {
        ok: true,
        status: 200,
        json: async () => buildRunDetail("run_beta"),
      } as Response;
    }

    if (url.includes("/__failure_lab__/artifacts/harvest.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          dataset_id: "analysis-cases-hallucination",
          lifecycle: "draft",
          mode: "cases",
          output_path: "datasets/harvested/analysis-cases-hallucination.json",
          selected_case_count: 1,
        }),
      } as Response;
    }

    return {
      ok: false,
      status: 404,
      json: async () => ({ message: `Unexpected request: ${url}` }),
    } as Response;
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function mockSignalAnalysisQuery() {
  const fetchMock = vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    if (url.includes("/__failure_lab__/artifacts/query.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          mode: "signals",
          filters: {
            failureType: "hallucination",
            model: null,
            dataset: null,
            runId: null,
            reportId: null,
            baselineRunId: null,
            candidateRunId: null,
            delta: null,
            aggregateBy: null,
            lastN: 10,
            since: null,
            until: null,
            limit: 20,
          },
          facets: {
            models: ["baseline-model", "candidate-model"],
            datasets: ["query-fixture-v1"],
            failureTypes: ["hallucination", "instruction_following", "reasoning"],
            deltaTypes: ["regression", "improvement", "swap"],
          },
          insight_report: null,
          rows: [
            {
              report_id: "compare_alpha_to_beta",
              created_at: "2026-04-01T10:10:00Z",
              dataset: "query-fixture-v1",
              baseline_run_id: "run_alpha",
              candidate_run_id: "run_beta",
              baseline_model: "baseline-model",
              candidate_model: "candidate-model",
              status: "regressed",
              compatible: true,
              signal_verdict: "regression",
              regression_score: 0.27,
              improvement_score: 0.08,
              net_score: 0.19,
              severity: 0.27,
              top_drivers: [
                {
                  driver_rank: 0,
                  failure_type: "hallucination",
                  delta: 0.18,
                  direction: "regression",
                  case_ids: ["case-regression"],
                },
              ],
              governance_recommendation: {
                comparison_id: "compare_alpha_to_beta",
                action: "create",
                policy_rule: "new_family_required",
                rationale:
                  "Qualifying regression has no existing family match, so governance recommends creating `regression-query-fixture-v1-hallucination`.",
                policy: {
                  minimum_severity: 0.05,
                  top_n: 10,
                  failure_type: null,
                  family_id: null,
                  family_case_cap: 200,
                  max_duplicate_ratio: 0.6,
                  recurrence_window: 5,
                  recurrence_threshold: 2,
                  strategy: "exact_suggested_family_then_health_guards",
                },
                signal: {
                  verdict: "regression",
                  reason: null,
                  regression_score: 0.27,
                  improvement_score: 0.08,
                  net_score: 0.19,
                  severity: 0.27,
                  top_drivers: [
                    {
                      driver_rank: 0,
                      failure_type: "hallucination",
                      delta: 0.18,
                      direction: "regression",
                      case_ids: ["case-regression"],
                    },
                  ],
                },
                matched_family: {
                  family_id: "regression-query-fixture-v1-hallucination",
                  match_kind: "suggested_new",
                  exists: false,
                  version_count: 0,
                  latest_dataset_id: null,
                  current_case_count: 0,
                  proposed_addition_count: 1,
                  duplicate_case_count: 0,
                  duplicate_ratio: 0,
                  projected_case_count: 1,
                  family_case_cap: 200,
                  cap_reached: false,
                  duplicate_ratio_exceeded: false,
                },
                selected_case_count: 1,
                evidence_case_ids: ["case-regression"],
                preview_cases: [
                  {
                    case_id: "case-regression-pack-001",
                    prompt_id: "case-regression",
                    prompt: "Regression case",
                    source_case_id: "case-regression",
                    source_report_id: "compare_alpha_to_beta",
                    source_run_id: "run_beta",
                    driver_failure_type: "hallucination",
                    driver_rank: 0,
                    transition_type: "no_failure_to_failure",
                  },
                ],
                cluster_context: [buildClusterSummaryPayload()],
                history_context: {
                  scope_kind: "dataset",
                  scope_value: "query-fixture-v1",
                  recent_comparison_count: 3,
                  recent_regression_count: 2,
                  comparison_trend: {
                    label: "degrading",
                    delta: 0.12,
                    sample_count: 3,
                    first_value: -0.04,
                    last_value: 0.08,
                    volatility: 0.06,
                    volatility_label: "medium",
                  },
                  candidate_run_trend: {
                    label: "degrading",
                    delta: 0.2,
                    sample_count: 2,
                    first_value: 0.3,
                    last_value: 0.5,
                    volatility: 0.2,
                    volatility_label: "high",
                  },
                  recurring_failures: [
                    {
                      failure_type: "hallucination",
                      occurrences: 2,
                      comparison_ids: [
                        "compare_alpha_to_beta",
                        "compare_beta_to_gamma",
                      ],
                      latest_delta: 0.18,
                    },
                  ],
                  recent_comparisons: [
                    {
                      report_id: "compare_alpha_to_beta",
                      created_at: "2026-04-01T10:10:00Z",
                      dataset: "query-fixture-v1",
                      baseline_run_id: "run_alpha",
                      candidate_run_id: "run_beta",
                      baseline_model: "baseline-model",
                      candidate_model: "candidate-model",
                      status: "regressed",
                      compatible: true,
                      signal_verdict: "regression",
                      regression_score: 0.27,
                      improvement_score: 0.08,
                      net_score: 0.19,
                      severity: 0.27,
                      top_drivers: [
                        {
                          driver_rank: 0,
                          failure_type: "hallucination",
                          delta: 0.18,
                          direction: "regression",
                          case_ids: ["case-regression"],
                        },
                      ],
                    },
                  ],
                  family_health: {
                    family_id: "regression-query-fixture-v1-hallucination",
                    health_label: "degrading",
                    trend: {
                      label: "degrading",
                      delta: 0.1,
                      sample_count: 2,
                      first_value: 0.25,
                      last_value: 0.35,
                      volatility: 0.1,
                      volatility_label: "high",
                    },
                    version_count: 2,
                    evaluation_run_count: 4,
                    recent_fail_rate: 0.35,
                    previous_fail_rate: 0.25,
                    latest_dataset_id: "regression-query-fixture-v1-hallucination-v2",
                    latest_version_tag: "v2",
                    latest_created_at: "2026-04-01T11:00:00Z",
                    source_dataset_id: "query-fixture-v1",
                    primary_failure_type: "hallucination",
                  },
                },
              },
            },
          ],
        }),
      } as Response;
    }

    if (url.includes("/__failure_lab__/artifacts/regression-pack.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          dataset_id: "regression-query-fixture-v1-hallucination-draft",
          lifecycle: "draft",
          comparison_id: "compare_alpha_to_beta",
          suggested_family_id: "regression-query-fixture-v1-hallucination",
          output_path:
            "datasets/harvested/regression-query-fixture-v1-hallucination-draft.json",
          selected_case_count: 1,
          policy: {
            top_n: 10,
            failure_type: "hallucination",
            strategy: "top_signal_driver_cases",
            delta_kind: "regression",
          },
          signal: {
            verdict: "regression",
            reason: null,
            regression_score: 0.27,
            improvement_score: 0.08,
            net_score: 0.19,
            severity: 0.27,
            top_drivers: [
              {
                driver_rank: 0,
                failure_type: "hallucination",
                delta: 0.18,
                direction: "regression",
                case_ids: ["case-regression"],
              },
            ],
          },
          preview_cases: [
            {
              case_id: "case-regression-pack-001",
              prompt_id: "case-regression",
              prompt: "Regression case",
              source_case_id: "case-regression",
              source_report_id: "compare_alpha_to_beta",
              source_run_id: "run_beta",
              driver_failure_type: "hallucination",
              driver_rank: 0,
              transition_type: "no_failure_to_failure",
            },
          ],
        }),
      } as Response;
    }

    if (url.includes("/__failure_lab__/artifacts/dataset-versions.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          family_id: "regression-query-fixture-v1-hallucination",
          versions: [],
          history: {
            scope_kind: "family",
            scope_value: "regression-query-fixture-v1-hallucination",
            run_history: [],
            comparison_history: [],
            run_trend: null,
            comparison_trend: null,
            recurring_failures: [],
            dataset_versions: [],
            dataset_health: {
              family_id: "regression-query-fixture-v1-hallucination",
              health_label: "degrading",
              trend: {
                label: "degrading",
                delta: 0.1,
                sample_count: 2,
                first_value: 0.25,
                last_value: 0.35,
                volatility: 0.1,
                volatility_label: "high",
              },
              version_count: 2,
              evaluation_run_count: 4,
              recent_fail_rate: 0.35,
              previous_fail_rate: 0.25,
              latest_dataset_id: "regression-query-fixture-v1-hallucination-v2",
              latest_version_tag: "v2",
              latest_created_at: "2026-04-01T11:00:00Z",
              source_dataset_id: "query-fixture-v1",
              primary_failure_type: "hallucination",
            },
          },
        }),
      } as Response;
    }

    return {
      ok: false,
      status: 404,
      json: async () => ({ message: `Unexpected request: ${url}` }),
    } as Response;
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function mockClusterAnalysisQuery() {
  const fetchMock = vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    if (url.includes("/__failure_lab__/artifacts/query.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          mode: "clusters",
          filters: {
            failureType: "reasoning",
            model: null,
            dataset: null,
            runId: null,
            reportId: null,
            baselineRunId: null,
            candidateRunId: null,
            delta: null,
            aggregateBy: null,
            clusterKind: null,
            includeNonRecurring: false,
            lastN: 10,
            since: null,
            until: null,
            limit: 20,
          },
          facets: {
            models: ["baseline-model", "candidate-model"],
            datasets: ["query-fixture-v1"],
            failureTypes: ["hallucination", "instruction_following", "reasoning"],
            deltaTypes: ["regression", "improvement", "swap"],
          },
          insight_report: null,
          rows: [buildClusterSummaryPayload()],
        }),
      } as Response;
    }

    return {
      ok: false,
      status: 404,
      json: async () => ({ message: `Unexpected request: ${url}` }),
    } as Response;
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("analysis route", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.history.replaceState({}, "", "/");
  });

  it("renders query-backed case results with URL-backed filters", async () => {
    const fetchMock = mockAnalysisQueryAndRunDetail();

    render(
      <App
        useMemoryRouter
        initialEntries={["/analysis?mode=cases&failureType=hallucination&lastN=5"]}
        initialArtifactState={buildReadyArtifactState()}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Cross-run artifact analysis." }),
    ).toBeInTheDocument();
    expect(screen.getByText("Grounded cross-run readout")).toBeInTheDocument();
    expect(screen.getByText("Regression case")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/__failure_lab__/artifacts/query.json?mode=cases&failureType=hallucination&lastN=5&limit=20&summarize=1",
      ),
    );
  });

  it("preserves the analysis route as the return target when opening run evidence", async () => {
    const user = userEvent.setup();
    mockAnalysisQueryAndRunDetail();

    render(
      <App
        useMemoryRouter
        initialEntries={["/analysis?mode=cases&failureType=hallucination"]}
        initialArtifactState={buildReadyArtifactState()}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    await user.click(await screen.findByRole("link", { name: "Inspect run evidence" }));

    expect(
      await screen.findByRole("heading", { name: "Selected case evidence" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to runs" })).toHaveAttribute(
      "href",
      "/analysis?mode=cases&failureType=hallucination",
    );
  });

  it("exports the filtered result set as a draft dataset", async () => {
    const user = userEvent.setup();
    const fetchMock = mockAnalysisQueryAndRunDetail();

    render(
      <App
        useMemoryRouter
        initialEntries={["/analysis?mode=cases&failureType=hallucination&lastN=5"]}
        initialArtifactState={buildReadyArtifactState()}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    await user.click(await screen.findByRole("button", { name: "Export draft dataset" }));

    expect(await screen.findByRole("heading", { name: "Draft dataset exported." })).toBeInTheDocument();
    expect(
      screen.getByText(/analysis-cases-hallucination was written to datasets\/harvested\/analysis-cases-hallucination\.json/i),
    ).toBeInTheDocument();

    await waitFor(() => {
      const harvestCall = fetchMock.mock.calls.find(([input]) =>
        String(input).includes("/__failure_lab__/artifacts/harvest.json"),
      ) as [string | URL | Request, RequestInit?] | undefined;
      expect(harvestCall).toBeTruthy();
      const init = harvestCall?.[1];
      expect(init).toBeDefined();
      if (!init) {
        throw new Error("Expected harvest request init");
      }
      expect(init).toMatchObject({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      expect(JSON.parse(String(init.body))).toEqual({
        mode: "cases",
        filters: {
          failureType: "hallucination",
          model: "",
          dataset: "",
          runId: "",
          promptId: "",
          reportId: "",
          baselineRunId: "",
          candidateRunId: "",
          delta: "",
          lastN: 5,
          since: "",
          until: "",
          limit: 20,
        },
        outputStem: "analysis-cases-hallucination",
      });
    });
  });

  it("renders comparison signal rows without enabling draft export", async () => {
    const fetchMock = mockSignalAnalysisQuery();

    render(
      <App
        useMemoryRouter
        initialEntries={["/analysis?mode=signals&signalDirection=regression&failureType=hallucination&lastN=10"]}
        initialArtifactState={buildReadyArtifactState()}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Cross-run artifact analysis." }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Grounded cross-run readout")).not.toBeInTheDocument();
    expect(screen.getByText("compare_alpha_to_beta")).toBeInTheDocument();
    expect(screen.getByText("27.0% severity")).toBeInTheDocument();
    expect(screen.getAllByText("create").length).toBeGreaterThan(0);
    expect(screen.getAllByText("degrading trend").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2 recent regressions").length).toBeGreaterThan(0);
    expect(screen.getByText("1 recurring clusters")).toBeInTheDocument();
    expect(screen.getByText("hallucination x2")).toBeInTheDocument();
    expect(screen.getByText("hallucination +18.0%")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Qualifying regression has no existing family match, so governance recommends creating `regression-query-fixture-v1-hallucination`.",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("link", { name: "Inspect strongest driver" }),
    ).toHaveAttribute(
      "href",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-regression",
    );
    expect(
      screen.queryByRole("button", { name: "Export draft dataset" }),
    ).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/__failure_lab__/artifacts/query.json?mode=signals&signalDirection=regression&failureType=hallucination&lastN=10&limit=20&summarize=1",
      ),
    );
  });

  it("can turn a signal row into a draft regression pack", async () => {
    const user = userEvent.setup();
    const fetchMock = mockSignalAnalysisQuery();

    render(
      <App
        useMemoryRouter
        initialEntries={["/analysis?mode=signals&signalDirection=regression&failureType=hallucination&lastN=10"]}
        initialArtifactState={buildReadyArtifactState()}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Cross-run artifact analysis." }),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Generate draft pack" }),
    );

    expect(
      await screen.findByText("regression-query-fixture-v1-hallucination-draft"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "datasets/harvested/regression-query-fixture-v1-hallucination-draft.json",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("No immutable versions exist yet for regression-query-fixture-v1-hallucination.")).toBeInTheDocument();

    await waitFor(() => {
      const packCall = fetchMock.mock.calls.find(([input]) =>
        String(input).includes("/__failure_lab__/artifacts/regression-pack.json"),
      ) as [string | URL | Request, RequestInit?] | undefined;
      expect(packCall).toBeTruthy();
      const init = packCall?.[1];
      expect(init).toBeDefined();
      if (!init) {
        throw new Error("Expected regression pack request init");
      }
      expect(init).toMatchObject({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      expect(JSON.parse(String(init.body))).toEqual({
        comparisonId: "compare_alpha_to_beta",
        familyId: "regression-query-fixture-v1-hallucination",
        failureType: "hallucination",
      });
    });
  });

  it("renders recurring cluster rows with direct evidence drillthrough", async () => {
    const fetchMock = mockClusterAnalysisQuery();

    render(
      <App
        useMemoryRouter
        initialEntries={["/analysis?mode=clusters&failureType=reasoning&lastN=10"]}
        initialArtifactState={buildReadyArtifactState()}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Cross-run artifact analysis." }),
    ).toBeInTheDocument();
    expect(screen.getByText("reasoning · no_failure to failure")).toBeInTheDocument();
    expect(screen.getByText("2 artifacts")).toBeInTheDocument();
    expect(screen.getByText("2 occurrences")).toBeInTheDocument();
    expect(screen.getByText("27.0% severity")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "compare_alpha_to_beta:case-regression" }),
    ).toHaveAttribute(
      "href",
      expect.stringContaining(
        "/comparisons/compare_alpha_to_beta?section=transitions&case=case-regression",
      ),
    );
    expect(
      screen.queryByRole("button", { name: "Export draft dataset" }),
    ).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/__failure_lab__/artifacts/query.json?mode=clusters&failureType=reasoning&lastN=10&limit=20&summarize=1",
      ),
    );
  });
});
