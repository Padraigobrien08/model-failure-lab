import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  CLUSTER_ID,
  DATASET_ID,
  buildClusterDetailWire,
  buildQueryResponse,
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
