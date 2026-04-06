import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactDatasetPortfolioItem,
  ArtifactGovernanceRecommendation,
  ArtifactShellState,
  ComparisonDetail,
  ComparisonInventoryItem,
  ComparisonInventoryState,
  RunDetail,
  RunInventoryState,
} from "@/lib/artifacts/types";

function buildReadyState(comparisonIds: string[]): ArtifactShellState {
  return {
    status: "ready",
    overview: {
      status: "ready",
      source: {
        label: "Repo root artifact store",
        path: "/tmp/model-failure-lab",
        runsPath: "/tmp/model-failure-lab/runs",
        reportsPath: "/tmp/model-failure-lab/reports",
      },
      runs: {
        count: 2,
        ids: ["run_alpha", "run_beta"],
      },
      comparisons: {
        count: comparisonIds.length,
        ids: comparisonIds,
      },
      issues: [],
      message: null,
    },
  };
}

function buildReadyInventoryState(): RunInventoryState {
  return {
    status: "ready",
    inventory: {
      source: {
        label: "Repo root artifact store",
        path: "/tmp/model-failure-lab",
        runsPath: "/tmp/model-failure-lab/runs",
        reportsPath: "/tmp/model-failure-lab/reports",
      },
      runs: [
        {
          runId: "run_alpha",
          dataset: "reasoning-failures-v1",
          model: "demo",
          createdAt: "2026-03-29T09:00:00Z",
          status: "completed",
        },
        {
          runId: "run_beta",
          dataset: "hallucination-failures-v1",
          model: "gpt-4.1-mini",
          createdAt: "2026-03-30T11:30:00Z",
          status: "completed",
        },
      ],
    },
    message: null,
  };
}

function buildReadyComparisonInventoryState(
  comparisons: ComparisonInventoryItem[],
): ComparisonInventoryState {
  return {
    status: "ready",
    inventory: {
      source: {
        label: "Repo root artifact store",
        path: "/tmp/model-failure-lab",
        runsPath: "/tmp/model-failure-lab/runs",
        reportsPath: "/tmp/model-failure-lab/reports",
      },
      comparisons,
    },
    message: null,
  };
}

function buildSignalInventoryFields(
  verdict: string,
  severity: number,
  driver?: { failureType: string; delta: number; caseIds: string[] },
) {
  const topDrivers =
    driver === undefined
      ? []
      : [
          {
            driverRank: 0,
            failureType: driver.failureType,
            delta: driver.delta,
            direction: driver.delta >= 0 ? "regression" : "improvement",
            caseIds: driver.caseIds,
          },
        ];

  return {
    signalVerdict: verdict,
    regressionScore: verdict === "regression" ? severity : 0,
    improvementScore: verdict === "improvement" ? severity : 0,
    netScore: verdict === "improvement" ? -severity : severity,
    severity,
    topDrivers,
  };
}

