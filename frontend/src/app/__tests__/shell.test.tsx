import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactOverview,
  ArtifactShellState,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";

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

function buildReadyState(
  overrides?: Partial<ArtifactShellState & { status: "ready" }>,
): ArtifactShellState {
  return {
    status: "ready",
    overview: {
      status: "ready",
      source: DEFAULT_SOURCE,
      runs: {
        count: 2,
        ids: ["run_alpha", "run_beta"],
      },
      comparisons: {
        count: 1,
        ids: ["compare_alpha_to_beta"],
      },
      issues: [],
      message: null,
    },
    ...overrides,
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
          createdAt: "2026-03-30T11:40:00Z",
          status: "improved",
          compatible: true,
          ...buildSignalInventoryFields("improvement", 0.18, {
            failureType: "hallucination",
            delta: -0.18,
            caseIds: ["case-002"],
          }),
        },
      ],
    },
    message: null,
  };
}

describe("App shell", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.history.replaceState({}, "", "/");
  });

  it("renders compact top navigation with the active artifact source", () => {
    const configuredOverview: ArtifactOverview = {
      status: "ready",
      source: CONFIGURED_SOURCE,
      runs: {
        count: 2,
        ids: ["run_alpha", "run_beta"],
      },
      comparisons: {
        count: 1,
        ids: ["compare_alpha_to_beta"],
      },
      issues: [],
      message: null,
    };

    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyState({
          overview: configuredOverview,
        })}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(screen.getByRole("link", { name: "Failure Lab" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Analysis" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Comparisons" })).toBeInTheDocument();
    expect(screen.getByText("Artifact source")).toBeInTheDocument();
    expect(screen.getByText("Configured artifact store")).toBeInTheDocument();
    expect(screen.getByText("/tmp/external-artifacts")).toBeInTheDocument();
    expect(screen.getByText("Runs 2")).toBeInTheDocument();
    expect(screen.getByText("Comparisons 1")).toBeInTheDocument();
  });

  it("lands on runs at / and lets users switch to comparisons from the top nav", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({
          source: DEFAULT_SOURCE,
          mode: "cases",
          filters: {
            failureType: null,
            model: null,
            dataset: null,
            runId: null,
            reportId: null,
            baselineRunId: null,
            candidateRunId: null,
            delta: null,
            aggregateBy: null,
            lastN: null,
            since: null,
            until: null,
            limit: 20,
          },
          facets: {
            models: ["demo", "gpt-4.1-mini"],
            datasets: ["reasoning-failures-v1", "hallucination-failures-v1"],
            failureTypes: ["hallucination"],
            deltaTypes: ["regression", "improvement"],
          },
          rows: [],
        }),
      })),
    );

    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyState()}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Saved runs inventory." }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Analysis" }));

    expect(
      await screen.findByRole("heading", {
        name: "Cross-run artifact analysis.",
      }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Comparisons" }));

    expect(
      await screen.findByRole("heading", {
        name: "Saved comparisons inventory.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Comparisons" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("shows an explicit loading state before artifacts are available", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={{ status: "loading", overview: null }}
        initialRunInventoryState={{
          status: "idle",
          inventory: null,
          message: null,
        }}
        initialComparisonInventoryState={{
          status: "idle",
          inventory: null,
          message: null,
        }}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Loading saved engine artifacts." }),
    ).toBeInTheDocument();
    expect(screen.getByText(/scanning the active artifact root/i)).toBeInTheDocument();
  });

  it("shows an explicit incompatible-artifact state instead of falling back to legacy data", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialArtifactState={{
          status: "incompatible",
          overview: {
            status: "incompatible",
            source: {
              label: "Repo root artifact store",
              path: "/tmp/model-failure-lab",
              runsPath: "/tmp/model-failure-lab/runs",
              reportsPath: "/tmp/model-failure-lab/reports",
            },
            runs: { count: 0, ids: [] },
            comparisons: { count: 0, ids: [] },
            issues: ["run demo_run is missing run.json or results.json"],
            message: "Saved artifacts do not match the supported contract.",
          },
        }}
        initialRunInventoryState={{
          status: "idle",
          inventory: null,
          message: null,
        }}
        initialComparisonInventoryState={{
          status: "idle",
          inventory: null,
          message: null,
        }}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "The saved artifacts do not match the supported shell contract.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Saved artifacts do not match the supported contract.")).toBeInTheDocument();
    expect(screen.getByText("run demo_run is missing run.json or results.json")).toBeInTheDocument();
  });
});
