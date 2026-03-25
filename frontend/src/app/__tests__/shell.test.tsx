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
        name: /Overview Final verdicts and official evidence launchpad/i,
      }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Comparisons Method-to-method debugging/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Failure Explorer Subgroup, ID\/OOD, and calibration entrypoints/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Runs Run-level lineage and seed context/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Evidence Raw reports, eval bundles, and metadata paths/i,
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
