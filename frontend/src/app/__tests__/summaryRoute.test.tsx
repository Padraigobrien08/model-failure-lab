import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("Summary route", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders the runs workspace at / instead of the removed verdict summary", () => {
    render(<App useMemoryRouter initialEntries={["/"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Where should I look?" }),
    ).not.toBeInTheDocument();
  });
});
