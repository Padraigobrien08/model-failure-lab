import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("Raw debug page", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("redirects the removed raw debug routes to the runs workspace", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/debug/raw/run_distilbert_reweighting_seed_13?scope=all"]}
      />,
    );

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
