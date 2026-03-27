import { cleanup, render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";

describe("Run page", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders the run lineage stack and grouped artifact summary", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/run/distilbert_reweighting_seed_13?scope=all&lane=calibration&method=reweighting"]}
      />,
    );

    expect(screen.getByText("Interpretation")).toBeInTheDocument();
    expect(screen.getByText("Lineage")).toBeInTheDocument();
    expect(screen.getByText("Parent method")).toBeInTheDocument();
    expect(screen.getByText("Parent run")).toBeInTheDocument();
    expect(screen.getByText("Current run")).toBeInTheDocument();
    expect(screen.getByText("Child evidence")).toBeInTheDocument();
    expect(screen.getByText("Artifacts")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Calibration" })).toHaveAttribute(
      "href",
      "/lane/calibration?scope=all",
    );
    expect(screen.getByRole("link", { name: "Reweighting" })).toHaveAttribute(
      "href",
      "/lane/calibration/reweighting?scope=all",
    );
  });

  it("shows a provenance-only inspector with open raw while keeping artifact actions in the main column", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting"]}
      />,
    );

    const inspector = screen.getByTestId("run-inspector");

    expect(within(inspector).getByText("Source path")).toBeInTheDocument();
    expect(within(inspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
    );
    expect(screen.getByRole("link", { name: "Run report" })).toHaveAttribute(
      "href",
      "/mock-artifacts/distilbert_reweighting_seed_13/report.md",
    );
    expect(within(inspector).queryByRole("link", { name: "Run report" })).not.toBeInTheDocument();
  });
});
