import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("Verdicts route", () => {
  it("lands on the runs workspace instead of the removed manifest verdict view", () => {
    render(<App useMemoryRouter initialEntries={["/"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", {
        name: /Verdict traceability starts with the final decision\./i,
      }),
    ).not.toBeInTheDocument();
  });
});
