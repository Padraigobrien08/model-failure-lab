import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("evidence drawer flow", () => {
  it("opens the shared evidence drawer from comparisons without leaving the page", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    await user.click(screen.getAllByRole("button", { name: /Inspect Reweighting evidence/i })[0]);

    expect(screen.getAllByRole("heading", { name: /Reweighting/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Live inspector/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /Open Run Lineage/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Ranked comparison canvas/i })).toBeInTheDocument();
  });
});
