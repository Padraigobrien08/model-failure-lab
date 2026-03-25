import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("runs route", () => {
  it("renders grouped run lanes with balanced run detail", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/runs"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /Grouped runs by method lane, then by seed/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Baseline$/i })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: /Temperature Scaling/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("heading", { name: /Reweighting/i }).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: /Inspect Reweighting run Seed 13/i }));

    expect(screen.getByRole("heading", { name: /Provenance before raw artifacts/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /What changed for this run/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Saved evidence, linked directly from the manifest/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Official only/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
