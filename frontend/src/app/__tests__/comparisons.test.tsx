import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import type { ArtifactShellState, RunInventoryState } from "@/lib/artifacts/types";

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

describe("comparisons route", () => {
  it("summarizes detected comparison artifacts from the active source", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialArtifactState={buildReadyState([
          "compare_alpha_to_beta",
          "compare_beta_to_gamma",
        ])}
        initialRunInventoryState={buildReadyInventoryState()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Saved comparisons stay secondary to runs." }),
    ).toBeInTheDocument();
    expect(screen.getByText("/tmp/model-failure-lab/reports")).toBeInTheDocument();
    expect(screen.getByText("compare_alpha_to_beta")).toBeInTheDocument();
    expect(screen.getByText("compare_beta_to_gamma")).toBeInTheDocument();
  });

  it("shows a route-level empty state when no comparison reports exist yet", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialArtifactState={buildReadyState([])}
        initialRunInventoryState={buildReadyInventoryState()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "No comparison reports are available yet." }),
    ).toBeInTheDocument();
    expect(screen.getByText(/generate a comparison with `failure-lab compare`/i)).toBeInTheDocument();
  });
});
