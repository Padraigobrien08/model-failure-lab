import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  BASELINE_RUN_ID,
  REPORT_ID,
  buildComparisonDetail,
  buildRunDetail,
} from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

const EVIDENCE_ROUTE = `/comparisons/${REPORT_ID}/evidence`;

function stubEvidence() {
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

// Rail entries are buttons whose accessible name starts with the case id
// followed by the baseline → candidate label.
const railButtonName = (caseId: string) => new RegExp(`^${caseId} `);

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("EvidencePage", () => {
  it("lists regressed cases by default and orders regressions first under All", async () => {
    stubEvidence();
    const user = userEvent.setup();
    renderApp([EVIDENCE_ROUTE]);

    expect(await screen.findByText("Changed cases · 3")).toBeInTheDocument();

    // Regressed scope: only the no_failure_to_failure case.
    expect(
      screen.getByRole("button", { name: railButtonName("case_reg") }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: railButtonName("case_swap") }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: railButtonName("case_fix") }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "All" }));

    const ids = screen
      .getAllByRole("button", { name: /^case_(reg|swap|fix) / })
      .map((node) => node.textContent?.match(/^case_(reg|swap|fix)/)?.[0]);
    expect(ids).toEqual(["case_reg", "case_swap", "case_fix"]);
  });

  it("selecting a case shows prompt band, both output panes and classifier footers", async () => {
    stubEvidence();
    renderApp([`${EVIDENCE_ROUTE}?caseId=case_reg`]);

    expect(
      await screen.findByText("Cite the source for the 2019 revenue figure."),
    ).toBeInTheDocument();
    expect(screen.getByText("Prompt")).toBeInTheDocument();

    // Baseline / candidate outputs come from the two run details.
    expect(
      await screen.findByText("Baseline answer with the correct citation."),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Candidate hallucinated a fake citation (Smith 2019)."),
    ).toBeInTheDocument();

    // Classifier footers.
    expect(
      screen.getByText("classifier heuristic-v1 · no_failure · conf 0.90"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("classifier heuristic-v1 · hallucination · conf 0.80"),
    ).toBeInTheDocument();
  });

  it("shows the Why it failed block with the candidate explanation for a regressed case", async () => {
    stubEvidence();
    renderApp([`${EVIDENCE_ROUTE}?caseId=case_reg`]);

    expect(await screen.findByText("Why it failed")).toBeInTheDocument();
    expect(
      screen.getByText("Model invented a citation that does not exist."),
    ).toBeInTheDocument();
  });

  it("prev and next buttons walk the visible cases", async () => {
    stubEvidence();
    const user = userEvent.setup();
    renderApp([`${EVIDENCE_ROUTE}?scope=all`]);

    expect(await screen.findByText("case 1 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous case" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Next case" }));
    expect(screen.getByText("case 2 of 3")).toBeInTheDocument();
    expect(
      await screen.findByText("Explain the refund process step by step."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Previous case" }));
    expect(screen.getByText("case 1 of 3")).toBeInTheDocument();
  });

  it("Raw JSON segment shows the JSON view", async () => {
    stubEvidence();
    const user = userEvent.setup();
    renderApp([`${EVIDENCE_ROUTE}?caseId=case_reg`]);
    await screen.findByText("Why it failed");

    await user.click(screen.getByRole("radio", { name: "Raw JSON" }));

    expect(screen.getByText(/"caseDelta"/, { selector: "pre" })).toBeInTheDocument();
    expect(screen.getByText(/"baselineCase"/, { selector: "pre" })).toBeInTheDocument();
  });

  it("Mark for harvest opens the harvest dialog", async () => {
    stubEvidence();
    const user = userEvent.setup();
    renderApp([`${EVIDENCE_ROUTE}?caseId=case_reg`]);
    await screen.findByText("Why it failed");

    await user.click(screen.getByRole("button", { name: "Mark for harvest" }));

    expect(
      screen.getByRole("dialog", { name: "Harvest regressions" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Promote 2 regressed cases")).toBeInTheDocument();
  });
});
