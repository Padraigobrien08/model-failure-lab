import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("Verdicts route", () => {
  it("renders the final verdict, supporting lanes, and trace path from manifest data", () => {
    render(
      <App
        useMemoryRouter
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: /Verdict traceability starts with the final decision\./i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Still Mixed/i).length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/Why the final verdict still turns on worst-group and OOD tradeoffs under shift\./i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Why reliability moved more cleanly than robustness in the official package\./i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen
        .getAllByRole("link", { name: /^Trace Evidence$/i })
        .some((link) => link.getAttribute("href") === "/lanes?lane=robustness"),
    ).toBe(true);
    expect(screen.getByText(/Supporting narrative and reopen conditions/i)).toBeInTheDocument();
  });
});
