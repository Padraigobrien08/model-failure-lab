import { render, screen } from "@testing-library/react";

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
          aggregate_metrics: {
            mean: {
              id_macro_f1: 0.842,
              worst_group_f1: 0.421,
            },
          },
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
            recommendation_reason: "Robustness remains mixed.",
            next_step: "Hold benchmark expansion until mitigation quality improves.",
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
          recommendation_reason:
            "Calibration is solved more cleanly than robustness, so the gate stays closed.",
          official_methods: ["temperature_scaling", "reweighting"],
          exploratory_methods: ["group_dro", "group_balanced_sampling"],
          summary_bullets: [
            "The baseline robustness gap remains real and stable.",
            "Temperature scaling remains the stable calibration lane.",
          ],
          reopen_conditions: [
            "Robustness lane achieves stable improvement instead of remaining mixed.",
          ],
        },
      ],
    },
  };
}

describe("Overview route", () => {
  it("renders final verdicts and the primary CTA from manifest data", () => {
    render(<App useMemoryRouter initialIndex={buildManifestFixture()} />);

    expect(
      screen.getByRole("heading", {
        name: /Final evidence, turned into an explorable debugging surface/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Still Mixed/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Defer Now Reopen Under Conditions/i)).toHaveLength(2);
    expect(screen.getByRole("link", { name: /Inspect Failure Traces/i })).toHaveAttribute(
      "href",
      "/comparisons",
    );
    expect(screen.getByText(/Temperature scaling remains the stable calibration lane/i)).toBeInTheDocument();
  });
});
