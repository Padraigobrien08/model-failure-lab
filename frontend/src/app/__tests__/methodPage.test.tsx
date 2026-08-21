import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("Method page", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("redirects the removed method page routes to the runs workspace", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
