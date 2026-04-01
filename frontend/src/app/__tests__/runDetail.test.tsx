import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  ComparisonInventoryState,
  RunDetail,
  RunInventoryItem,
  RunInventoryState,
} from "@/lib/artifacts/types";

const nativeScrollIntoView = HTMLElement.prototype.scrollIntoView;

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
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: nativeScrollIntoView,
    });
    window.history.replaceState({}, "", "/");
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
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    const runHeading = await screen.findByRole("heading", {
      name: "Hallucination Failures V1",
    });
    expect(runHeading).toBeInTheDocument();
    expect(screen.getAllByText("run_gamma").length).toBeGreaterThan(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("navigation", { name: "Detail section jumps" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Stay inside the run flow" })).toBeInTheDocument();
    expect(screen.getByText("Stage 1 · Run identity")).toBeInTheDocument();
    expect(screen.queryByText("Pathway checkpoints")).not.toBeInTheDocument();
    expect(screen.queryByText("Follow the run from identity to evidence.")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overall failure shape" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Why it failed" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Notable cases worth opening first" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Selected case evidence" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Mismatches (3)" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getAllByText("Unexpected Failure").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Answer using only the supplied source snippet.").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Attempted")).toBeInTheDocument();
    expect(screen.getByText("Failure rate")).toBeInTheDocument();
    expect(screen.getAllByText("Unsupported factual framing detected.").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Persistent run provenance" })).toBeInTheDocument();
  });

  it("falls back to the first non-empty evidence lens when mismatches are absent", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    detail.lenses.mismatchCaseIds = [];
    mockRunDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Notable (2)" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.queryByText("No cases match this lens.")).not.toBeInTheDocument();
  });

  it("switches case lenses and keeps inspection inside the run route", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    mockRunDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "All (5)" }));
    fireEvent.click(screen.getByRole("button", { name: "Inspect case case-001" }));

    expect(screen.getByRole("tab", { name: "All (5)" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("Grounded summary.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Errors (1)" }));

    expect(screen.getByRole("tab", { name: "Errors (1)" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("Request timed out")).toBeInTheDocument();
    expect(screen.getAllByText("Emit a structured answer.").length).toBeGreaterThan(0);
  });

  it("opens a notable case directly into the selected evidence flow", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    mockRunDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Inspect notable case case-004" }));

    expect(screen.getByRole("tab", { name: "Notable (2)" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getAllByText("Answer went beyond supplied context.").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Use only the provided evidence bullets.").length,
    ).toBeGreaterThan(0);
  });

  it("shows focused artifact context on the selected run case surface", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    mockRunDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma?section=evidence&case=case-002"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();

    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getAllByText("run_gamma").length).toBeGreaterThan(0);
    expect(within(artifactContext).getByText("run_gamma_report")).toBeInTheDocument();
    expect(within(artifactContext).getByText("/tmp/model-failure-lab")).toBeInTheDocument();
  });

  it("surfaces lightweight related comparison links when saved reports reference the run", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    mockRunDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs/run_gamma"]}
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState([
          {
            reportId: "compare_alpha_to_gamma",
            baselineRunId: "run_alpha",
            candidateRunId: "run_gamma",
            dataset: "hallucination-failures-v1",
            createdAt: "2026-03-30T12:30:00Z",
            status: "improved",
            compatible: true,
          },
        ])}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Saved comparisons touching this run" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "compare_alpha_to_gamma" }),
    ).toHaveAttribute("href", "/comparisons/compare_alpha_to_gamma");
  });

  it("restores explicit run-detail URL state and canonicalizes invalid case selection", async () => {
    const detail = buildRunDetail(SAMPLE_RUN);
    mockRunDetail(detail);
    const scrolledIds: string[] = [];
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: function mockScrollIntoView() {
        scrolledIds.push((this as HTMLElement).id);
      },
    });
    window.history.replaceState({}, "", "/runs/run_gamma?lens=errors&case=case-002");

    render(
      <App
        initialArtifactState={buildReadyArtifactState([SAMPLE_RUN.runId])}
        initialRunInventoryState={buildReadyInventoryState([SAMPLE_RUN])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Hallucination Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Errors (1)" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("Request timed out")).toBeInTheDocument();
    expect(
      await screen.findByText(
        "Requested case case-002 is unavailable in this evidence state. Showing case-006 instead.",
      ),
    ).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("evidence");
      expect(params.get("lens")).toBe("errors");
      expect(params.get("case")).toBe("case-006");
      expect(scrolledIds).toContain("run-detail-evidence");
    });
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
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
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
