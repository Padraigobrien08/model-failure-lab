import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
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

describe("comparisons route", () => {
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

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
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
    expect(screen.getByRole("navigation", { name: "Comparison breadcrumb" })).toBeInTheDocument();
    expect(screen.getByText("Selected comparison route is ready.")).toBeInTheDocument();
  });
});
