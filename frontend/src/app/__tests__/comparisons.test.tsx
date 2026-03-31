import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  ComparisonDetail,
  ComparisonInventoryItem,
  ComparisonInventoryState,
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
          json: async () => detail,
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
          },
          {
            reportId: "compare_beta_to_gamma",
            baselineRunId: "run_beta",
            candidateRunId: "run_gamma",
            dataset: null,
            createdAt: "2026-03-30T12:30:00Z",
            status: "incompatible_dataset",
            compatible: false,
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
    expect(rows[0]).toHaveAttribute("aria-label", "Open comparison compare_beta_to_gamma");
    expect(rows[1]).toHaveAttribute("aria-label", "Open comparison compare_alpha_to_beta");
    expect(screen.getByText("Multiple datasets")).toBeInTheDocument();
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
          },
        ])}
      />,
    );

    await user.click(screen.getByRole("link", { name: "Open comparison compare_alpha_to_beta" }));

    expect(
      await screen.findByRole("heading", { name: "compare_alpha_to_beta" }),
    ).toBeInTheDocument();
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
});
