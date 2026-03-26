import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("evidence route", () => {
  it("renders the official-first evidence browser and makes exploratory scope explicit", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/evidence"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(screen.getByRole("heading", { name: /Artifact browser with live provenance handoff/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Reports$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Evaluations$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Runs$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Official only/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await user.click(screen.getAllByRole("button", { name: /Include exploratory/i })[0]);

    expect(screen.getAllByText(/Exploratory evidence is enabled/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Group DRO/i).length).toBeGreaterThan(0);
  });
});
