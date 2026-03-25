import type {
  ArtifactEntity,
  ArtifactIndex,
  ComparisonCardModel,
  EvidenceAction,
  FailureDomainKey,
  FailureDomainModel,
  FailureDomainSummaryItem,
  FinalRobustnessBundle,
  FinalRobustnessMethodSummary,
  MitigationComparisonView,
  OverviewSnapshot,
  ReportEntity,
  SeedBreakdownRow,
  ResearchCloseout,
  SeededCohort,
  StabilityPackage,
} from "@/lib/manifest/types";
import { artifactPathToPublicUrl } from "@/lib/manifest/load";

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

const METHOD_ORDER: Record<string, number> = {
  temperature_scaling: 0,
  reweighting: 1,
  distilbert_baseline: 2,
  group_balanced_sampling: 3,
  group_dro: 4,
};

const FAILURE_DOMAIN_CONFIG: Record<
  FailureDomainKey,
  { label: string; description: string; tableRefKey: string }
> = {
  worst_group: {
    label: "Worst Group",
    description: "Where the subgroup floor moves, not just the average lane.",
    tableRefKey: "worst_group_summary_csv",
  },
  ood: {
    label: "OOD",
    description: "Out-of-distribution macro F1 under saved shift evaluation.",
    tableRefKey: "ood_summary_csv",
  },
  id: {
    label: "ID",
    description: "In-distribution tradeoffs that guard against brittle robustness wins.",
    tableRefKey: "id_summary_csv",
  },
  calibration: {
    label: "Calibration",
    description: "ECE and Brier changes that explain whether reliability improved or regressed.",
    tableRefKey: "calibration_summary_csv",
  },
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

export function getReportEntities(index: ArtifactIndex, includeExploratory = false): ReportEntity[] {
  return getDefaultVisibleEntities(index, "reports", includeExploratory) as ReportEntity[];
}

export function getReportEntityByScope(
  index: ArtifactIndex,
  scope: string,
  includeExploratory = true,
): ReportEntity | null {
  return (
    getReportEntities(index, includeExploratory).find((report) => report.report_scope === scope) ??
    null
  );
}

function getReportEntityById(index: ArtifactIndex, reportId: string | null | undefined): ReportEntity | null {
  if (!reportId) {
    return null;
  }

  return (index.entities.reports as ReportEntity[]).find((report) => report.id === reportId) ?? null;
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

function getMethodOrder(methodName: string) {
  return METHOD_ORDER[methodName] ?? Number.MAX_SAFE_INTEGER;
}

function getSeededCohortByMethod(index: ArtifactIndex, methodName: string) {
  return (
    index.views.seeded_cohorts.find((cohort) =>
      methodName === "distilbert_baseline"
        ? cohort.cohort_id === "distilbert_baseline"
        : cohort.mitigation_method === methodName,
    ) ?? null
  );
}

function getMitigationComparisonByMethod(index: ArtifactIndex, methodName: string) {
  return (
    index.views.mitigation_comparisons.find(
      (view) => view.mitigation_method === methodName,
    ) ?? null
  );
}

function toEvidenceAction(
  refMap: ReportEntity["artifact_refs"] | undefined,
  key: string,
  label: string,
): EvidenceAction | null {
  const ref = refMap?.[key];
  if (!ref?.path || ref.exists === false) {
    return null;
  }

  return {
    label,
    path: artifactPathToPublicUrl(ref.path),
  };
}

function buildDefaultReportActions(report: ReportEntity | null): EvidenceAction[] {
  if (!report) {
    return [];
  }

  return [
    toEvidenceAction(report.artifact_refs, "report_markdown", "View report"),
    toEvidenceAction(report.artifact_refs, "report_data_json", "Open report payload"),
    toEvidenceAction(report.artifact_refs, "comparison_table_csv", "View raw metrics table"),
    toEvidenceAction(report.artifact_refs, "mitigation_comparison_table_csv", "View raw metrics table"),
    toEvidenceAction(report.artifact_refs, "worst_group_summary_csv", "View raw metrics table"),
  ].filter((action): action is EvidenceAction => action !== null);
}

function sortMethodSummaries<T extends { method_name: string }>(items: T[]) {
  return [...items].sort(
    (left, right) => getMethodOrder(left.method_name) - getMethodOrder(right.method_name),
  );
}

function buildSeedBreakdown(index: ArtifactIndex, methodName: string): SeedBreakdownRow[] {
  const seededCohort = getSeededCohortByMethod(index, methodName);
  const comparisonView = getMitigationComparisonByMethod(index, methodName);
  const comparisonBySeed = new Map(
    (comparisonView?.per_seed_comparisons ?? []).map((entry) => [String(entry.seed ?? ""), entry]),
  );

  if (!seededCohort) {
    return [];
  }

  return [...(seededCohort.per_seed_metrics ?? [])]
    .map((entry) => {
      const seed = String(entry.seed ?? "");
      const comparison = comparisonBySeed.get(seed);
      const deltas = (comparison?.deltas ?? {}) as Record<string, number | null | undefined>;

      return {
        seed,
        runId: String(entry.run_id ?? comparison?.child_run_id ?? ""),
        evalId: String(entry.eval_id ?? comparison?.child_eval_id ?? ""),
        verdict: typeof comparison?.verdict === "string" ? comparison.verdict : undefined,
        metrics: {
          worst_group_f1: entry.worst_group_f1 as number | null | undefined,
          ood_macro_f1: entry.ood_macro_f1 as number | null | undefined,
          id_macro_f1: entry.id_macro_f1 as number | null | undefined,
          ece: entry.ece as number | null | undefined,
          brier_score: entry.brier_score as number | null | undefined,
        },
        deltas: {
          worst_group_f1: deltas.worst_group_f1_delta,
          ood_macro_f1: deltas.ood_macro_f1_delta,
          id_macro_f1: deltas.id_macro_f1_delta,
          ece: deltas.ece_delta,
          brier_score: deltas.brier_score_delta,
        },
      };
    })
    .sort((left, right) => Number(left.seed) - Number(right.seed));
}

export function buildComparisonCards(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle,
  includeExploratory = false,
): ComparisonCardModel[] {
  const methodSummaries = sortMethodSummaries([
    ...bundle.summary.official_methods,
    ...(includeExploratory ? bundle.summary.exploratory_methods : []),
  ]);
  const finalReport = bundle.report;

  return methodSummaries.map((summary) => {
    const mitigationView = getMitigationComparisonByMethod(index, summary.method_name);
    const supportReport =
      getReportEntityById(index, mitigationView?.aggregate_report_id) ?? finalReport;

    return {
      methodName: summary.method_name,
      displayName: summary.display_name,
      verdict: summary.primary_verdict ?? summary.stability_label ?? "unknown",
      comparisonMode: summary.comparison_mode,
      storyNote: summary.story_note,
      seedCount: summary.seed_count ?? 0,
      seededInterpretation: summary.seeded_interpretation,
      isExploratory: summary.is_exploratory,
      metrics: {
        worstGroup: {
          label: "Worst Group",
          value: summary.metrics.mean.worst_group_f1,
          std: summary.metrics.std.worst_group_f1,
          comparisonMode: summary.comparison_mode,
        },
        ood: {
          label: "OOD",
          value: summary.metrics.mean.ood_macro_f1,
          std: summary.metrics.std.ood_macro_f1,
          comparisonMode: summary.comparison_mode,
        },
        id: {
          label: "ID",
          value: summary.metrics.mean.id_macro_f1,
          std: summary.metrics.std.id_macro_f1,
          comparisonMode: summary.comparison_mode,
        },
        ece: {
          label: "ECE",
          value: summary.metrics.mean.ece,
          std: summary.metrics.std.ece,
          comparisonMode: summary.comparison_mode,
          invertPolarity: true,
        },
        brier: {
          label: "Brier",
          value: summary.metrics.mean.brier_score,
          std: summary.metrics.std.brier_score,
          comparisonMode: summary.comparison_mode,
          invertPolarity: true,
        },
      },
      seedBreakdown: buildSeedBreakdown(index, summary.method_name),
      actions: buildDefaultReportActions(supportReport),
    };
  });
}

function getFailureDomainSource(
  bundle: FinalRobustnessBundle,
  domain: FailureDomainKey,
): FailureDomainSummaryItem[] {
  switch (domain) {
    case "worst_group":
      return bundle.data.worst_group_summary;
    case "ood":
      return bundle.data.ood_summary;
    case "id":
      return bundle.data.id_summary;
    case "calibration":
      return bundle.data.calibration_summary;
  }
}

export function buildFailureDomainModels(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle,
  includeExploratory = false,
): FailureDomainModel[] {
  return (Object.keys(FAILURE_DOMAIN_CONFIG) as FailureDomainKey[]).map((domain) => {
    const config = FAILURE_DOMAIN_CONFIG[domain];
    const items = getFailureDomainSource(bundle, domain)
      .filter((entry) => includeExploratory || entry.is_exploratory !== true)
      .sort((left, right) => getMethodOrder(left.method_name) - getMethodOrder(right.method_name))
      .map((entry) => ({
        methodName: entry.method_name,
        displayName: entry.display_name,
        verdict: entry.primary_verdict ?? entry.stability_label ?? "unknown",
        comparisonMode: entry.comparison_mode,
        isExploratory: entry.is_exploratory,
        storyNote: entry.story_note,
        seedCount: entry.seed_count ?? 0,
        mean: entry.mean,
        std: entry.std,
        eceMean: entry.ece_mean,
        eceStd: entry.ece_std,
        brierMean: entry.brier_score_mean,
        brierStd: entry.brier_score_std,
        seedBreakdown: buildSeedBreakdown(index, entry.method_name),
      }));

    return {
      domain,
      label: config.label,
      description: config.description,
      actions: [
        toEvidenceAction(bundle.report.artifact_refs, "report_markdown", "View supporting report"),
        toEvidenceAction(bundle.report.artifact_refs, "report_data_json", "Open eval bundle"),
        toEvidenceAction(bundle.report.artifact_refs, config.tableRefKey, "View raw metrics table"),
      ].filter((action): action is EvidenceAction => action !== null),
      items,
    };
  });
}
