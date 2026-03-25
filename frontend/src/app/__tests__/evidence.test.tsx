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

    expect(screen.getByRole("heading", { name: /Official-first artifact browser/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Reports$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Evaluations$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Runs$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Official only/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await user.click(screen.getByRole("button", { name: /Include exploratory/i }));

    expect(screen.getByText(/Exploratory evidence is enabled/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Group DRO/i).length).toBeGreaterThan(0);
  });
});