function buildInventoryGovernanceRecommendation(
  overrides: Partial<ArtifactGovernanceRecommendation> = {},
): ArtifactGovernanceRecommendation {
  return {
    comparisonId: "compare_alpha_to_beta",
    action: "evolve",
    policyRule: "existing_family_match",
    rationale:
      "Qualifying regression matches existing family `regression-reasoning-failures-v1-hallucination`.",
    policy: {
      minimumSeverity: 0.05,
      topN: 10,
      failureType: null,
      familyId: null,
      familyCaseCap: 200,
      maxDuplicateRatio: 0.6,
      recurrenceWindow: 5,
      recurrenceThreshold: 2,
      strategy: "exact_suggested_family_then_health_guards",
    },
    signal: {
      verdict: "regression",
      reason: null,
      regressionScore: 0.27,
      improvementScore: 0,
      netScore: 0.27,
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
    matchedFamily: {
      familyId: "regression-reasoning-failures-v1-hallucination",
      matchKind: "existing_family",
      exists: true,
      versionCount: 2,
      latestDatasetId: "regression-reasoning-failures-v1-hallucination-v2",
      currentCaseCount: 12,
      proposedAdditionCount: 2,
      duplicateCaseCount: 0,
      duplicateRatio: 0,
      projectedCaseCount: 14,
      familyCaseCap: 200,
      capReached: false,
      duplicateRatioExceeded: false,
    },
    selectedCaseCount: 2,
    evidenceCaseIds: ["case-regression"],
    previewCases: [],
    historyContext: null,
    clusterContext: [],
    escalation: {
      status: "critical",
      score: 0.41,
      severityBand: "high",
      reason: "severity=0.270, recent_regressions=2, recurring_clusters=1",
      recentRegressionCount: 2,
      recurringClusterCount: 1,
      familyHealthLabel: "degrading",
    },
    lifecycleRecommendation: {
      familyId: "regression-reasoning-failures-v1-hallucination",
      action: "prune",
      healthCondition: "overgrown",
      rationale: "Projected family growth crosses the deterministic overgrowth threshold.",
      targetFamilyId: null,
      relatedFamilyIds: [],
      sourceDatasetId: "reasoning-failures-v1",
      primaryFailureType: "hallucination",
      latestDatasetId: "regression-reasoning-failures-v1-hallucination-v2",
      versionCount: 2,
      evaluationRunCount: 3,
      recentFailRate: 0.25,
      projectedCaseCount: 14,
    },
    ...overrides,
  };
}

function buildInventoryPortfolioItem(
  overrides: Partial<ArtifactDatasetPortfolioItem> = {},
): ArtifactDatasetPortfolioItem {
  return {
    familyId: "regression-reasoning-failures-v1-hallucination",
    priorityRank: 1,
    priorityBand: "urgent",
    priorityScore: 91.25,
    actionability: "actionable_now",
    rationale: "Critical escalation with recurring regressions keeps this family at the top.",
    lifecycleAction: "prune",
    healthCondition: "overgrown",
    healthLabel: "degrading",
    trendLabel: "degrading",
    versionCount: 2,
    latestDatasetId: "regression-reasoning-failures-v1-hallucination-v2",
    latestVersionTag: "v2",
    latestComparisonId: "compare_alpha_to_beta",
    sourceDatasetId: "reasoning-failures-v1",
    primaryFailureType: "hallucination",
    recentFailRate: 0.25,
    projectedCaseCount: 14,
    escalationStatus: "critical",
    escalationScore: 0.41,
    recentRegressionCount: 2,
    recurringClusterCount: 1,
    targetFamilyId: null,
    relatedFamilyIds: [],
    comparisonRefs: [],
    clusterIds: [],
    datasets: ["reasoning-failures-v1"],
    models: ["demo"],
    activeLifecycleActionId: "life-001",
    activeLifecycleAction: "prune",
    activeLifecycleCondition: "overgrown",
    activeLifecycleAppliedAt: "2026-03-30T12:45:00Z",
    outcomeFeedback: null,
    ...overrides,
  };
}

function buildComparisonDetail(reportId: string): ComparisonDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    comparison: {
      reportId,
      createdAt: "2026-03-30T12:00:00Z",
      status: "improved",
      baselineRunId: "run_alpha",
      candidateRunId: "run_beta",
      dataset: "reasoning-failures-v1",
      baselineDataset: null,
      candidateDataset: null,
      compatible: true,
      reason: null,
      comparisonMode: "baseline_to_candidate",
      metricsComputedOn: "shared_cases_only",
    },
    signal: {
      verdict: "improvement",
      reason: null,
      regressionScore: 0.08,
      improvementScore: 0.22,
      netScore: -0.14,
      severity: 0.22,
      topDrivers: [
        {
          driverRank: 0,
          failureType: "hallucination",
          delta: -0.22,
          direction: "improvement",
          caseIds: ["case-002"],
        },
      ],
    },
    metrics: {
      baseline: {
        attemptedCaseCount: 8,
        classifiedCaseCount: 8,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 8,
        failureRate: 0.5,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      candidate: {
        attemptedCaseCount: 8,
        classifiedCaseCount: 8,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 8,
        failureRate: 0.25,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      delta: {
        failureRate: -0.25,
        classificationCoverage: 0,
        executionSuccessRate: 0,
      },
    },
    coverage: {
      sharedCaseCount: 8,
      baselineOnlyCaseCount: 1,
      candidateOnlyCaseCount: 0,
      sharedCaseIds: ["case-002", "case-003"],
      baselineOnlyCaseIds: ["case-001"],
      candidateOnlyCaseIds: [],
    },
    transitions: {
      counts: {
        improvements: 1,
        regressions: 0,
        failureTypeSwaps: 0,
        errorChanges: 0,
      },
      summary: [
        {
          transitionType: "failure_to_no_failure",
          label: "failure -> no_failure",
          count: 1,
          caseIds: ["case-002"],
        },
      ],
    },
    caseDeltas: [
      {
        caseId: "case-002",
        promptId: "case-002",
        prompt: "Answer using only the supplied source snippet.",
        tags: ["core", "factuality"],
        transitionType: "failure_to_no_failure",
        transitionLabel: "failure -> no_failure",
        baselineFailureType: "hallucination",
        candidateFailureType: "no_failure",
        baselineExpectationVerdict: "unexpected_failure",
        candidateExpectationVerdict: "no_failure_as_expected",
        baselineErrorStage: null,
        candidateErrorStage: null,
        baselineExplanation: "Unsupported factual framing detected.",
        candidateExplanation: "No heuristic failure signal detected.",
      },
    ],
    insightReport: null,
    governanceRecommendation: null,
  };
}

function serializeComparisonDetail(detail: ComparisonDetail): Record<string, unknown> {
  return {
    ...detail,
    signal: {
      verdict: detail.signal.verdict,
      reason: detail.signal.reason,
      regression_score: detail.signal.regressionScore,
      improvement_score: detail.signal.improvementScore,
      net_score: detail.signal.netScore,
      severity: detail.signal.severity,
      top_drivers: detail.signal.topDrivers.map((driver) => ({
        driver_rank: driver.driverRank,
        failure_type: driver.failureType,
        delta: driver.delta,
        direction: driver.direction,
        case_ids: driver.caseIds,
      })),
    },
  };
}

function mockComparisonDetail(detail: ComparisonDetail) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes(`/__failure_lab__/artifacts/comparison-detail.json?reportId=${detail.comparison.reportId}`)) {
        return {
          ok: true,
          status: 200,
          json: async () => serializeComparisonDetail(detail),
        } as Response;
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({ message: `Unexpected request: ${url}` }),
      } as Response;
    }),
  );
}

