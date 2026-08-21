import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";

describe("sharedFocus flow", () => {
  it("keeps /comparisons on the comparisons workspace without the removed focus workbench", () => {
    render(<App useMemoryRouter initialEntries={["/comparisons"]} />);

    expect(screen.getByRole("link", { name: "Comparisons" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.queryByRole("region", { name: /Workbench state/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Focus lane/i })).not.toBeInTheDocument();
  });
});
