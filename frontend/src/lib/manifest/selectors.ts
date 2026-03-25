import type {
  ArtifactEntity,
  ArtifactIndex,
  MitigationComparisonView,
  OverviewSnapshot,
  ResearchCloseout,
  SeededCohort,
  StabilityPackage,
} from "@/lib/manifest/types";

const PRIMARY_COHORT_ORDER = [
  "logistic_baseline",
  "distilbert_baseline",
  "temperature_scaling",
  "reweighting",
];

const MITIGATION_ORDER: Record<string, number> = {
  temperature_scaling: 0,
  reweighting: 1,
};

function filterDefaultVisible<T extends { default_visible?: boolean }>(
  items: T[],
  includeExploratory = false,
) {
  if (includeExploratory) {
    return items;
  }

  return items.filter((item) => item.default_visible === true);
}

export function getDefaultVisibleEntities(
  index: ArtifactIndex,
  entityType: keyof ArtifactIndex["entities"],
  includeExploratory = false,
): ArtifactEntity[] {
  return filterDefaultVisible(index.entities[entityType], includeExploratory);
}

export function getSeededCohorts(
  index: ArtifactIndex,
  includeExploratory = false,
): SeededCohort[] {
  const order = new Map(PRIMARY_COHORT_ORDER.map((cohortId, idx) => [cohortId, idx]));
  return filterDefaultVisible(index.views.seeded_cohorts, includeExploratory).sort((left, right) => {
    return (
      (order.get(left.cohort_id) ?? Number.MAX_SAFE_INTEGER) -
      (order.get(right.cohort_id) ?? Number.MAX_SAFE_INTEGER)
    );
  });
}

export function getMitigationComparisonViews(
  index: ArtifactIndex,
  includeExploratory = false,
): MitigationComparisonView[] {
  return filterDefaultVisible(index.views.mitigation_comparisons, includeExploratory).sort(
    (left, right) =>
      (MITIGATION_ORDER[left.mitigation_method] ?? Number.MAX_SAFE_INTEGER) -
      (MITIGATION_ORDER[right.mitigation_method] ?? Number.MAX_SAFE_INTEGER),
  );
}

export function getPrimaryStabilityPackage(
  index: ArtifactIndex,
  includeExploratory = false,
): StabilityPackage | null {
  return filterDefaultVisible(index.views.stability_packages, includeExploratory)[0] ?? null;
}

export function getPrimaryResearchCloseout(
  index: ArtifactIndex,
  includeExploratory = false,
): ResearchCloseout | null {
  return filterDefaultVisible(index.views.research_closeout, includeExploratory)[0] ?? null;
}

export function buildOverviewSnapshot(
  index: ArtifactIndex,
  includeExploratory = false,
): OverviewSnapshot {
  const seededCohorts = getSeededCohorts(index, includeExploratory);
  const mitigationViews = getMitigationComparisonViews(index, includeExploratory);
  const closeout = getPrimaryResearchCloseout(index, includeExploratory);
  const stability = getPrimaryStabilityPackage(index, includeExploratory);

  return {
    seededCohorts,
    mitigationLabels: Object.fromEntries(
      mitigationViews.map((view) => [
        view.mitigation_method,
        view.stability_assessment?.label ?? "unknown",
      ]),
    ),
    finalRobustnessVerdict: closeout?.final_robustness_verdict,
    datasetExpansionRecommendation:
      closeout?.dataset_expansion_decision ??
      stability?.milestone_assessment?.dataset_expansion_recommendation,
    recommendationReason:
      closeout?.recommendation_reason ?? stability?.milestone_assessment?.recommendation_reason,
    nextStep: closeout?.next_step ?? stability?.milestone_assessment?.next_step,
    reopenConditions: closeout?.reopen_conditions ?? [],
    summaryBullets: closeout?.summary_bullets ?? [],
    inventoryCounts: {
      runs: getDefaultVisibleEntities(index, "runs", includeExploratory).length,
      evaluations: getDefaultVisibleEntities(index, "evaluations", includeExploratory).length,
      reports: getDefaultVisibleEntities(index, "reports", includeExploratory).length,
    },
    officialMethods: closeout?.official_methods ?? [],
    exploratoryMethods: closeout?.exploratory_methods ?? [],
  };
}