function buildLinkedRunDetail(runId: string, dataset: string): RunDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    run: {
      runId,
      dataset,
      model: "demo",
      createdAt: "2026-03-30T12:10:00Z",
      status: "completed",
      reportId: `${runId}_report`,
      adapterId: "demo",
      classifierId: "heuristic_v1",
      runSeed: 17,
    },
    metrics: {
      attemptedCaseCount: 4,
      classifiedCaseCount: 4,
      executionErrorCount: 0,
      unclassifiedCount: 0,
      successfulModelInvocationCount: 4,
      failureCaseCount: 1,
      failureRate: 0.25,
      classificationCoverage: 1,
      executionSuccessRate: 1,
    },
    summary: {
      failureTypes: [
        { label: "hallucination", count: 1, share: 0.25, caseIds: ["case-002"] },
      ],
      expectationVerdicts: [
        { label: "unexpected_failure", count: 1, share: 0.25, caseIds: ["case-002"] },
      ],
      tagSlices: [
        {
          tag: "core",
          attemptedCaseCount: 4,
          classifiedCaseCount: 4,
          failureCaseCount: 1,
          failureRate: 0.25,
          expectationVerdictCounts: { unexpected_failure: 1 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: ["case-002"],
      notableCaseIds: ["case-002"],
      allCaseIds: ["case-001", "case-002"],
      errorCaseIds: [],
    },
    cases: [
      {
        caseId: "case-002",
        promptId: "case-002",
        prompt: "Answer using only the supplied source snippet.",
        tags: ["core", "factuality"],
        outputText: "Invented unsupported detail.",
        expectation: {
          expectedFailure: { failureType: "no_failure", failureSubtype: null },
          observedFailure: { failureType: "hallucination", failureSubtype: null },
          verdict: "unexpected_failure",
        },
        classification: {
          failure: { failureType: "hallucination", failureSubtype: null },
          confidence: 0.91,
          explanation: "Unsupported factual framing detected.",
        },
        error: null,
      },
    ],
  };
}

function mockComparisonAndRunDetails(detail: ComparisonDetail) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (
        url.includes(
          `/__failure_lab__/artifacts/comparison-detail.json?reportId=${detail.comparison.reportId}`,
        )
      ) {
        return {
          ok: true,
          status: 200,
          json: async () => serializeComparisonDetail(detail),
        } as Response;
      }

      if (
        url.includes(
          `/__failure_lab__/artifacts/run-detail.json?runId=${detail.comparison.baselineRunId}`,
        )
      ) {
        return {
          ok: true,
          status: 200,
          json: async () =>
            buildLinkedRunDetail(detail.comparison.baselineRunId, "reasoning-failures-v1"),
        } as Response;
      }

      if (
        url.includes(
          `/__failure_lab__/artifacts/run-detail.json?runId=${detail.comparison.candidateRunId}`,
        )
      ) {
        return {
          ok: true,
          status: 200,
          json: async () =>
            buildLinkedRunDetail(detail.comparison.candidateRunId, "reasoning-failures-v1"),
        } as Response;
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({ message: `Unexpected request: ${url}` }),
      } as Response;
    }),
  );
}

