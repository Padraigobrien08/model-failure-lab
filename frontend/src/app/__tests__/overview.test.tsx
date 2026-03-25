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
        name: /Final evidence, turned into an explorable debugging surface/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Still Mixed/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Defer Now Reopen Under Conditions/i)).toHaveLength(2);
    expect(screen.getByRole("link", { name: /Inspect Failure Traces/i })).toHaveAttribute(
      "href",
      "/comparisons",
    );
    expect(screen.getByText(/Temperature scaling remains the stable calibration lane/i)).toBeInTheDocument();
    expect(
      screen.getByText(/This is the primary UI\. Streamlit remains available as a fallback\./i),
    ).toBeInTheDocument();
  });
});
