/**
 * One gate state, three surfaces, one answer.
 *
 * Two bugs lived in the gap between these surfaces, and neither was catchable by a test
 * that only rendered one screen:
 *
 *  - The rail chip painted every block red, so a fail-closed "runs are not comparable"
 *    showed a red FAIL badge in the rail and an amber banner on the page beside it --
 *    two colors for one state, on screen simultaneously.
 *  - The comparison detail short-circuited an `incompatible` verdict to "not evaluated"
 *    before reading its gate row, so the comparison that was the *sole reason* the gate
 *    failed reported, on its own page, that the gate had not been evaluated on it.
 *
 * These tests assert agreement across surfaces rather than correctness of one, because
 * disagreement is the defect.
 */

import { screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { REPORT_ID, buildComparisonDetail, buildGateState } from "@/test/factories";
import { renderApp, stubFetch } from "@/test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

/** The rail chip: the one gate surface visible on every screen. */
function railGateChip(): HTMLElement {
  const nav = screen.getByRole("navigation", { name: "Primary" });
  const link = within(nav).getByRole("link", { name: /^Gate/ });
  const chip = link.querySelector("span");
  if (!chip) {
    throw new Error("rail gate link has no status chip");
  }
  return chip as HTMLElement;
}

describe("gate agreement across surfaces", () => {
  it("a fail-closed block is amber in the rail, not red", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("fail-closed") });

    const chip = railGateChip();
    expect(chip).toHaveTextContent("FAIL");
    // DESIGN.md: red means regression, only regression. This block has none.
    expect(chip.className).toContain("text-warn");
    expect(chip.className).not.toContain("text-bad");
  });

  it("a regression block is red in the rail", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("blocked") });

    const chip = railGateChip();
    expect(chip).toHaveTextContent("FAIL");
    expect(chip.className).toContain("text-bad");
  });

  it("a clear gate is green in the rail", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("clear") });

    const chip = railGateChip();
    expect(chip).toHaveTextContent("PASS");
    expect(chip.className).toContain("text-good");
  });

  it("the rail chip and the gate banner never disagree", () => {
    for (const variant of ["blocked", "fail-closed", "clear"] as const) {
      const view = renderApp(["/gate"], { initialGateState: buildGateState(variant) });
      const chipClass = railGateChip().className;
      const bannerLabel = variant === "clear" ? "PASS" : "FAIL";
      expect(railGateChip()).toHaveTextContent(bannerLabel);

      // The banner headline carries the same tone token as the chip.
      const headline = screen.getByText(
        variant === "clear" ? /All recent comparisons pass/ : /blocks the gate\.$/,
      );
      const bannerTone = variant === "clear" ? "good" : variant === "blocked" ? "bad" : "warn";
      expect(chipClass, `rail chip for ${variant}`).toContain(
        bannerTone === "bad" ? "text-bad" : `text-${bannerTone}`,
      );
      expect(headline.className, `banner for ${variant}`).toContain(
        bannerTone === "bad" ? "text-bad-head" : `text-${bannerTone}`,
      );
      view.unmount();
    }
  });

  it("the gate remedy names the waiver file the engine actually discovers", () => {
    renderApp(["/gate"], { initialGateState: buildGateState("fail-closed") });

    // `--waivers waivers.yml` resolved to nothing; DEFAULT_WAIVER_FILENAMES is
    // governance/waivers.yml.
    expect(screen.getByText(/governance\/waivers\.yml/)).toBeInTheDocument();
    expect(screen.queryByText(/--waivers waivers\.yml/)).not.toBeInTheDocument();
  });

  it("an incompatible comparison reports the gate decision that blocks CI, not 'not evaluated'", async () => {
    stubFetch([
      {
        match: "comparison-detail.json",
        respond: buildComparisonDetail({
          signal: {
            verdict: "incompatible",
            reason: "dataset_mismatch",
            regressionScore: 0,
            improvementScore: 0,
            netScore: 0,
            severity: 0,
            topDrivers: [],
          },
          comparison: { compatible: false, reason: "dataset_mismatch" },
        }),
      },
    ]);
    renderApp([`/comparisons/${REPORT_ID}`], {
      initialGateState: buildGateState("fail-closed"),
    });

    // The gate row exists and blocks, so the tile must say so.
    expect(await screen.findByText("FAIL")).toBeInTheDocument();
    expect(screen.getByText("blocked")).toBeInTheDocument();
    expect(screen.getByText(/runs are not comparable/)).toBeInTheDocument();
    // ...and must not claim the gate skipped it.
    expect(screen.queryByText(/not evaluated/)).not.toBeInTheDocument();
  });

  it("an incompatible comparison the gate has not seen still says 'not evaluated'", async () => {
    stubFetch([
      {
        match: "comparison-detail.json",
        respond: buildComparisonDetail({
          signal: {
            verdict: "incompatible",
            reason: "dataset_mismatch",
            regressionScore: 0,
            improvementScore: 0,
            netScore: 0,
            severity: 0,
            topDrivers: [],
          },
          comparison: { compatible: false, reason: "dataset_mismatch" },
        }),
      },
    ]);
    // A gate whose window contains a different comparison entirely.
    renderApp([`/comparisons/${REPORT_ID}`], {
      initialGateState: buildGateState("fail-closed", [{ comparisonId: "cmp_other_999" }]),
    });

    expect(await screen.findByText(/not evaluated/)).toBeInTheDocument();
    expect(screen.getByText(/signal discarded/)).toBeInTheDocument();
  });
});
