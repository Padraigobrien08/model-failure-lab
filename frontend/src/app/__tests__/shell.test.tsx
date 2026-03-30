import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";

function buildReadyState(overrides?: Partial<ArtifactShellState & { status: "ready" }>): ArtifactShellState {
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
        },
      ],
    },
    message: null,
  };
}

describe("App shell", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders compact top navigation with the active artifact source", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyState()}
        initialRunInventoryState={buildReadyInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(screen.getByRole("link", { name: "Failure Lab" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Comparisons" })).toBeInTheDocument();
    expect(screen.getByText("Artifact source")).toBeInTheDocument();
    expect(screen.getByText("/tmp/model-failure-lab")).toBeInTheDocument();
    expect(screen.getByText("Runs 2")).toBeInTheDocument();
    expect(screen.getByText("Comparisons 1")).toBeInTheDocument();
  });

  it("lands on runs at / and lets users switch to comparisons from the top nav", async () => {
    const user = userEvent.setup();

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
    expect(
      screen.getByText(/scanning the default local artifact root/i),
    ).toBeInTheDocument();
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
