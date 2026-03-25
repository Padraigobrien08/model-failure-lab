import {
  ARTIFACT_INDEX_SCHEMA_VERSION,
  validateArtifactIndex,
} from "@/lib/manifest/load";
import {
  buildOverviewSnapshot,
  getDefaultVisibleEntities,
  getMitigationComparisonViews,
  getSeededCohorts,
} from "@/lib/manifest/selectors";
import type { ArtifactIndex } from "@/lib/manifest/types";

function buildManifestFixture(): ArtifactIndex {
  return {
    schema_version: ARTIFACT_INDEX_SCHEMA_VERSION,
    default_filters: { official_only: true },
    entities: {
      runs: [
        { id: "run_official", default_visible: true, is_official: true },
        { id: "run_exploratory", default_visible: false, is_official: false },
      ],
      evaluations: [{ id: "eval_official", default_visible: true, is_official: true }],
      reports: [
        { id: "phase26_report", default_visible: true, is_official: true },
        { id: "phase23_scout_report", default_visible: false, is_official: false },
      ],
    },
    views: {
      seeded_cohorts: [
        {
          cohort_id: "reweighting",
          display_name: "Reweighting",
          cohort_type: "mitigation",
          model_name: "distilbert",
          mitigation_method: "reweighting",
          default_visible: true,
          is_official: true,
        },
        {
          cohort_id: "temperature_scaling",
          display_name: "Temperature Scaling",
          cohort_type: "mitigation",
          model_name: "distilbert",
          mitigation_method: "temperature_scaling",
          default_visible: true,
          is_official: true,
        },
        {
          cohort_id: "distilbert_baseline",
          display_name: "DistilBERT Baseline",
          cohort_type: "baseline",
          model_name: "distilbert",
          default_visible: true,
          is_official: true,
        },
        {
          cohort_id: "logistic_baseline",
          display_name: "Logistic TF-IDF Baseline",
          cohort_type: "baseline",
          model_name: "logistic_tfidf",
          default_visible: true,
          is_official: true,
        },
      ],
      mitigation_comparisons: [
        {
          view_id: "reweighting_view",
          mitigation_method: "reweighting",
          default_visible: true,
          is_official: true,
          stability_assessment: { label: "mixed" },
        },
        {
          view_id: "temperature_scaling_view",
          mitigation_method: "temperature_scaling",
          default_visible: true,
          is_official: true,
          stability_assessment: { label: "stable" },
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
          reopen_conditions: ["Stable robustness gains across seeds."],
          official_methods: ["temperature_scaling", "reweighting"],
          exploratory_methods: ["group_dro", "group_balanced_sampling"],
        },
      ],
    },
  };
}

describe("artifact index contract", () => {
  it("accepts the current schema version", () => {
    const manifest = buildManifestFixture();

    expect(validateArtifactIndex(manifest).schema_version).toBe(ARTIFACT_INDEX_SCHEMA_VERSION);
  });

  it("rejects an unknown schema version", () => {
    const manifest = {
      ...buildManifestFixture(),
      schema_version: "artifact_index_v2",
    };

    expect(() => validateArtifactIndex(manifest)).toThrow("Unsupported artifact index schema");
  });

  it("keeps official/default-visible ordering and filtering stable", () => {
    const manifest = buildManifestFixture();

    expect(getDefaultVisibleEntities(manifest, "runs").map((item) => item.id)).toEqual([
      "run_official",
    ]);
    expect(getSeededCohorts(manifest).map((item) => item.cohort_id)).toEqual([
      "logistic_baseline",
      "distilbert_baseline",
      "temperature_scaling",
      "reweighting",
    ]);
    expect(getMitigationComparisonViews(manifest).map((item) => item.mitigation_method)).toEqual(
      ["temperature_scaling", "reweighting"],
    );
  });

  it("builds the overview snapshot from closeout and official counts", () => {
    const manifest = buildManifestFixture();
    const snapshot = buildOverviewSnapshot(manifest);

    expect(snapshot.finalRobustnessVerdict).toBe("still_mixed");
    expect(snapshot.datasetExpansionRecommendation).toBe("defer_now_reopen_under_conditions");
    expect(snapshot.mitigationLabels.temperature_scaling).toBe("stable");
    expect(snapshot.mitigationLabels.reweighting).toBe("mixed");
    expect(snapshot.inventoryCounts.reports).toBe(1);
    expect(snapshot.summaryBullets).toContain("Calibration is stable.");
  });
});
