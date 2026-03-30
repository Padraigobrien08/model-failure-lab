import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
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

describe("runs route", () => {
  it("renders a dense newest-first inventory table from the active source", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState(SAMPLE_RUNS.map((run) => run.runId))}
        initialRunInventoryState={buildReadyInventoryState(SAMPLE_RUNS)}
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

  it("opens the dedicated run route from both row activation and the explicit affordance", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState(SAMPLE_RUNS.map((run) => run.runId))}
        initialRunInventoryState={buildReadyInventoryState(SAMPLE_RUNS)}
      />,
    );

    await user.click(screen.getByRole("link", { name: "Open run run_gamma" }));
    expect(
      await screen.findByRole("heading", { name: "run_gamma" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Run breadcrumb" })).toBeInTheDocument();
    expect(screen.getByText("hallucination-failures-v1")).toBeInTheDocument();

    const backToRuns = screen.getAllByRole("link", { name: "Back to runs" })[0];
    await user.click(backToRuns);

    const row = screen.getByRole("link", { name: "Open run run_beta" });
    await user.click(within(row).getByRole("button", { name: "Open run_beta" }));
    expect(
      await screen.findByRole("heading", { name: "run_beta" }),
    ).toBeInTheDocument();
  });

  it("shows a route-level empty state when the shell is ready but no runs exist", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyArtifactState([])}
        initialRunInventoryState={buildReadyInventoryState([])}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "No saved runs are available yet." }),
    ).toBeInTheDocument();
    expect(screen.getByText(/there are no `runs\/<run_id>` directories/i)).toBeInTheDocument();
  });
});
