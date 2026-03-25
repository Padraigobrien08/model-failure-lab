import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("App shell", () => {
  it("renders the locked top-level navigation and defaults to overview", () => {
    render(
      <App
        useMemoryRouter
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    const primaryNavigation = screen.getByRole("navigation", { name: /Primary/i });

    expect(screen.getByRole("heading", { name: /Failure Debugger/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Workbench state/i)).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Overview System index for the final verdict and active scope/i,
      }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Comparisons Rank lanes and inspect why the order holds/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Failure Explorer Separate subgroup, OOD, ID, and calibration stories/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Runs Seeded run lineage and detailed inspection/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Evidence Reports, eval bundles, and manifest-backed paths/i,
      }),
    ).toBeInTheDocument();
  });

  it("makes exploratory scope explicit when toggled on", async () => {
    const user = userEvent.setup();
    render(
      <App
        useMemoryRouter
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Show exploratory evidence/i }));

    expect(screen.getByText(/Scope: Official \+ Exploratory/i)).toBeInTheDocument();
    expect(screen.getByText(/exploratory scope active/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Official \+ Exploratory/i).length).toBeGreaterThanOrEqual(1);
  });
});
