import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BASELINE_RUN_ID, buildRunDetail } from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

const RUN_ROUTE = `/runs/${BASELINE_RUN_ID}`;

function stubRunDetail() {
  return stubFetch([
    { match: "run-detail.json", respond: buildRunDetail(BASELINE_RUN_ID) },
  ]);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RunDetailPage", () => {
  it("renders the metric cards", async () => {
    stubRunDetail();
    renderApp([RUN_ROUTE]);

    expect(await screen.findByText("Failure rate")).toBeInTheDocument();
    expect(screen.getByText("25.0%")).toBeInTheDocument();
    expect(screen.getByText("1 of 3 classified")).toBeInTheDocument();
    expect(screen.getByText("Classification coverage")).toBeInTheDocument();
    expect(screen.getByText("3 / 4")).toBeInTheDocument();
    expect(screen.getByText("Execution success")).toBeInTheDocument();
    expect(screen.getByText("1 error")).toBeInTheDocument();
  });

  it("renders lens segments with counts and filters by lens", async () => {
    stubRunDetail();
    const user = userEvent.setup();
    renderApp([RUN_ROUTE]);
    await screen.findByText("Failure rate");

    expect(screen.getByRole("radio", { name: "all (4)" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "mismatches (1)" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "notable (2)" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "errors (1)" })).toBeInTheDocument();
    expect(screen.getByText("4 cases · dataset order")).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "errors (1)" }));
    expect(screen.getByText("1 case · dataset order")).toBeInTheDocument();
    expect(screen.getByText("case_err")).toBeInTheDocument();
    expect(screen.queryByText("case_reg")).not.toBeInTheDocument();
  });

  it("failure-type strip filters the case table", async () => {
    stubRunDetail();
    const user = userEvent.setup();
    renderApp([RUN_ROUTE]);
    await screen.findByText("Failure rate");

    // Strip button shows label + count · share.
    const strip = screen.getByText("1 · 25.0%").closest("button")!;
    expect(strip).toHaveTextContent("hallucination");
    await user.click(strip);

    expect(screen.getByText("1 case · dataset order")).toBeInTheDocument();
    expect(screen.getByText("case_fix")).toBeInTheDocument();
    expect(screen.queryByText("case_reg")).not.toBeInTheDocument();

    // Chip clears the filter.
    await user.click(screen.getByRole("button", { name: /failure type: hallucination/ }));
    expect(screen.getByText("4 cases · dataset order")).toBeInTheDocument();
  });

  it("row selection opens the right panel with prompt, output, classification and footer", async () => {
    stubRunDetail();
    const user = userEvent.setup();
    renderApp([RUN_ROUTE]);
    await screen.findByText("Failure rate");

    await user.click(screen.getByText("case_reg"));

    const panel = screen.getByText("Case").closest("aside")!;
    expect(
      within(panel).getByText("Cite the source for the 2019 revenue figure."),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText("Baseline answer with the correct citation."),
    ).toBeInTheDocument();
    expect(within(panel).getByText("no_failure")).toBeInTheDocument();
    expect(within(panel).getByText("conf 0.90")).toBeInTheDocument();
    expect(
      within(panel).getByText(`runs/${BASELINE_RUN_ID}/results.json#case_reg`),
    ).toBeInTheDocument();
  });

  it("an error case shows the error block", async () => {
    stubRunDetail();
    const user = userEvent.setup();
    renderApp([RUN_ROUTE]);
    await screen.findByText("Failure rate");

    await user.click(screen.getByText("case_err"));

    const panel = screen.getByText("Case").closest("aside")!;
    expect(within(panel).getByText("Error")).toBeInTheDocument();
    expect(within(panel).getByText("stage model_invocation")).toBeInTheDocument();
    expect(within(panel).getByText("type TimeoutError")).toBeInTheDocument();
    expect(within(panel).getByText("request timed out after 30s")).toBeInTheDocument();
  });
});
