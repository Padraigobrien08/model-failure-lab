import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("run drillthrough handoff", () => {
  it("opens the drawer from failure explorer and hands the selected run into the Runs route", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/failure-explorer"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    await user.click(screen.getAllByRole("button", { name: /Inspect Reweighting evidence/i })[0]);
    await user.click(screen.getByRole("link", { name: /Open Run Lineage/i }));

    expect(
      screen.getByRole("heading", { name: /Grouped runs by method lane, then by seed/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Focused run: reweighting_seed_13/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pin in inspector/i })).toBeInTheDocument();
  });
});
