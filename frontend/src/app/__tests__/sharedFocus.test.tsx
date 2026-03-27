import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("sharedFocus flow", () => {
  it("carries selected method and domain focus from comparisons into failure explorer", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons"]}
        initialIndex={buildManifestFixture()}
        initialFinalRobustnessBundle={buildFinalRobustnessBundleFixture()}
      />,
    );

    const reweightingCard = screen.getAllByRole("heading", {
      name: /Reweighting/i,
    })[0].closest('[class*="rounded"]');
    expect(reweightingCard).not.toBeNull();

    await user.click(
      within(reweightingCard as HTMLElement).getByRole("button", { name: /Focus lane/i }),
    );
    await user.click(screen.getByRole("link", { name: /Trace Worst Group/i }));

    const workbenchState = screen.getByRole("region", { name: /Workbench state/i });

    expect(within(workbenchState).getByText(/^Robustness$/i)).toBeInTheDocument();
    expect(within(workbenchState).getByText(/^Reweighting$/i)).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Worst Group/i })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getAllByRole("button", { name: /Focused lane/i })[0]).toBeInTheDocument();
  });
});
