import { render, screen } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
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
        { label: "hallucination", count: 3, share: 0.3, caseIds: ["case-002", "case-004", "case-006"] },
        { label: "reasoning", count: 1, share: 0.1, caseIds: ["case-003"] },
      ],
      expectationVerdicts: [
        { label: "unexpected_failure", count: 2, share: 0.2, caseIds: ["case-002", "case-004"] },
        { label: "missed_expected", count: 1, share: 0.1, caseIds: ["case-005"] },
      ],
      tagSlices: [
        {
          tag: "core",
          attemptedCaseCount: 6,
          classifiedCaseCount: 6,
          failureCaseCount: 3,
          failureRate: 0.5,
          expectationVerdictCounts: {
            unexpected_failure: 1,
            matched_expected: 2,
          },
        },
        {
          tag: "factuality",
          attemptedCaseCount: 4,
          classifiedCaseCount: 3,
          failureCaseCount: 2,
          failureRate: 2 / 3,
          expectationVerdictCounts: {
            unexpected_failure: 2,
          },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: ["case-002", "case-004", "case-005"],
      notableCaseIds: ["case-002", "case-004"],
      allCaseIds: ["case-001", "case-002", "case-003", "case-004", "case-005"],
      errorCaseIds: ["case-006"],
    },
    cases: [
      {
        caseId: "case-001",
        promptId: "case-001",
        prompt: "Give a grounded summary.",
        tags: ["core", "control"],
        outputText: "Grounded summary.",
        expectation: {
          expectedFailure: { failureType: "no_failure", failureSubtype: null },
          observedFailure: { failureType: "no_failure", failureSubtype: null },
          verdict: "no_failure_as_expected",
        },
        classification: {
          failure: { failureType: "no_failure", failureSubtype: null },
          confidence: 0.2,
          explanation: "No heuristic failure signal detected.",
        },
        error: null,
      },
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
        caseId: "case-004",
        promptId: "case-004",
        prompt: "Use only the provided evidence bullets.",
        tags: ["factuality"],
        outputText: "Used an unsupported source claim.",
        expectation: {
          expectedFailure: { failureType: "no_failure", failureSubtype: null },
          observedFailure: { failureType: "hallucination", failureSubtype: null },
          verdict: "unexpected_failure",
        },
        classification: {
          failure: { failureType: "hallucination", failureSubtype: null },
          confidence: 0.88,
          explanation: "Answer went beyond supplied context.",
        },
        error: null,
      },
      {
        caseId: "case-005",
        promptId: "case-005",
        prompt: "Follow the reference reasoning chain exactly.",
        tags: ["core"],
        outputText: "Skipped a required inference step.",
        expectation: {
          expectedFailure: { failureType: "reasoning", failureSubtype: null },
          observedFailure: { failureType: "no_failure", failureSubtype: null },
          verdict: "missed_expected",
        },
        classification: {
          failure: { failureType: "no_failure", failureSubtype: null },
          confidence: 0.3,
          explanation: "No heuristic failure signal detected.",
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

function mockRunDetail(detail: RunDetail) {
  const fetchMock = vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    if (url.includes(`/__failure_lab__/artifacts/run-detail.json?runId=${detail.run.runId}`)) {
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
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const SAMPLE_RUN: RunInventoryItem = {
  runId: "run_gamma",
  dataset: "hallucination-failures-v1",
  model: "gpt-4.1-mini",
  createdAt: "2026-03-30T12:15:00Z",
  status: "completed_with_errors",
};

describe("run detail route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders the summary-first run detail hierarchy from saved artifact payloads", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    const fetchMock = mockRunDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
      />,
    );

    expect(await screen.findByRole("heading", { name: "run_gamma" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("heading", { name: "Failure types, verdicts, and tag slices" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Notable cases" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Case inspection" })).toBeInTheDocument();
    expect(screen.getAllByText("Unexpected Failure").length).toBeGreaterThan(0);
    expect(screen.getByText("Answer using only the supplied source snippet.")).toBeInTheDocument();
    expect(screen.getByText("Attempted")).toBeInTheDocument();
    expect(screen.getByText("Failure rate")).toBeInTheDocument();
  });

  it("shows an explicit incompatible-detail state when the saved run payload cannot be read", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 500,
        json: async () => ({ message: "Saved report detail is missing report_details.json" }),
      })),
    );

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
      />,
    );

    expect(
      await screen.findByRole("heading", {
        name: "The saved run detail could not be loaded.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Saved report detail is missing report_details.json")).toBeInTheDocument();
  });
});
