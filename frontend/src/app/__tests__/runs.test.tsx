import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  BASELINE_RUN_ID,
  CANDIDATE_RUN_ID,
  buildComparisonDetail,
  buildReadyComparisonInventoryState,
  buildReadyRunInventoryState,
} from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RunsPage", () => {
  it("renders run rows with id, dataset, model, failure rate, and the count line", () => {
    renderApp(["/"]);

    expect(screen.getByText("2 runs · newest first")).toBeInTheDocument();

    const baselineRow = screen.getByText(BASELINE_RUN_ID).closest("tr")!;
    expect(within(baselineRow).getByText("qa-failures-v1")).toBeInTheDocument();
    expect(within(baselineRow).getByText("demo-baseline")).toBeInTheDocument();
    expect(within(baselineRow).getByText("25.0%")).toBeInTheDocument();

    const candidateRow = screen.getByText(CANDIDATE_RUN_ID).closest("tr")!;
    expect(within(candidateRow).getByText("demo-candidate")).toBeInTheDocument();
    expect(within(candidateRow).getByText("35.0%")).toBeInTheDocument();
  });

  it("narrows via the id filter and the no-match state names the filter", async () => {
    const user = userEvent.setup();
    renderApp(["/"]);

    const input = screen.getByLabelText("Filter runs by id");
    await user.type(input, "cand");
    expect(screen.getByText("1 run · newest first")).toBeInTheDocument();
    expect(screen.queryByText(BASELINE_RUN_ID)).not.toBeInTheDocument();

    await user.clear(input);
    await user.type(input, "zzz");
    expect(screen.getByText("No runs match the current filters.")).toBeInTheDocument();
    expect(screen.getByText('clear the run id filter "zzz"')).toBeInTheDocument();
  });

  it("shows the selection bar with truncated ids when two runs are selected", async () => {
    const user = userEvent.setup();
    renderApp(["/"]);

    await user.click(
      screen.getByLabelText(`Select ${BASELINE_RUN_ID} for comparison`),
    );
    await user.click(
      screen.getByLabelText(`Select ${CANDIDATE_RUN_ID} for comparison`),
    );

    expect(screen.getByText("2 selected")).toBeInTheDocument();
    const bar = screen.getByText("2 selected").parentElement!;
    expect(bar).toHaveTextContent("…_base_001");
    expect(bar).toHaveTextContent("…_cand_002");
    expect(bar).toHaveTextContent("same dataset · qa-failures-v1");
  });

  it("Build comparison navigates to the matching comparison detail", async () => {
    stubFetch([{ match: "comparison-detail.json", respond: buildComparisonDetail() }]);
    const user = userEvent.setup();
    renderApp(["/"]);

    await user.click(
      screen.getByLabelText(`Select ${BASELINE_RUN_ID} for comparison`),
    );
    await user.click(
      screen.getByLabelText(`Select ${CANDIDATE_RUN_ID} for comparison`),
    );
    await user.click(screen.getByRole("button", { name: "Build comparison" }));

    expect(
      await screen.findByText(
        "Candidate raised failure rate 10.0 pts on 10 shared cases.",
      ),
    ).toBeInTheDocument();
  });

  it("shows the CLI message when no saved comparison matches the pair", async () => {
    const user = userEvent.setup();
    renderApp(["/"], {
      initialComparisonInventoryState: buildReadyComparisonInventoryState([]),
    });

    await user.click(
      screen.getByLabelText(`Select ${BASELINE_RUN_ID} for comparison`),
    );
    await user.click(
      screen.getByLabelText(`Select ${CANDIDATE_RUN_ID} for comparison`),
    );
    await user.click(screen.getByRole("button", { name: "Build comparison" }));

    expect(
      screen.getByText(
        `no saved comparison for this pair · run: failure-lab compare ${BASELINE_RUN_ID} ${CANDIDATE_RUN_ID}`,
      ),
    ).toBeInTheDocument();
  });

  it("empty inventory names the runs/ path and the failure-lab run command", () => {
    renderApp(["/"], { initialRunInventoryState: buildReadyRunInventoryState([]) });

    expect(screen.getByText("No saved runs.")).toBeInTheDocument();
    expect(
      screen.getByText("read runs/ · run: failure-lab run --dataset <dataset> --model <model>"),
    ).toBeInTheDocument();
  });
});
