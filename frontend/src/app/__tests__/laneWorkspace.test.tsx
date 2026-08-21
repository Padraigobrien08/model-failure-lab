import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("Lane workspace", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("redirects the removed lane workspace routes to the runs workspace", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=all"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
