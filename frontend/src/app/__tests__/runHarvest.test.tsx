import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CANDIDATE_RUN_ID, buildRunDetail } from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

const HARVEST_WIRE = {
  source: {
    label: "Local artifact root",
    path: "/work/failure-lab-workspace",
    runsPath: "runs/",
    reportsPath: "reports/",
  },
  dataset_id: "run-cand-002-failures-draft",
  lifecycle: "draft",
  mode: "cases",
  output_path: "datasets/harvested/run-cand-002-failures-draft.json",
  selected_case_count: 2,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("run-scoped harvest", () => {
  it("harvests failing cases from a run and shows the draft receipt", async () => {
    const calls = stubFetch([
      { match: "run-detail.json", respond: buildRunDetail(CANDIDATE_RUN_ID) },
      { match: "harvest.json", respond: HARVEST_WIRE },
    ]);
    renderApp([`/runs/${CANDIDATE_RUN_ID}`]);

    const openButton = await screen.findByRole("button", { name: "Harvest failures" });
    await userEvent.click(openButton);

    const dialog = await screen.findByRole("dialog", { name: "Harvest failing cases" });
    expect(dialog).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Write draft pack" }));

    expect(
      await screen.findByText(/wrote datasets\/harvested\/run-cand-002-failures-draft.json/),
    ).toBeInTheDocument();
    expect(screen.getByText(/promote: failure-lab dataset promote/)).toBeInTheDocument();

    const harvestCall = calls.find((call) => call.url.includes("harvest.json"));
    expect(harvestCall?.init?.method).toBe("POST");
    const body = JSON.parse(String(harvestCall?.init?.body));
    expect(body.mode).toBe("cases");
    expect(body.filters.runId).toBe(CANDIDATE_RUN_ID);
  });

  it("scopes the harvest to the active failure-type filter", async () => {
    const calls = stubFetch([
      { match: "run-detail.json", respond: buildRunDetail(CANDIDATE_RUN_ID) },
      { match: "harvest.json", respond: HARVEST_WIRE },
    ]);
    renderApp([`/runs/${CANDIDATE_RUN_ID}?failureType=hallucination`]);

    await userEvent.click(
      await screen.findByRole("button", { name: "Harvest failures" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Write draft pack" }));

    await waitFor(() => {
      const harvestCall = calls.find((call) => call.url.includes("harvest.json"));
      expect(harvestCall).toBeDefined();
      const body = JSON.parse(String(harvestCall?.init?.body));
      expect(body.filters.failureType).toBe("hallucination");
    });
  });

  it("closes on Escape without writing", async () => {
    const calls = stubFetch([
      { match: "run-detail.json", respond: buildRunDetail(CANDIDATE_RUN_ID) },
    ]);
    renderApp([`/runs/${CANDIDATE_RUN_ID}`]);

    await userEvent.click(
      await screen.findByRole("button", { name: "Harvest failures" }),
    );
    await userEvent.keyboard("{Escape}");
    await waitFor(() => {
      expect(
        screen.queryByRole("dialog", { name: "Harvest failing cases" }),
      ).not.toBeInTheDocument();
    });
    expect(calls.some((call) => call.url.includes("harvest.json"))).toBe(false);
  });
});
