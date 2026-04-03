import { render, screen } from "@testing-library/react";
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
    expect(screen.getByText("Regression case")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/__failure_lab__/artifacts/query.json?mode=cases&failureType=hallucination&lastN=5",
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
});