describe("comparisons route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders a dense newest-first comparison inventory from the active source", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialArtifactState={buildReadyState([
          "compare_alpha_to_beta",
          "compare_beta_to_gamma",
        ])}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([
          {
            reportId: "compare_alpha_to_beta",
            baselineRunId: "run_alpha",
            candidateRunId: "run_beta",
            dataset: "reasoning-failures-v1",
            createdAt: "2026-03-30T12:00:00Z",
            status: "improved",
            compatible: true,
            ...buildSignalInventoryFields("improvement", 0.22, {
              failureType: "hallucination",
              delta: -0.22,
              caseIds: ["case-002"],
            }),
          },
          {
            reportId: "compare_beta_to_gamma",
            baselineRunId: "run_beta",
            candidateRunId: "run_gamma",
            dataset: null,
            createdAt: "2026-03-30T12:30:00Z",
            status: "incompatible_dataset",
            compatible: false,
            ...buildSignalInventoryFields("incompatible", 0.05),
          },
        ])}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Saved comparisons inventory." }),
    ).toBeInTheDocument();
    expect(screen.getByText("compare_beta_to_gamma")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Comparisons inventory" })).toBeInTheDocument();
    const rows = screen.getAllByRole("link", { name: /Open comparison /i });
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveAttribute("aria-label", "Open comparison compare_alpha_to_beta");
    expect(rows[1]).toHaveAttribute("aria-label", "Open comparison compare_beta_to_gamma");
    expect(screen.getByText("Multiple datasets")).toBeInTheDocument();
    expect(screen.getByText("22.0% severity")).toBeInTheDocument();
    expect(screen.getByText("Driver: hallucination -22.0%")).toBeInTheDocument();
  });

  it("supports operator-first triage lenses and priority surfacing from the inventory", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons?triage=critical&order=priority"]}
        initialArtifactState={buildReadyState([
          "compare_alpha_to_beta",
          "compare_beta_to_gamma",
          "compare_gamma_to_delta",
        ])}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([
          {
            reportId: "compare_alpha_to_beta",
            baselineRunId: "run_alpha",
            candidateRunId: "run_beta",
            dataset: "reasoning-failures-v1",
            createdAt: "2026-03-30T12:00:00Z",
            status: "regressed",
            compatible: true,
            ...buildSignalInventoryFields("regression", 0.27, {
              failureType: "hallucination",
              delta: 0.18,
              caseIds: ["case-regression"],
            }),
            governanceRecommendation: buildInventoryGovernanceRecommendation(),
            portfolioItem: buildInventoryPortfolioItem(),
          },
          {
            reportId: "compare_beta_to_gamma",
            baselineRunId: "run_beta",
            candidateRunId: "run_gamma",
            dataset: "reasoning-failures-v1",
            createdAt: "2026-03-30T12:30:00Z",
            status: "regressed",
            compatible: true,
            ...buildSignalInventoryFields("regression", 0.14, {
              failureType: "reasoning",
              delta: 0.12,
              caseIds: ["case-008"],
            }),
            governanceRecommendation: buildInventoryGovernanceRecommendation({
              action: "ignore",
              escalation: {
                status: "watch",
                score: 0.12,
                severityBand: "medium",
                reason: "severity=0.140",
                recentRegressionCount: 1,
                recurringClusterCount: 0,
                familyHealthLabel: null,
              },
              lifecycleRecommendation: {
                familyId: "regression-reasoning-failures-v1-reasoning",
                action: "keep",
                healthCondition: "stable",
                rationale: "No lifecycle follow-up is required.",
                targetFamilyId: null,
                relatedFamilyIds: [],
                sourceDatasetId: "reasoning-failures-v1",
                primaryFailureType: "reasoning",
                latestDatasetId: "regression-reasoning-failures-v1-reasoning-v1",
                versionCount: 1,
                evaluationRunCount: 2,
                recentFailRate: 0.1,
                projectedCaseCount: 8,
              },
            }),
            portfolioItem: buildInventoryPortfolioItem({
              familyId: "regression-reasoning-failures-v1-reasoning",
              priorityRank: 4,
              priorityBand: "medium",
              priorityScore: 40.5,
              actionability: "monitor",
              lifecycleAction: "keep",
              healthCondition: "stable",
              escalationStatus: "watch",
              escalationScore: 0.12,
            }),
          },
          {
            reportId: "compare_gamma_to_delta",
            baselineRunId: "run_gamma",
            candidateRunId: "run_delta",
            dataset: "hallucination-failures-v1",
            createdAt: "2026-03-30T13:00:00Z",
            status: "improved",
            compatible: true,
            ...buildSignalInventoryFields("improvement", 0.18, {
              failureType: "hallucination",
              delta: -0.18,
              caseIds: ["case-013"],
            }),
          },
        ])}
      />,
    );

    expect(screen.getByText("1 visible")).toBeInTheDocument();
    expect(screen.getByText("1 critical")).toBeInTheDocument();
    expect(screen.getByText("1 lifecycle follow-up")).toBeInTheDocument();
    expect(screen.getByText("Rank 1 Urgent")).toBeInTheDocument();
    expect(screen.getAllByText("Critical").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Prune").length).toBeGreaterThan(0);
    expect(
      screen.getByText("Family: regression-reasoning-failures-v1-hallucination · Actionable Now"),
    ).toBeInTheDocument();
    expect(screen.queryByText("compare_beta_to_gamma")).not.toBeInTheDocument();
    expect(screen.queryByText("compare_gamma_to_delta")).not.toBeInTheDocument();
  });

  it("shows a route-level empty state when no comparison reports exist yet", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialArtifactState={buildReadyState([])}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([])}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "No comparison reports are available yet." }),
    ).toBeInTheDocument();
    expect(screen.getByText(/generate a comparison with `failure-lab compare`/i)).toBeInTheDocument();
  });

  it("opens the dedicated comparison route from row activation", async () => {
    const user = userEvent.setup();
    mockComparisonDetail(buildComparisonDetail("compare_alpha_to_beta"));

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons?sort=timestamp_desc"]}
        initialArtifactState={buildReadyState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([
          {
            reportId: "compare_alpha_to_beta",
            baselineRunId: "run_alpha",
            candidateRunId: "run_beta",
            dataset: "reasoning-failures-v1",
            createdAt: "2026-03-30T12:00:00Z",
            status: "improved",
            compatible: true,
            ...buildSignalInventoryFields("improvement", 0.22, {
              failureType: "hallucination",
              delta: -0.22,
              caseIds: ["case-002"],
            }),
          },
        ])}
      />,
    );

    await user.click(screen.getByRole("link", { name: "Open comparison compare_alpha_to_beta" }));

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("compare_alpha_to_beta").length).toBeGreaterThan(0);
    const breadcrumb = screen.getByRole("navigation", { name: "Comparison breadcrumb" });
    expect(breadcrumb).toBeInTheDocument();
    expect(within(breadcrumb).getByRole("link", { name: "Comparisons" })).toHaveAttribute(
      "href",
      "/comparisons?sort=timestamp_desc",
    );
    expect(
      screen.getByRole("heading", { name: "Directional change at a glance" }),
    ).toBeInTheDocument();
  });

  it("proves the comparison-led investigation story from inventory into run evidence artifact context", async () => {
    const user = userEvent.setup();
    const detail = buildComparisonDetail("compare_alpha_to_beta");
    mockComparisonAndRunDetails(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialArtifactState={buildReadyState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([
          {
            reportId: "compare_alpha_to_beta",
            baselineRunId: "run_alpha",
            candidateRunId: "run_beta",
            dataset: "reasoning-failures-v1",
            createdAt: "2026-03-30T12:00:00Z",
            status: "improved",
            compatible: true,
            ...buildSignalInventoryFields("improvement", 0.22, {
              failureType: "hallucination",
              delta: -0.22,
              caseIds: ["case-002"],
            }),
          },
        ])}
      />,
    );

    await user.click(screen.getByRole("link", { name: "Open comparison compare_alpha_to_beta" }));

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Inspect transition case case-002" }),
    ).toHaveAttribute("data-active-case", "true");

    await user.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Selected case evidence" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Inspect case case-002" }),
    ).toHaveAttribute("data-active-case", "true");
    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(within(artifactContext).getByText("run_alpha_report")).toBeInTheDocument();
    expect(within(artifactContext).getByText("/tmp/model-failure-lab")).toBeInTheDocument();
  });
});
