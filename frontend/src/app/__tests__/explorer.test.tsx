import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  CANDIDATE_RUN_ID,
  CLUSTER_ID,
  DATASET_ID,
  REPORT_ID,
  buildClusterDetailWire,
  buildHistorySnapshotWire,
  buildQueryResponse,
  buildRunDetail,
} from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";
import type { RecordedFetch } from "@/test/render";

function stubExplorer(): RecordedFetch[] {
  return stubFetch([
    {
      match: "query.json",
      respond: (url) => {
        const mode = new URL(url, "http://test.local").searchParams.get("mode") ?? "deltas";
        return buildQueryResponse(
          mode as "cases" | "deltas" | "aggregates" | "signals" | "clusters",
        );
      },
    },
    { match: "cluster-detail.json", respond: buildClusterDetailWire() },
  ]);
}

const queryCalls = (calls: RecordedFetch[]) =>
  calls.filter((call) => call.url.includes("query.json"));

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ExplorerPage", () => {
  it("renders the deltas table by default", async () => {
    stubExplorer();
    renderApp(["/evidence"]);

    expect(await screen.findByText("case_reg")).toBeInTheDocument();
    expect(screen.getByText("no_failure_to_failure")).toBeInTheDocument();
    expect(screen.getByText("— → hallucination")).toBeInTheDocument();
    expect(screen.getByText("1 row · limit 200")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Deltas" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("switching mode updates the query URL and refetches", async () => {
    const calls = stubExplorer();
    const user = userEvent.setup();
    renderApp(["/evidence"]);
    await screen.findByText("case_reg");

    await user.click(screen.getByRole("radio", { name: "Aggregates" }));

    // Aggregates table with the bar column.
    expect(await screen.findByText("Group")).toBeInTheDocument();
    const halluRow = screen
      .getByRole("cell", { name: "hallucination" })
      .closest("tr")!;
    expect(within(halluRow).getByText("5")).toBeInTheDocument();

    const modes = queryCalls(calls).map(
      (call) => new URL(call.url, "http://test.local").searchParams.get("mode"),
    );
    expect(modes).toEqual(["deltas", "aggregates"]);
    expect(screen.getByRole("radio", { name: "Aggregates" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("facet selects set URL filter params and refetch", async () => {
    const calls = stubExplorer();
    const user = userEvent.setup();
    renderApp(["/evidence"]);
    await screen.findByText("case_reg");

    await user.selectOptions(screen.getByLabelText("Filter by dataset"), DATASET_ID);

    const last = queryCalls(calls).at(-1)!;
    const params = new URL(last.url, "http://test.local").searchParams;
    expect(params.get("dataset")).toBe(DATASET_ID);
    expect(params.get("mode")).toBe("deltas");
  });

  it("clusters mode row click opens the cluster detail panel", async () => {
    stubExplorer();
    const user = userEvent.setup();
    renderApp(["/evidence?mode=clusters"]);

    expect(await screen.findByText(CLUSTER_ID)).toBeInTheDocument();
    await user.click(screen.getByText(CLUSTER_ID));

    // Panel loads cluster-detail.json.
    expect(
      await screen.findByText("Cases where the candidate invents sources that do not exist."),
    ).toBeInTheDocument();
    expect(screen.getByText("3 occurrences")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Close cluster panel" }),
    ).toBeInTheDocument();
  });

  it("history mode without a scope shows the scope prompt and fetches nothing", async () => {
    const calls = stubExplorer();
    renderApp(["/evidence?mode=history"]);

    expect(
      await screen.findByText("Pick a dataset or model scope to load history."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("run: failure-lab history --dataset <id> · or --model <id>"),
    ).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "History" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.queryByLabelText("Filter by failure type")).not.toBeInTheDocument();
    expect(calls.filter((call) => call.url.includes("history.json"))).toHaveLength(0);
  });

  it("selecting a dataset scope loads history.json and renders trends and tables", async () => {
    const calls = stubFetch([
      { match: "history.json", respond: buildHistorySnapshotWire() },
    ]);
    const user = userEvent.setup();
    renderApp(["/evidence?mode=history"]);
    await screen.findByText("Pick a dataset or model scope to load history.");

    await user.selectOptions(screen.getByLabelText("Filter by dataset"), DATASET_ID);

    // Trend cards.
    expect(await screen.findByText("degrading")).toBeInTheDocument();
    expect(screen.getByText("Run failure-rate trend")).toBeInTheDocument();
    expect(screen.getByText("Comparison severity trend")).toBeInTheDocument();
    expect(screen.getByText("Δ +0.100 · 2 samples · volatility stable")).toBeInTheDocument();

    // Run history table, newest first, with count line.
    expect(screen.getByText("2 runs")).toBeInTheDocument();
    expect(screen.getByText("35.0%")).toBeInTheDocument();

    // Comparison history table.
    expect(screen.getByText("1 comparison")).toBeInTheDocument();
    // Once as the report id cell, once as the recurring-failure comparison chip.
    expect(screen.getAllByText(REPORT_ID)).toHaveLength(2);
    expect(screen.getByText("regression")).toBeInTheDocument();
    expect(screen.getByText("0.360")).toBeInTheDocument();
    expect(screen.getByText("−0.360")).toBeInTheDocument();

    // Recurring failures.
    expect(screen.getByText("hallucination")).toBeInTheDocument();
    expect(screen.getByText("2 occurrences")).toBeInTheDocument();
    expect(screen.getByText("+10.0%")).toBeInTheDocument();

    const historyCall = calls.find((call) => call.url.includes("history.json"))!;
    const params = new URL(historyCall.url, "http://test.local").searchParams;
    expect(params.get("dataset")).toBe(DATASET_ID);
    expect(params.get("model")).toBeNull();
  });

  it("history run row click navigates to the run detail route", async () => {
    stubFetch([
      { match: "history.json", respond: buildHistorySnapshotWire() },
      { match: "run-detail.json", respond: buildRunDetail(CANDIDATE_RUN_ID) },
    ]);
    const user = userEvent.setup();
    renderApp([`/evidence?mode=history&dataset=${DATASET_ID}`]);

    expect(await screen.findByText("degrading")).toBeInTheDocument();
    const runCell = screen.getByText((_, element) =>
      element?.tagName === "TD" && element.textContent === CANDIDATE_RUN_ID,
    );
    await user.click(runCell.closest("tr")!);

    expect(
      await screen.findByRole("heading", { name: CANDIDATE_RUN_ID }),
    ).toBeInTheDocument();
  });

  it("empty state names the sqlite index and the rebuild command", async () => {
    stubFetch([
      { match: "query.json", respond: buildQueryResponse("deltas", []) },
    ]);
    renderApp(["/evidence"]);

    expect(await screen.findByText("No indexed evidence.")).toBeInTheDocument();
    expect(
      screen.getByText(".failure_lab/query_index.sqlite3 · run: failure-lab index rebuild"),
    ).toBeInTheDocument();
  });
});
