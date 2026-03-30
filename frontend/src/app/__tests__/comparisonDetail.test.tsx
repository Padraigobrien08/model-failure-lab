import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  ComparisonDetail,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";

function buildReadyArtifactState(comparisonIds: string[]): ArtifactShellState {
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

function buildReadyRunInventoryState(): RunInventoryState {
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
          dataset: "reasoning-failures-v1",
          model: "demo",
          createdAt: "2026-03-30T11:30:00Z",
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
      source: {
        label: "Repo root artifact store",
        path: "/tmp/model-failure-lab",
        runsPath: "/tmp/model-failure-lab/runs",
        reportsPath: "/tmp/model-failure-lab/reports",
      },
      comparisons: [
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
          reportId: "compare_dataset_mismatch",
          baselineRunId: "run_alpha",
          candidateRunId: "run_beta",
          dataset: null,
          createdAt: "2026-03-30T12:30:00Z",
          status: "incompatible_dataset",
          compatible: false,
        },
      ],
    },
    message: null,
  };
}

function buildCompatibleDetail(): ComparisonDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    comparison: {
      reportId: "compare_alpha_to_beta",
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
        regressions: 1,
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
        {
          transitionType: "no_failure_to_failure",
          label: "no_failure -> failure",
          count: 1,
          caseIds: ["case-004"],
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
      {
        caseId: "case-004",
        prompt: "Use only the provided evidence bullets.",
        tags: ["extended"],
        transitionType: "no_failure_to_failure",
        transitionLabel: "no_failure -> failure",
        baselineFailureType: "no_failure",
        candidateFailureType: "reasoning",
        baselineExpectationVerdict: "no_failure_as_expected",
        candidateExpectationVerdict: "unexpected_failure",
        baselineErrorStage: null,
        candidateErrorStage: null,
        baselineExplanation: "No heuristic failure signal detected.",
        candidateExplanation: "Reasoning chain diverged from the rubric.",
      },
    ],
  };
}

function buildIncompatibleDetail(): ComparisonDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    comparison: {
      reportId: "compare_dataset_mismatch",
      createdAt: "2026-03-30T12:30:00Z",
      status: "incompatible_dataset",
      baselineRunId: "run_alpha",
      candidateRunId: "run_beta",
      dataset: null,
      baselineDataset: "reasoning-failures-v1",
      candidateDataset: "hallucination-failures-v1",
      compatible: false,
      reason: "dataset_mismatch",
      comparisonMode: "baseline_to_candidate",
      metricsComputedOn: null,
    },
    metrics: {
      baseline: {
        attemptedCaseCount: 10,
        classifiedCaseCount: 10,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 10,
        failureRate: 0.4,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      candidate: {
        attemptedCaseCount: 10,
        classifiedCaseCount: 10,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 10,
        failureRate: 0.2,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      delta: {
        failureRate: null,
        classificationCoverage: null,
        executionSuccessRate: null,
      },
    },
    coverage: {
      sharedCaseCount: 0,
      baselineOnlyCaseCount: 1,
      candidateOnlyCaseCount: 1,
      sharedCaseIds: [],
      baselineOnlyCaseIds: ["case-001"],
      candidateOnlyCaseIds: ["case-101"],
    },
    transitions: {
      counts: {
        improvements: 0,
        regressions: 0,
        failureTypeSwaps: 0,
        errorChanges: 0,
      },
      summary: [],
    },
    caseDeltas: [],
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

describe("comparison detail route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders the summary-first comparison explorer and supports in-page case inspection", async () => {
    mockComparisonDetail(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "compare_alpha_to_beta" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Directional change at a glance" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Compatibility and shared-case scope" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shared-case analysis only")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Grouped case transitions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "failure -> no_failure" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Unsupported factual framing detected."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Inspect transition case case-004" }));

    expect(screen.getByText("Reasoning chain diverged from the rubric.")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Use only the provided evidence bullets." }),
    ).toBeInTheDocument();
  });

  it("keeps incompatible comparisons openable with explicit coverage semantics", async () => {
    mockComparisonDetail(buildIncompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_dataset_mismatch"]}
        initialArtifactState={buildReadyArtifactState(["compare_dataset_mismatch"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "compare_dataset_mismatch" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Incompatible comparison: Dataset Mismatch")).toBeInTheDocument();
    expect(screen.getByText("reasoning-failures-v1 vs hallucination-failures-v1")).toBeInTheDocument();
    expect(screen.getByText("The comparison is still readable even though the datasets do not align.")).toBeInTheDocument();
    expect(screen.getByText("case-001")).toBeInTheDocument();
    expect(screen.getByText("case-101")).toBeInTheDocument();
    expect(screen.getByText("No grouped transition changes are available.")).toBeInTheDocument();
  });
});
