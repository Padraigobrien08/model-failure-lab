import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { REPORT_ID, buildComparisonDetail } from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

const DRAFT_WIRE = {
  source: {
    label: "Local artifact root",
    path: "/work/failure-lab-workspace",
    runsPath: "runs/",
    reportsPath: "reports/",
  },
  drafts: [
    {
      dataset_id: "qa-regressions-draft",
      name: "Qa Regressions Draft",
      lifecycle: "draft",
      created_at: "2026-08-22T23:03:49Z",
      case_count: 4,
      mode: "deltas",
      origin: "regression_signal_pack",
      comparison_report_id: REPORT_ID,
      run_id: null,
      failure_type: null,
      suggested_family_id: "qa-regressions",
      path: "datasets/harvested/qa-regressions-draft.json",
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("dataset drafts section", () => {
  it("lists harvested drafts with source link and promote receipt", async () => {
    stubFetch([{ match: "dataset-drafts.json", respond: DRAFT_WIRE }]);
    renderApp(["/datasets"]);

    expect(await screen.findByText("qa-regressions-draft")).toBeInTheDocument();
    expect(screen.getByText("1 draft · datasets/harvested/")).toBeInTheDocument();
    expect(screen.getAllByText("qa-regressions").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/promote: failure-lab dataset promote/),
    ).toBeInTheDocument();
  });

  it("navigates to the source comparison from a draft row", async () => {
    stubFetch([
      { match: "dataset-drafts.json", respond: DRAFT_WIRE },
      { match: "comparison-detail.json", respond: buildComparisonDetail() },
    ]);
    renderApp(["/datasets"]);

    const sourceLink = await screen.findByRole("button", { name: /…_001|cmp_001/ });
    await userEvent.click(sourceLink);
    await waitFor(() => {
      // The heading names the two runs, so landing on the right comparison is what this
      // asserts -- a constant heading would have passed for any comparison at all.
      expect(
        screen.getByRole("heading", { level: 1, name: "…_base_001 → …_cand_002" }),
      ).toBeInTheDocument();
    });
  });

  it("shows the empty note when no drafts exist", async () => {
    stubFetch([
      {
        match: "dataset-drafts.json",
        respond: { source: DRAFT_WIRE.source, drafts: [] },
      },
    ]);
    renderApp(["/datasets"]);

    expect(
      await screen.findByText(/no drafts awaiting promotion/),
    ).toBeInTheDocument();
  });
});
