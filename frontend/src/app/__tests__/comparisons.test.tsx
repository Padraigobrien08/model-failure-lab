import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("comparisons route", () => {
  it("renders the ranked comparison canvas with official-first ordering", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /Ranked comparison canvas/i }),
    ).toBeInTheDocument();

    const cards = screen.getAllByText(/Ranked method summary/i);
    expect(cards).toHaveLength(3);
    expect(screen.getByRole("heading", { name: /Temperature Scaling/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Reweighting/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /DistilBERT Baseline/i })).toBeInTheDocument();
    expect(screen.queryByText(/Group DRO/i)).not.toBeInTheDocument();
  });

  it("expands seeded detail and reveals exploratory methods only when scope is enabled", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    const reweightingCard = screen.getByRole("heading", {
      name: /Reweighting/i,
    }).closest("div");
    expect(reweightingCard).not.toBeNull();

    await user.click(screen.getAllByRole("button", { name: /Show per-seed breakdown/i })[0]);
    expect(screen.getByText(/Seed 13/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Show exploratory evidence/i }));
    expect(screen.getAllByRole("heading", { name: /Group DRO/i })).not.toHaveLength(0);
  });
});
