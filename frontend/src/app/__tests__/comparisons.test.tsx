import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("lanes route", () => {
  it("redirects legacy comparisons URLs into the lane workspace with official-first ordering", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /Robustness lane workspace\./i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Robustness$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Calibration$/i })).toBeInTheDocument();

    const cards = screen.getAllByText(/Ranked method summary/i);
    expect(cards).toHaveLength(3);
    expect(screen.getAllByRole("heading", { name: /Temperature Scaling/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("heading", { name: /Reweighting/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("heading", { name: /DistilBERT Baseline/i }).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Group DRO/i)).not.toBeInTheDocument();
  });

  it("expands seeded detail and reveals exploratory methods only when scope is enabled", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/lanes"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    const reweightingCard = screen.getAllByRole("heading", {
      name: /Reweighting/i,
    })[0].closest("div");
    expect(reweightingCard).not.toBeNull();

    await user.click(screen.getAllByRole("button", { name: /Show per-seed breakdown/i })[0]);
    expect(screen.getByText(/Seed 13/i)).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: /Include exploratory/i })[0]);
    expect(screen.getAllByRole("heading", { name: /Group DRO/i })).not.toHaveLength(0);
  });
});
