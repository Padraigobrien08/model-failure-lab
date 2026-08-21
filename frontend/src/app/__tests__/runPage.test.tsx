import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("Run page", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("redirects the removed /run/:runId workspace routes to the runs workspace", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={[
          "/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting",
        ]}
      />,
    );

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
