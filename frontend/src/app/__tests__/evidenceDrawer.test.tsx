import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("evidence drawer flow", () => {
  it("keeps /comparisons on the comparisons workspace without the removed evidence drawer", () => {
    render(<App useMemoryRouter initialEntries={["/comparisons"]} />);

    expect(screen.getByRole("link", { name: "Comparisons" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(
      screen.queryByRole("button", { name: /Inspect Reweighting evidence/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Live inspector/i)).not.toBeInTheDocument();
  });
});
