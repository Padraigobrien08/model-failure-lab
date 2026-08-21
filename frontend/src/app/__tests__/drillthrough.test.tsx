import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("run drillthrough handoff", () => {
  it("redirects the removed failure-explorer drillthrough entry to the runs workspace", () => {
    render(<App useMemoryRouter initialEntries={["/failure-explorer"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
