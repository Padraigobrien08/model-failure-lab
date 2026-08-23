import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  REPORT_ID,
  buildComparisonDetail,
  buildGateState,
} from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("GatePage", () => {
  it("shows the blocked banner when a comparison blocks the gate", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("blocked") });
    expect(screen.getByText("1 comparison blocks the gate.")).toBeInTheDocument();
  });

  it("shows the clear banner when the gate passes", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("clear") });
    expect(
      screen.getByText("All recent comparisons pass the gate."),
    ).toBeInTheDocument();
  });

  it("renders policy key/value rows", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("blocked") });

    const minRow = screen.getByText("minimumSeverity").parentElement!;
    expect(within(minRow).getByText("0.25")).toBeInTheDocument();
    const strategyRow = screen.getByText("strategy").parentElement!;
    expect(within(strategyRow).getByText("top_regressions")).toBeInTheDocument();
    const failureTypeRow = screen.getByText("failureType").parentElement!;
    expect(within(failureTypeRow).getByText("—")).toBeInTheDocument();
  });

  it("renders the decisions table with the waiver column", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("blocked") });

    expect(screen.getByText("2 decisions")).toBeInTheDocument();

    const blockedRow = screen.getByText(REPORT_ID).closest("tr")!;
    expect(within(blockedRow).getByText("block")).toBeInTheDocument();
    expect(within(blockedRow).getByText("0.420")).toBeInTheDocument();
    expect(within(blockedRow).getByText("blocked")).toBeInTheDocument();

    const waivedRow = screen.getByText("cmp_waived_002").closest("tr")!;
    expect(within(waivedRow).getByText("clear")).toBeInTheDocument();
    expect(within(waivedRow).getByText("waived")).toBeInTheDocument();
    expect(within(waivedRow).getByText("maya · expires 2026-09-01")).toBeInTheDocument();
  });

  it("row click navigates to the comparison detail", async () => {
    stubFetch([{ match: "comparison-detail.json", respond: buildComparisonDetail() }]);
    const user = userEvent.setup();
    renderApp(["/gate"], { initialGateState: buildGateState("blocked") });

    await user.click(screen.getByText(REPORT_ID));

    expect(
      await screen.findByText(
        "Candidate raised failure rate 10.0 pts on 10 shared cases.",
      ),
    ).toBeInTheDocument();
  });
});
