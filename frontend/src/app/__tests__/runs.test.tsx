import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  ComparisonDetail,
  ComparisonInventoryState,
  RunDetail,
  RunInventoryItem,
  RunInventoryState,
} from "@/lib/artifacts/types";

function buildReadyArtifactState(runIds: string[]): ArtifactShellState {
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
        count: runIds.length,
        ids: runIds,
      },
      comparisons: {
        count: 0,
        ids: [],
      },
      issues: [],
      message: null,
    },
  };
}

function buildReadyInventoryState(runs: RunInventoryItem[]): RunInventoryState {
  return {
    status: "ready",
    inventory: {
      source: {
        label: "Repo root artifact store",
        path: "/tmp/model-failure-lab",
        runsPath: "/tmp/model-failure-lab/runs",
        reportsPath: "/tmp/model-failure-lab/reports",
      },
      runs,
    },
    message: null,
  };
}

function buildReadyComparisonInventoryState(
  comparisons: NonNullable<ComparisonInventoryState["inventory"]>["comparisons"] = [],
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

const SAMPLE_RUNS: RunInventoryItem[] = [
  {
    runId: "run_alpha",
    dataset: "reasoning-failures-v1",
    model: "demo",
    createdAt: "2026-03-28T09:30:00Z",
    status: "completed",
  },
  {
    runId: "run_gamma",
    dataset: "hallucination-failures-v1",
    model: "gpt-4.1-mini",
    createdAt: "2026-03-30T12:15:00Z",
    status: "completed_with_errors",
  },
  {
    runId: "run_beta",
    dataset: "reasoning-failures-v1",
    model: "gpt-4.1-mini",
    createdAt: "2026-03-29T10:45:00Z",
    status: "completed",
  },
];

function buildRunDetail(run: RunInventoryItem): RunDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    run: {
      runId: run.runId,
      dataset: run.dataset,
      model: run.model,
      createdAt: run.createdAt,
      status: run.status,
      reportId: `${run.runId}_report`,
      adapterId: "demo",
      classifierId: "heuristic_v1",
      runSeed: 17,
    },
    metrics: {
      attemptedCaseCount: 12,
      classifiedCaseCount: 10,
      executionErrorCount: 1,
      unclassifiedCount: 1,
      successfulModelInvocationCount: 11,
      failureCaseCount: 4,
      failureRate: 0.4,
      classificationCoverage: 10 / 12,
      executionSuccessRate: 11 / 12,
    },
    summary: {
      failureTypes: [
        { label: "hallucination", count: 3, share: 0.3, caseIds: ["case-002"] },
      ],
      expectationVerdicts: [
        { label: "unexpected_failure", count: 2, share: 0.2, caseIds: ["case-002"] },
      ],
      tagSlices: [
        {
          tag: "factuality",
          attemptedCaseCount: 4,
          classifiedCaseCount: 3,
          failureCaseCount: 2,
          failureRate: 2 / 3,
          expectationVerdictCounts: { unexpected_failure: 2 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: ["case-002"],
      notableCaseIds: ["case-002"],
      allCaseIds: ["case-001", "case-002"],
      errorCaseIds: ["case-006"],
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
      {
        caseId: "case-006",
        promptId: "case-006",
        prompt: "Emit a structured answer.",
        tags: ["extended"],
        outputText: null,
        expectation: {
          expectedFailure: null,
          observedFailure: null,
          verdict: null,
        },
        classification: null,
        error: {
          stage: "model_invoke",
          type: "TimeoutError",
          message: "Request timed out",
        },
      },
    ],
  };
}

function buildComparisonDetail(
  reportId: string,
  baselineRunId: string,
  candidateRunId: string,
  dataset: string,
): ComparisonDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    comparison: {
      reportId,
      createdAt: "2026-03-30T12:30:00Z",
      status: "improved",
      baselineRunId,
      candidateRunId,
      dataset,
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
      regressionScore: 0.05,
      improvementScore: 0.25,
      netScore: -0.2,
      severity: 0.25,
      topDrivers: [
        {
          driverRank: 0,
          failureType: "hallucination",
          delta: -0.25,
          direction: "improvement",
          caseIds: ["case-002"],
        },
      ],
    },
    metrics: {
      baseline: {
        attemptedCaseCount: 4,
        classifiedCaseCount: 4,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 4,
        failureRate: 0.5,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      candidate: {
        attemptedCaseCount: 4,
        classifiedCaseCount: 4,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 4,
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
      sharedCaseCount: 4,
      baselineOnlyCaseCount: 0,
      candidateOnlyCaseCount: 0,
      sharedCaseIds: ["case-002"],
      baselineOnlyCaseIds: [],
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

function mockRunDetail(runs: RunInventoryItem[]) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      const matchedRun = runs.find((run) =>
        url.includes(`/__failure_lab__/artifacts/run-detail.json?runId=${run.runId}`),
      );
      if (matchedRun) {
        return {
          ok: true,
          status: 200,
          json: async () => buildRunDetail(matchedRun),
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

function mockRunAndComparisonDetails(
  runs: RunInventoryItem[],
  comparisons: ComparisonDetail[],
) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      const matchedRun = runs.find((run) =>
        url.includes(`/__failure_lab__/artifacts/run-detail.json?runId=${run.runId}`),
      );
      if (matchedRun) {
        return {
          ok: true,
          status: 200,
          json: async () => buildRunDetail(matchedRun),
        } as Response;
      }

      const matchedComparison = comparisons.find((comparison) =>
        url.includes(
          `/__failure_lab__/artifacts/comparison-detail.json?reportId=${comparison.comparison.reportId}`,
        ),
      );
      if (matchedComparison) {
        return {
          ok: true,
          status: 200,
          json: async () => serializeComparisonDetail(matchedComparison),
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

describe("runs route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders a dense newest-first inventory table from the active source", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState(SAMPLE_RUNS.map((run) => run.runId))}
        initialRunInventoryState={buildReadyInventoryState(SAMPLE_RUNS)}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Saved runs inventory." }),
    ).toBeInTheDocument();
    expect(screen.getByText("3 detected")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Runs inventory" })).toBeInTheDocument();

    const rows = screen.getAllByRole("link", { name: /Open run /i });
    expect(rows).toHaveLength(3);
    expect(rows[0]).toHaveAttribute("aria-label", "Open run run_gamma");
    expect(rows[1]).toHaveAttribute("aria-label", "Open run run_beta");
    expect(rows[2]).toHaveAttribute("aria-label", "Open run run_alpha");
  });

  it("filters runs by query, dataset, model, and status with a reset action", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState(SAMPLE_RUNS.map((run) => run.runId))}
        initialRunInventoryState={buildReadyInventoryState(SAMPLE_RUNS)}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    await user.type(screen.getByRole("searchbox", { name: "Run id search" }), "beta");
    expect(screen.getAllByRole("link", { name: /Open run /i })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Open run run_beta" })).toBeInTheDocument();

    await user.clear(screen.getByRole("searchbox", { name: "Run id search" }));
    await user.selectOptions(screen.getByRole("combobox", { name: "Dataset" }), [
      "hallucination-failures-v1",
    ]);
    expect(screen.getAllByRole("link", { name: /Open run /i })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Open run run_gamma" })).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Model" }), ["gpt-4.1-mini"]);
    await user.selectOptions(screen.getByRole("combobox", { name: "Status" }), [
      "completed_with_errors",
    ]);
    expect(screen.getAllByRole("link", { name: /Open run /i })).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getAllByRole("link", { name: /Open run /i })).toHaveLength(3);
  });

  it("restores the runs inventory state from URL query params on first render", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={[
          "/?q=gamma&dataset=hallucination-failures-v1&model=gpt-4.1-mini&status=completed_with_errors&sort=timestamp_desc",
        ]}
        initialArtifactState={buildReadyArtifactState(SAMPLE_RUNS.map((run) => run.runId))}
        initialRunInventoryState={buildReadyInventoryState(SAMPLE_RUNS)}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(screen.getByRole("searchbox", { name: "Run id search" })).toHaveValue("gamma");
    expect(screen.getByRole("combobox", { name: "Dataset" })).toHaveValue(
      "hallucination-failures-v1",
    );
    expect(screen.getByRole("combobox", { name: "Model" })).toHaveValue("gpt-4.1-mini");
    expect(screen.getByRole("combobox", { name: "Status" })).toHaveValue(
      "completed_with_errors",
    );
    expect(screen.getAllByRole("link", { name: /Open run /i })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Open run run_gamma" })).toBeInTheDocument();
  });

  it("opens the dedicated run route from both row activation and the explicit affordance", async () => {
    const user = userEvent.setup();
    mockRunDetail([SAMPLE_RUNS[1], SAMPLE_RUNS[2]]);

    render(
      <App
        useMemoryRouter
        initialEntries={[
          "/?q=gamma&dataset=hallucination-failures-v1&model=gpt-4.1-mini&status=completed_with_errors&sort=timestamp_desc",
        ]}
        initialArtifactState={buildReadyArtifactState(SAMPLE_RUNS.map((run) => run.runId))}
        initialRunInventoryState={buildReadyInventoryState(SAMPLE_RUNS)}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    await user.click(screen.getByRole("link", { name: "Open run run_gamma" }));
    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Run breadcrumb" })).toBeInTheDocument();
    expect(screen.getAllByText("run_gamma").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Why it failed" })).toBeInTheDocument();

    const backToRuns = screen.getAllByRole("link", { name: "Back to runs" })[0];
    await user.click(backToRuns);

    expect(screen.getByRole("searchbox", { name: "Run id search" })).toHaveValue("gamma");
    expect(screen.getAllByRole("link", { name: /Open run /i })).toHaveLength(1);

    const row = screen.getByRole("link", { name: "Open run run_gamma" });
    await user.click(within(row).getByRole("button", { name: "Open run_gamma" }));
    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();
  });

  it("proves the run-led investigation story from inventory into related comparison artifact context", async () => {
    const user = userEvent.setup();
    const comparisons = [
      buildComparisonDetail(
        "compare_alpha_to_gamma",
        "run_alpha",
        "run_gamma",
        "hallucination-failures-v1",
      ),
    ];
    mockRunAndComparisonDetails([SAMPLE_RUNS[0], SAMPLE_RUNS[1]], comparisons);

    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState(["run_alpha", "run_gamma"])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUNS[0], SAMPLE_RUNS[1]])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([
          {
            reportId: "compare_alpha_to_gamma",
            baselineRunId: "run_alpha",
            candidateRunId: "run_gamma",
            dataset: "hallucination-failures-v1",
            createdAt: "2026-03-30T12:30:00Z",
            status: "improved",
            compatible: true,
            ...buildSignalInventoryFields("improvement", 0.25, {
              failureType: "hallucination",
              delta: -0.25,
              caseIds: ["case-002"],
            }),
          },
        ])}
      />,
    );

    await user.click(screen.getByRole("link", { name: "Open run run_gamma" }));

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Inspect case case-002" }),
    ).toHaveAttribute("data-active-case", "true");

    await user.click(screen.getByRole("link", { name: "compare_alpha_to_gamma" }));

    expect(
      await screen.findByRole("heading", { name: "Grouped case transitions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Inspect transition case case-002" }),
    ).toHaveAttribute("data-active-case", "true");

    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getByText("compare_alpha_to_gamma")).toBeInTheDocument();
    expect(within(artifactContext).getAllByText("case-002").length).toBeGreaterThan(0);
    expect(within(artifactContext).getByText("run_alpha / run_gamma")).toBeInTheDocument();
  });

  it("shows a route-level empty state when the shell is ready but no runs exist", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState([])}
        initialRunInventoryState={buildReadyInventoryState([])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "No saved runs are available yet." }),
    ).toBeInTheDocument();
    expect(screen.getByText(/there are no `runs\/<run_id>` directories/i)).toBeInTheDocument();
  });
});
