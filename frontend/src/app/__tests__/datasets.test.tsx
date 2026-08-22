import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FAMILY_ID, buildDatasetVersionsResponse } from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DatasetsPage", () => {
  it("renders the families table from the initial dataset families state", () => {
    renderApp(["/datasets"]);

    expect(screen.getByText("2 families")).toBeInTheDocument();

    const qaRow = screen.getByText(FAMILY_ID).closest("tr")!;
    expect(within(qaRow).getByText("v2")).toBeInTheDocument();
    expect(within(qaRow).getByText("12")).toBeInTheDocument();
    expect(within(qaRow).getByText("hallucination")).toBeInTheDocument();
    expect(within(qaRow).getByText("10.0%")).toBeInTheDocument();

    const safetyRow = screen.getByText("safety-regressions").closest("tr")!;
    expect(within(safetyRow).getByText("refusal")).toBeInTheDocument();
    expect(within(safetyRow).getByText("40.0%")).toBeInTheDocument();
  });

  it("health chips carry the tone matching the label", () => {
    renderApp(["/datasets"]);

    expect(screen.getByText("healthy").className).toContain("text-good");
    expect(screen.getByText("regressing").className).toContain("text-bad");
  });

  it("row click navigates to the family page with stats, versions and empty lifecycle", async () => {
    stubFetch([
      { match: "dataset-versions.json", respond: buildDatasetVersionsResponse() },
    ]);
    const user = userEvent.setup();
    renderApp(["/datasets"]);

    await user.click(screen.getByText(FAMILY_ID));

    // Stat cards.
    expect(await screen.findByText("latest v2")).toBeInTheDocument();
    const versionsCard = screen.getByText("latest v2").parentElement!;
    expect(within(versionsCard).getByText("2")).toBeInTheDocument();
    expect(screen.getAllByText("qa-regressions-v2").length).toBeGreaterThan(0);

    // Versions table, newest first.
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("v2");
    expect(rows[0]).toHaveTextContent("datasets/qa-regressions-v2.json");
    expect(rows[0]).toHaveTextContent("regression");
    expect(rows[0]).toHaveTextContent("0.420");
    expect(rows[1]).toHaveTextContent("v1");

    // Lifecycle empty note.
    expect(
      screen.getByText(
        `none recorded · read governance/lifecycle_actions/${FAMILY_ID}/`,
      ),
    ).toBeInTheDocument();

    // Collapsed detail panels.
    for (const title of ["Portfolio", "Plans", "Executions", "Outcomes"]) {
      const details = screen.getByText(title).closest("details")!;
      expect(details.open).toBe(false);
    }
  });
});
