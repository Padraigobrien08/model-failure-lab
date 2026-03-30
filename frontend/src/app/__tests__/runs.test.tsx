import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import type { ArtifactShellState } from "@/lib/artifacts/types";

function buildReadyState(runIds: string[]): ArtifactShellState {
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

describe("runs route", () => {
  it("summarizes detected run artifacts from the active source", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyState(["run_alpha", "run_beta", "run_gamma"])}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Saved runs are now the home route." }),
    ).toBeInTheDocument();
    expect(screen.getByText("/tmp/model-failure-lab/runs")).toBeInTheDocument();
    expect(screen.getByText("run_alpha")).toBeInTheDocument();
    expect(screen.getByText("run_beta")).toBeInTheDocument();
    expect(screen.getByText("run_gamma")).toBeInTheDocument();
  });

  it("shows a route-level empty state when the shell is ready but no runs exist", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/"]}
        initialArtifactState={buildReadyState([])}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "No saved runs are available yet." }),
    ).toBeInTheDocument();
    expect(screen.getByText(/there are no `runs\/<run_id>` directories/i)).toBeInTheDocument();
  });
});
