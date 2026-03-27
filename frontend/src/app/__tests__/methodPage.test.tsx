import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";

describe("Method page", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders the fixed explanation blocks and compact lineage chain", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting"]} />);

    expect(screen.getByText("What improved")).toBeInTheDocument();
    expect(screen.getByText("What regressed")).toBeInTheDocument();
    expect(screen.getByText("Reason for status")).toBeInTheDocument();
    expect(screen.getByText("Parent")).toBeInTheDocument();
    expect(screen.getByText("Current method")).toBeInTheDocument();
    expect(screen.getByText("Child runs")).toBeInTheDocument();
  });

  it("keeps the first official run selected by default and updates the inspector on explicit selection", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />);

    const inspector = screen.getByTestId("method-inspector");
    expect(within(inspector).getByText("distilbert_reweighting_seed_13")).toBeInTheDocument();
    expect(within(inspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
    );

    await user.click(screen.getByTestId("method-run-row-distilbert_reweighting_seed_42"));

    expect(within(inspector).getByText("distilbert_reweighting_seed_42")).toBeInTheDocument();
    expect(within(inspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_42?scope=all",
    );
  });

  it("shows a recoverable scope warning instead of silently falling back from an exploratory method", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness/group_dro?scope=official"]} />);

    expect(screen.getByRole("heading", { name: "Group DRO", level: 1 })).toBeInTheDocument();
    expect(screen.getByTestId("method-scope-hidden")).toBeInTheDocument();
    expect(screen.getByText("Scope warning")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Include exploratory" })).toHaveAttribute(
      "href",
      "/lane/robustness/group_dro?scope=all",
    );
    expect(screen.queryByRole("table", { name: "Reweighting runs" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Include exploratory" }));

    expect(await screen.findByRole("table", { name: "Group DRO runs" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  });
});
