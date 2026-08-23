import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { REPORT_ID, buildComparisonDetail } from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ComparisonsPage", () => {
  it("renders comparison rows with verdict chip and three-decimal severity", () => {
    renderApp(["/comparisons"]);

    expect(screen.getByText("1 comparison · newest first")).toBeInTheDocument();

    const row = screen.getByText(REPORT_ID).closest("tr")!;
    expect(within(row).getByText("regression")).toBeInTheDocument();
    expect(within(row).getByText("0.420")).toBeInTheDocument();
    expect(within(row).getByText("qa-failures-v1")).toBeInTheDocument();
    // Top driver column.
    expect(within(row).getByText("hallucination")).toBeInTheDocument();
  });

  it("row click navigates to the comparison detail", async () => {
    stubFetch([{ match: "comparison-detail.json", respond: buildComparisonDetail() }]);
    const user = userEvent.setup();
    renderApp(["/comparisons"]);

    await user.click(screen.getByText(REPORT_ID));

    expect(
      await screen.findByText(
        "Candidate raised failure rate 10.0 pts on 10 shared cases.",
      ),
    ).toBeInTheDocument();
  });
});
