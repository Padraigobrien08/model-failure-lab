import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@testing-library/react";

import { App } from "@/app/App";
import type { ArtifactIndex } from "@/lib/manifest/types";

function buildManifestFixture(): ArtifactIndex {
  return {
    schema_version: "artifact_index_v1",
    default_filters: { official_only: true },
    entities: {
      runs: [{ id: "run_official", default_visible: true, is_official: true }],
      evaluations: [{ id: "eval_official", default_visible: true, is_official: true }],
      reports: [{ id: "report_official", default_visible: true, is_official: true }],
    },
    views: {
      seeded_cohorts: [
        {
          cohort_id: "distilbert_baseline",
          display_name: "DistilBERT Baseline",
          cohort_type: "baseline",
          model_name: "distilbert",
          default_visible: true,
          is_official: true,
        },
      ],
      mitigation_comparisons: [
        {
          view_id: "temperature_scaling",
          mitigation_method: "temperature_scaling",
          default_visible: true,
          is_official: true,
          stability_assessment: { label: "stable" },
        },
        {
          view_id: "reweighting",
          mitigation_method: "reweighting",
          default_visible: true,
          is_official: true,
          stability_assessment: { label: "mixed" },
        },
      ],
      stability_packages: [
        {
          view_id: "phase20_stability",
          default_visible: true,
          is_official: true,
          milestone_assessment: {
            dataset_expansion_recommendation: "defer_now_reopen_under_conditions",
          },
        },
      ],
      research_closeout: [
        {
          view_id: "phase27_gate",
          default_visible: true,
          is_official: true,
          final_robustness_verdict: "still_mixed",
          dataset_expansion_decision: "defer_now_reopen_under_conditions",
          summary_bullets: ["Calibration is stable.", "Robustness remains mixed."],
          recommendation_reason: "Reweighting is still mixed.",
          official_methods: ["temperature_scaling", "reweighting"],
          exploratory_methods: ["group_dro", "group_balanced_sampling"],
          reopen_conditions: ["Stable robustness gains across seeds."],
        },
      ],
    },
  };
}

describe("App shell", () => {
  it("renders the locked top-level navigation and defaults to overview", () => {
    render(<App useMemoryRouter initialIndex={buildManifestFixture()} />);

    const primaryNavigation = screen.getByRole("navigation", { name: /Primary/i });

    expect(screen.getByRole("heading", { name: /Failure Debugger/i })).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Overview Final verdicts and official evidence launchpad/i,
      }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Comparisons Method-to-method debugging/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Failure Explorer Subgroup, ID\/OOD, and calibration entrypoints/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Runs Run-level lineage and seed context/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(primaryNavigation).getByRole("link", {
        name: /Evidence Raw reports, eval bundles, and metadata paths/i,
      }),
    ).toBeInTheDocument();
  });

  it("makes exploratory scope explicit when toggled on", async () => {
    const user = userEvent.setup();
    render(<App useMemoryRouter initialIndex={buildManifestFixture()} />);

    await user.click(screen.getByRole("button", { name: /Show exploratory evidence/i }));

    expect(screen.getByText(/Exploratory Evidence On/i)).toBeInTheDocument();
    expect(screen.getByText(/exploratory scope active/i)).toBeInTheDocument();
  });
});
