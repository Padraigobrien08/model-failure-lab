import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("App shell", () => {
  it("renders the locked top-level navigation and defaults to verdicts", () => {
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
        name: /Verdicts Final verdict, supporting lanes, and first evidence path/i,
      }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Lanes Calibration-versus-robustness workspace and method ordering/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Runs Run lineage, seeded detail, and artifact handoff/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Evidence Reports, eval bundles, and manifest-backed artifact paths/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Manifest Contract provenance, visibility flags, and entity relationships/i,
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

    await user.click(screen.getByRole("button", { name: /Include exploratory/i }));

    expect(screen.getByText(/Scope: Official \+ Exploratory/i)).toBeInTheDocument();
    expect(screen.getByText(/exploratory scope active/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Official \+ Exploratory/i).length).toBeGreaterThanOrEqual(1);
  });
});
