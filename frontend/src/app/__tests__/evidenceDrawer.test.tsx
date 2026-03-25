import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("evidence drawer flow", () => {
  it("opens the shared evidence drawer from comparisons without leaving the page", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Inspect Reweighting evidence/i }));

    expect(screen.getByRole("heading", { name: /Quick drillthrough/i })).toBeInTheDocument();
    expect(screen.getByText(/Evidence drawer/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Open in Runs view/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Ranked comparison canvas/i })).toBeInTheDocument();
  });
});
