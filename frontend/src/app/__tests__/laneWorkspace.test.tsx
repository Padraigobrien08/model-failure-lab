import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";

describe("Lane workspace", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("keeps expansion separate from inspector selection", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=all"]} />);

    const inspector = screen.getByTestId("lane-inspector");
    expect(within(inspector).getByText("Baseline")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Show runs for Baseline" }));

    expect(screen.getByRole("table", { name: "Baseline runs" })).toBeInTheDocument();
    expect(within(inspector).getByText("Baseline")).toBeInTheDocument();

    await user.click(screen.getByTestId("method-row-reweighting"));

    expect(within(inspector).getByText("Reweighting")).toBeInTheDocument();
  });

  it("updates the inspector from a selected run row and keeps scoped drill links", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=all"]} />);

    await user.click(screen.getByRole("button", { name: "Show runs for Baseline" }));
    await user.click(screen.getByTestId("run-row-distilbert_baseline_seed_13"));

    const inspector = screen.getByTestId("lane-inspector");
    expect(within(inspector).getByText("distilbert_baseline_seed_13")).toBeInTheDocument();
    expect(within(inspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_baseline_seed_13?scope=all",
    );
  });

  it("labels exploratory rows only when scope=all", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=all"]} />);
    expect(screen.getByText("Exploratory")).toBeInTheDocument();

    cleanup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=official"]} />);
    expect(screen.queryByText("Exploratory")).not.toBeInTheDocument();
    expect(screen.queryByText("Group DRO")).not.toBeInTheDocument();
  });
});
