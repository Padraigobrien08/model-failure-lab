import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("evidence route", () => {
  it("redirects the removed evidence browser route to the runs workspace", () => {
    render(<App useMemoryRouter initialEntries={["/evidence"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
