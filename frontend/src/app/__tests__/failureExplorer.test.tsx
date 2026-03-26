import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("failureExplorer route", () => {
  it("redirects legacy failure-explorer URLs into the lane workspace and keeps the four domain tabs", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/failure-explorer"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(screen.getByRole("heading", { name: /Robustness lane workspace\./i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Worst Group/i })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: /^OOD$/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /^ID$/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Calibration/i })).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: /Show per-seed breakdown/i })[0]);
    expect(screen.getByText(/Seed 13/i)).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /Calibration/i }));
    expect(screen.getAllByRole("heading", { name: /Calibration/i }).length).toBeGreaterThanOrEqual(
      1,
    );
    expect(screen.getAllByText(/ECE -0.011 \/ Brier -0.001/i).length).toBeGreaterThanOrEqual(1);
  });
});
