import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  BASELINE_RUN_ID,
  REPORT_ID,
  buildComparisonDetail,
  buildRunDetail,
} from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

const DETAIL_ROUTE = `/comparisons/${REPORT_ID}`;

function stubDetail() {
  return stubFetch([
    { match: "comparison-detail.json", respond: buildComparisonDetail() },
    {
      match: "run-detail.json",
      respond: (url) => {
        const runId = new URL(url, "http://test.local").searchParams.get("runId");
        return buildRunDetail(runId ?? BASELINE_RUN_ID);
      },
    },
  ]);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ComparisonDetailPage", () => {
  it("renders the verdict banner with headline, REGRESSED chip and CI gate FAIL", async () => {
    stubDetail();
    renderApp([DETAIL_ROUTE]);

    expect(
      await screen.findByText(
        "Candidate raised failure rate 10.0 pts on 10 shared cases.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Regressed")).toBeInTheDocument();

    // The gate state row matching this reportId is blocked.
    const gatePanel = screen.getByText("CI gate").parentElement!;
    expect(within(gatePanel).getByText("FAIL")).toBeInTheDocument();
    expect(within(gatePanel).getByText("blocked")).toBeInTheDocument();
    expect(gatePanel).toHaveTextContent("policy: severity_above_threshold");
  });

  it("renders four delta cards with signed pts values", async () => {
    stubDetail();
    renderApp([DETAIL_ROUTE]);
    await screen.findByText("Regressed");

    expect(screen.getByText("Failure rate")).toBeInTheDocument();
    expect(screen.getByText("+10.0 pts")).toBeInTheDocument();
    expect(screen.getByText("Classification coverage")).toBeInTheDocument();
    expect(screen.getByText("+0.0 pts")).toBeInTheDocument();
    expect(screen.getByText("Execution success")).toBeInTheDocument();
    expect(screen.getByText("−5.0 pts")).toBeInTheDocument();
    expect(screen.getByText("Shared scope")).toBeInTheDocument();
    expect(screen.getByText("10 / 12")).toBeInTheDocument();
  });

  it("renders top drivers with monospace failure types and evidence chips navigating to evidence", async () => {
    stubDetail();
    const user = userEvent.setup();
    renderApp([DETAIL_ROUTE]);
    await screen.findByText("Regressed");

    const driversSection = screen.getByText("Top drivers").closest("section")!;
    const driverCell = within(driversSection).getByText("hallucination");
    expect(driverCell.className).toContain("font-mono");
    expect(within(driversSection).getByText("+20.0%")).toBeInTheDocument();

    // Evidence chip for the first regressed case.
    await user.click(within(driversSection).getByRole("button", { name: "case_reg" }));

    // Landed on the evidence route: case rail + prompt band.
    expect(await screen.findByText("Changed cases · 3")).toBeInTheDocument();
    expect(
      await screen.findByText("Cite the source for the 2019 revenue figure."),
    ).toBeInTheDocument();
  });

  it("groups transitions with count and share", async () => {
    stubDetail();
    renderApp([DETAIL_ROUTE]);
    await screen.findByText("Regressed");

    expect(screen.getByText("Case transitions · 3 changed")).toBeInTheDocument();
    const header = screen.getByText("no_failure_to_failure").closest("div")!;
    expect(within(header).getByText("1 case · 33%")).toBeInTheDocument();
    expect(screen.getByText("failure_type_swap")).toBeInTheDocument();
    expect(screen.getByText("failure_to_no_failure")).toBeInTheDocument();
  });

  it("Matrix segment switches to the matrix table via the section URL param", async () => {
    stubDetail();
    const user = userEvent.setup();
    renderApp([DETAIL_ROUTE]);
    await screen.findByText("Regressed");

    await user.click(screen.getByRole("radio", { name: "Matrix" }));

    expect(screen.getByRole("radio", { name: "Matrix" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByText("baseline ↓ / cand →")).toBeInTheDocument();
    expect(
      screen.getByText(/^matrix covers the 3 changed cases/),
    ).toBeInTheDocument();
  });

  it("deep-linking with section=matrix renders the matrix directly", async () => {
    stubDetail();
    renderApp([`${DETAIL_ROUTE}?section=matrix`]);
    await screen.findByText("Regressed");
    expect(screen.getByText("baseline ↓ / cand →")).toBeInTheDocument();
  });

  it("governance details panel renders action and policyRule", async () => {
    stubDetail();
    const user = userEvent.setup();
    renderApp([DETAIL_ROUTE]);
    await screen.findByText("Regressed");

    const summary = screen.getByText("Governance · evolve · severity_above_threshold");
    await user.click(summary);
    expect(
      screen.getByText(
        "Recurring hallucination regressions warrant evolving the family.",
      ),
    ).toBeInTheDocument();
    const panel = summary.closest("details")!;
    expect(panel).toHaveTextContent("family qa-regressions · 2 versions · 12 cases");
    expect(panel).toHaveTextContent("proposed +2 → 14 cases");
  });

  it("Open report.json toggles the raw JSON view", async () => {
    stubDetail();
    const user = userEvent.setup();
    renderApp([DETAIL_ROUTE]);
    await screen.findByText("Regressed");

    await user.click(screen.getByRole("button", { name: "Open report.json" }));

    expect(screen.getByRole("button", { name: "Close report.json" })).toBeInTheDocument();
    expect(
      screen.getByText(/"reportId": "cmp_001"/, { selector: "pre" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Close report.json" }));
    expect(screen.getByText("Regressed")).toBeInTheDocument();
  });
});
