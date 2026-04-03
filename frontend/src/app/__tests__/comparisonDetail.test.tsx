import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  RunDetail,
  ComparisonDetail,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";

const nativeScrollIntoView = HTMLElement.prototype.scrollIntoView;
const DEFAULT_SOURCE = {
  label: "Repo root artifact store",
  path: "/tmp/model-failure-lab",
  runsPath: "/tmp/model-failure-lab/runs",
  reportsPath: "/tmp/model-failure-lab/reports",
};
const CONFIGURED_SOURCE = {
  label: "Configured artifact store",
  path: "/tmp/external-artifacts",
  runsPath: "/tmp/external-artifacts/runs",
  reportsPath: "/tmp/external-artifacts/reports",
};

function buildReadyArtifactState(
  comparisonIds: string[],
  source = DEFAULT_SOURCE,
): ArtifactShellState {
  return {
    status: "ready",
    overview: {
      status: "ready",
      source,
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

function buildReadyRunInventoryState(
  runs: NonNullable<RunInventoryState["inventory"]>["runs"] = [
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
  source = DEFAULT_SOURCE,
): RunInventoryState {
  return {
    status: "ready",
    inventory: {
      source,
      runs,
    },
    message: null,
  };
}

function buildReadyComparisonInventoryState(
  source = DEFAULT_SOURCE,
): ComparisonInventoryState {
  return {
    status: "ready",
    inventory: {
      source,
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

function buildCompatibleDetail(source = DEFAULT_SOURCE): ComparisonDetail {
  return {
    source,
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
      {
        caseId: "case-004",
        promptId: "case-004",
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

function buildFallbackLinkedRunDetail(runId: string, dataset: string): RunDetail {
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
      attemptedCaseCount: 1,
      classifiedCaseCount: 1,
      executionErrorCount: 0,
      unclassifiedCount: 0,
      successfulModelInvocationCount: 1,
      failureCaseCount: 0,
      failureRate: 0,
      classificationCoverage: 1,
      executionSuccessRate: 1,
    },
    summary: {
      failureTypes: [],
      expectationVerdicts: [],
      tagSlices: [
        {
          tag: "core",
          attemptedCaseCount: 1,
          classifiedCaseCount: 1,
          failureCaseCount: 0,
          failureRate: 0,
          expectationVerdictCounts: { no_failure_as_expected: 1 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: [],
      notableCaseIds: ["case-001"],
      allCaseIds: ["case-001"],
      errorCaseIds: [],
    },
    cases: [
      {
        caseId: "case-001",
        promptId: "case-001",
        prompt: "Ground the answer in the supplied source.",
        tags: ["core"],
        outputText: "Grounded answer.",
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
    ],
  };
}

function mockComparisonAndRunDetails(
  detail: ComparisonDetail,
  linkedRuns: Map<string, RunDetail> = new Map([
    ["run_alpha", buildLinkedRunDetail("run_alpha", "reasoning-failures-v1")],
    ["run_beta", buildLinkedRunDetail("run_beta", "reasoning-failures-v1")],
  ]),
) {

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

      for (const [runId, runDetail] of linkedRuns) {
        if (url.includes(`/__failure_lab__/artifacts/run-detail.json?runId=${runId}`)) {
          return {
            ok: true,
            status: 200,
            json: async () => runDetail,
          } as Response;
        }
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
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: nativeScrollIntoView,
    });
    window.history.replaceState({}, "", "/");
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

    const comparisonHeading = await screen.findByRole("heading", {
      name: "Reasoning Failures V1",
    });
    expect(comparisonHeading).toBeInTheDocument();
    const comparisonHeader = comparisonHeading.closest("header");
    expect(comparisonHeader).not.toBeNull();
    expect(within(comparisonHeader as HTMLElement).queryByText("Baseline run")).not.toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).queryByText("Candidate run")).not.toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).queryByText("Report ID")).not.toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Baseline")).toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Candidate")).toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Status")).toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Saved at")).toBeInTheDocument();
    expect(screen.getAllByText("compare_alpha_to_beta").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("navigation", { name: "Detail section jumps" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Traverse comparison evidence" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Pathway checkpoints")).not.toBeInTheDocument();
    expect(screen.queryByText("Orient first, then compare hard.")).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Directional change at a glance" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Scope and compatibility" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shared-case analysis only")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Grouped case transitions" }),
    ).toBeInTheDocument();
    const routeProvenanceHeading = screen.getByRole("heading", {
      name: "Route provenance",
    });
    const comparisonRail = routeProvenanceHeading.closest("aside");
    expect(comparisonRail).not.toBeNull();
    expect(within(comparisonRail as HTMLElement).getByText("Report ID")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Baseline run")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Candidate run")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Compare mode")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Metrics scope")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).queryByText("Shared cases")).not.toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).queryByText("Baseline only")).not.toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).queryByText("Candidate only")).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "failure -> no_failure" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Active case").length).toBeGreaterThanOrEqual(2);
    expect(
      screen.getByRole("button", { name: "Inspect transition case case-002" }),
    ).toHaveAttribute("data-active-case", "true");
    expect(document.querySelectorAll('[data-active-case="true"]')).toHaveLength(2);
    expect(
      await screen.findByText("Unsupported factual framing detected."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Inspect transition case case-004" }));

    expect(
      screen.getByRole("button", { name: "Inspect transition case case-004" }),
    ).toHaveAttribute("data-active-case", "true");
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
      await screen.findByRole("heading", {
        name: "Reasoning Failures V1 Vs Hallucination Failures V1",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Incompatible comparison: Dataset Mismatch")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The comparison stays readable even though the saved runs do not align cleanly.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("case-001")).toBeInTheDocument();
    expect(screen.getByText("case-101")).toBeInTheDocument();
    expect(screen.getByText("No grouped transition changes are available.")).toBeInTheDocument();
  });

  it("links baseline and candidate identifiers directly into run detail routes", async () => {
    mockComparisonAndRunDetails(buildCompatibleDetail());

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
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Open baseline run_alpha" }));

    expect(await screen.findByRole("heading", { name: "Reasoning Failures V1" })).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Why it failed" })).toBeInTheDocument();
  });

  it("opens the selected comparison case directly into baseline and candidate run evidence", async () => {
    mockComparisonAndRunDetails(buildCompatibleDetail());
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    const firstRender = render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("transitions");
      expect(params.get("case")).toBe("case-002");
      expect(params.get("transition")).toBe("failure_to_no_failure");
    });

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Selected case evidence" })).toBeInTheDocument();
    expect(screen.getByText("Invented unsupported detail.")).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("evidence");
      expect(params.get("lens")).toBe("mismatches");
      expect(params.get("case")).toBe("case-002");
    });

    const baselineReturnLink = screen.getByRole("link", { name: "Back to runs" });
    const baselineReturnUrl = new URL(
      baselineReturnLink.getAttribute("href") ?? "",
      "https://example.test",
    );
    expect(baselineReturnUrl.pathname).toBe("/comparisons/compare_alpha_to_beta");
    expect(baselineReturnUrl.searchParams.get("section")).toBe("transitions");
    expect(baselineReturnUrl.searchParams.get("case")).toBe("case-002");
    expect(baselineReturnUrl.searchParams.get("transition")).toBe("failure_to_no_failure");

    firstRender.unmount();

    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in candidate run run_beta",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("run_beta").length).toBeGreaterThan(0);
    expect(screen.getByText("Invented unsupported detail.")).toBeInTheDocument();
  });

  it("disables selected-case drillthrough when the target run is already unavailable", async () => {
    mockComparisonDetail(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState([
          {
            runId: "run_beta",
            dataset: "reasoning-failures-v1",
            model: "demo",
            createdAt: "2026-03-30T11:30:00Z",
            status: "completed",
          },
        ])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Saved baseline run run_alpha is unavailable in the active run inventory.",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("link", {
        name: "Open case case-002 in candidate run run_beta",
      }),
    ).toBeInTheDocument();
  });

  it("restores explicit comparison URL state and canonicalizes mismatched transition context", async () => {
    mockComparisonDetail(buildCompatibleDetail());
    const scrolledIds: string[] = [];
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: function mockScrollIntoView() {
        scrolledIds.push((this as HTMLElement).id);
      },
    });
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?case=case-002&transition=no_failure_to_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Reasoning chain diverged from the rubric.")).toBeInTheDocument();
    expect(
      await screen.findByText(
        "Requested case case-002 is unavailable in this transition context. Showing case-004 instead.",
      ),
    ).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("transitions");
      expect(params.get("case")).toBe("case-004");
      expect(params.get("transition")).toBe("no_failure_to_failure");
      expect(scrolledIds).toContain(
        "comparison-transition-no_failure_to_failure",
      );
    });
  });

  it("preserves comparison detail as the return target when opening a linked run", async () => {
    mockComparisonAndRunDetails(buildCompatibleDetail());
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(new URLSearchParams(window.location.search).get("section")).toBe("transitions");
    });

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(await screen.findByRole("heading", { name: "Reasoning Failures V1" })).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    const returnLink = screen.getByRole("link", { name: "Back to runs" });
    const returnUrl = new URL(returnLink.getAttribute("href") ?? "", "https://example.test");
    expect(returnUrl.pathname).toBe("/comparisons/compare_alpha_to_beta");
    expect(returnUrl.searchParams.get("section")).toBe("transitions");
    expect(returnUrl.searchParams.get("case")).toBe("case-002");
    expect(returnUrl.searchParams.get("transition")).toBe("failure_to_no_failure");
  });

  it("shows focused artifact context on the selected comparison case surface", async () => {
    mockComparisonDetail(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getAllByText("compare_alpha_to_beta").length).toBeGreaterThan(0);
    expect(within(artifactContext).getAllByText("case-002").length).toBeGreaterThan(0);
    expect(within(artifactContext).getByText("/tmp/model-failure-lab")).toBeInTheDocument();
  });

  it("preserves configured artifact-source metadata on the comparison detail route", async () => {
    mockComparisonDetail(buildCompatibleDetail(CONFIGURED_SOURCE));

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"], CONFIGURED_SOURCE)}
        initialRunInventoryState={buildReadyRunInventoryState(undefined, CONFIGURED_SOURCE)}
        initialComparisonInventoryState={buildReadyComparisonInventoryState(CONFIGURED_SOURCE)}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Configured artifact store")).toBeInTheDocument();
    expect(screen.getAllByText("/tmp/external-artifacts").length).toBeGreaterThan(0);

    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getByText("/tmp/external-artifacts")).toBeInTheDocument();
  });

  it("falls back with an explicit notice when exact baseline evidence cannot be resolved after navigation", async () => {
    mockComparisonAndRunDetails(
      buildCompatibleDetail(),
      new Map([
        ["run_alpha", buildFallbackLinkedRunDetail("run_alpha", "reasoning-failures-v1")],
        ["run_beta", buildLinkedRunDetail("run_beta", "reasoning-failures-v1")],
      ]),
    );
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(
      await screen.findByText(
        "Requested case case-002 is unavailable in this evidence state. Showing case-001 instead.",
      ),
    ).toBeInTheDocument();
  });
});
