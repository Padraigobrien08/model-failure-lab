import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("Overview route", () => {
  it("renders final verdicts and the primary CTA from manifest data", () => {
    render(
      <App
        useMemoryRouter
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: /Final verdicts, evidence scope, and next inspection paths\./i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Still Mixed/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Defer Now Reopen Under Conditions/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("link", { name: /Inspect Failure Traces/i })).toHaveAttribute(
      "href",
      "/comparisons",
    );
    expect(screen.getByText(/Temperature scaling remains the stable calibration lane/i)).toBeInTheDocument();
    expect(
      screen.getByText(/This is the primary UI\. Streamlit remains available as a fallback\./i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Next inspection path/i).length).toBeGreaterThanOrEqual(1);
  });
});
