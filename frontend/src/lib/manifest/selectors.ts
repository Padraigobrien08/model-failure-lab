import type {
  AggregateMetrics,
  ArtifactEntity,
  ArtifactIndex,
  ArtifactRef,
  ArtifactRefMap,
  ComparisonCardModel,
  EvaluationEntity,
  EvidenceAction,
  EvidenceActionGroup,
  EvidenceDrawerModel,
  EvidenceEntityCardModel,
  EvidenceScope,
  EvidenceSectionModel,
  FailureDomainKey,
  FailureDomainModel,
  FailureDomainSummaryItem,
  FinalRobustnessBundle,
  FinalRobustnessMethodSummary,
  MitigationComparisonView,
  OverviewSnapshot,
  ReportEntity,
  ResearchCloseout,
  VerdictLaneModel,
  VerdictWorkspaceModel,
  RunCardModel,
  RunDetailMetricModel,
  RunDetailModel,
  RunEntity,
  RunLaneModel,
  SeedBreakdownRow,
  SeededCohort,
  StabilityPackage,
} from "@/lib/manifest/types";
import { artifactPathToPublicUrl } from "@/lib/manifest/load";
import { formatLabel, formatMetric, formatSignedMetric } from "@/lib/formatters";

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
  logistic_tfidf_baseline: 3,
  group_balanced_sampling: 4,
  group_dro: 5,
};

const LANE_ORDER: Record<string, number> = {
  baseline: 0,
  temperature_scaling: 1,
  reweighting: 2,
  exploratory: 3,
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

function isArtifactRef(value: unknown): value is ArtifactRef {
  return (
    typeof value === "object" &&
    value !== null &&
    "path" in value &&
    typeof (value as ArtifactRef).path === "string"
  );
}

function flattenArtifactRefs(
  refMap: ArtifactRefMap | undefined,
  prefix = "",
): Array<{ key: string; ref: ArtifactRef }> {
  if (!refMap) {
    return [];
  }

  const entries: Array<{ key: string; ref: ArtifactRef }> = [];

  for (const [key, value] of Object.entries(refMap)) {
    const nextKey = prefix ? `${prefix}.${key}` : key;

    if (isArtifactRef(value)) {
      entries.push({ key: nextKey, ref: value });
      continue;
    }

    if (value && typeof value === "object") {
      entries.push(...flattenArtifactRefs(value as ArtifactRefMap, nextKey));
    }
  }

  return entries;
}

function findArtifactRef(refMap: ArtifactRefMap | undefined, key: string): ArtifactRef | null {
  for (const candidate of flattenArtifactRefs(refMap)) {
    if (candidate.key === key || candidate.key.endsWith(`.${key}`)) {
      return candidate.ref;
    }
  }

  return null;
}

function toEvidenceAction(
  refMap: ArtifactRefMap | undefined,
  key: string,
  label: string,
): EvidenceAction | null {
  const ref = findArtifactRef(refMap, key);
  if (!ref?.path || ref.exists === false) {
    return null;
  }

  return {
    label,
    path: artifactPathToPublicUrl(ref.path),
  };
}

function toPathAction(path: string | null | undefined, label: string): EvidenceAction | null {
  if (!path) {
    return null;
  }

  return {
    label,
    path: artifactPathToPublicUrl(path),
  };
}

function uniqueActions(actions: Array<EvidenceAction | null>): EvidenceAction[] {
  const seen = new Set<string>();
  const result: EvidenceAction[] = [];

  for (const action of actions) {
    if (!action) {
      continue;
    }

    const key = `${action.label}:${action.path}`;
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    result.push(action);
  }

  return result;
}

export function getDefaultVisibleEntities(
  index: ArtifactIndex,
  entityType: keyof ArtifactIndex["entities"],
  includeExploratory = false,
): ArtifactEntity[] {
  return filterDefaultVisible(index.entities[entityType], includeExploratory);
}

export function getRunEntities(index: ArtifactIndex, includeExploratory = false): RunEntity[] {
  return getDefaultVisibleEntities(index, "runs", includeExploratory) as RunEntity[];
}

export function getEvaluationEntities(
  index: ArtifactIndex,
  includeExploratory = false,
): EvaluationEntity[] {
  return getDefaultVisibleEntities(index, "evaluations", includeExploratory) as EvaluationEntity[];
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

export function getMethodLaneKey(methodName: string) {
  return methodName === "temperature_scaling" ? "calibration" : "robustness";
}

function getMethodOrder(methodName: string) {
  return METHOD_ORDER[methodName] ?? Number.MAX_SAFE_INTEGER;
}

function getRunMethodName(run: RunEntity): string {
  if (run.mitigation_method) {
    return run.mitigation_method;
  }

  if (run.experiment_type === "baseline" && run.model_name) {
    return `${run.model_name}_baseline`;
  }

  return run.model_name ?? run.run_id;
}

function getRunDisplayName(run: RunEntity): string {
  if (run.experiment_type === "baseline") {
    if (run.model_name === "distilbert") {
      return "DistilBERT Baseline";
    }

    if (run.model_name === "logistic_tfidf") {
      return "Logistic TF-IDF Baseline";
    }
  }

  if (run.mitigation_method) {
    return formatLabel(run.mitigation_method);
  }

  return formatLabel(getRunMethodName(run));
}

function getRunLane(run: RunEntity) {
  if (run.experiment_type === "baseline") {
    return {
      laneKey: "baseline",
      laneLabel: "Baseline",
      description: "Reference runs grouped by seed and model family.",
      isExploratoryLane: false,
    };
  }

  if (run.mitigation_method === "temperature_scaling") {
    return {
      laneKey: "temperature_scaling",
      laneLabel: "Temperature Scaling",
      description: "Stable calibration lane with reference-level robustness.",
      isExploratoryLane: false,
    };
  }

  if (run.mitigation_method === "reweighting") {
    return {
      laneKey: "reweighting",
      laneLabel: "Reweighting",
      description: "Best current robustness lane, still mixed in the official package.",
      isExploratoryLane: false,
    };
  }

  return {
    laneKey: "exploratory",
    laneLabel: "Exploratory",
    description: "Rejected scout lanes kept explicit but outside the default official story.",
    isExploratoryLane: true,
  };
}

function getSeedLabel(seed: string | number | null | undefined) {
  return seed === null || seed === undefined || seed === "" ? "Unseeded" : `Seed ${String(seed)}`;
}

function getSeedSortValue(seed: string | number | null | undefined) {
  const normalized =
    typeof seed === "string" && seed.startsWith("Seed ") ? seed.slice(5) : seed;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : Number.MAX_SAFE_INTEGER;
}

function buildMethodSummaryLookup(bundle: FinalRobustnessBundle | null) {
  const lookup = new Map<string, FinalRobustnessMethodSummary>();

  for (const summary of [
    ...(bundle?.summary.official_methods ?? []),
    ...(bundle?.summary.exploratory_methods ?? []),
  ]) {
    lookup.set(summary.method_name, summary);
  }

  return lookup;
}

function getSeededCohortByMethod(index: ArtifactIndex, methodName: string) {
  return (
    index.views.seeded_cohorts.find((cohort) =>
      methodName === "distilbert_baseline"
        ? cohort.cohort_id === "distilbert_baseline"
        : methodName === "logistic_tfidf_baseline"
          ? cohort.cohort_id === "logistic_baseline"
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

function buildDefaultReportActions(report: ReportEntity | null): EvidenceAction[] {
  if (!report) {
    return [];
  }

  return uniqueActions([
    toEvidenceAction(report.artifact_refs, "report_markdown", "View report"),
    toEvidenceAction(report.payload_refs ?? report.artifact_refs, "report_data_json", "Open report payload"),
    toEvidenceAction(report.artifact_refs, "comparison_table_csv", "View raw metrics table"),
    toEvidenceAction(report.artifact_refs, "mitigation_comparison_table_csv", "View raw metrics table"),
    toEvidenceAction(report.artifact_refs, "worst_group_summary_csv", "View raw metrics table"),
  ]);
}

function sortMethodSummaries<T extends { method_name: string }>(items: T[]) {
  return [...items].sort(
    (left, right) => getMethodOrder(left.method_name) - getMethodOrder(right.method_name),
  );
}

function findSeededMetricEntry(index: ArtifactIndex, runId: string) {
  for (const cohort of index.views.seeded_cohorts) {
    for (const entry of cohort.per_seed_metrics ?? []) {
      if (String(entry.run_id ?? "") === runId) {
        return entry as Record<string, unknown>;
      }
    }
  }

  return null;
}

function findPerSeedComparison(index: ArtifactIndex, methodName: string, seed: string | null | undefined) {
  const comparisonView = getMitigationComparisonByMethod(index, methodName);
  if (!comparisonView) {
    return null;
  }

  return (
    comparisonView.per_seed_comparisons?.find((entry) => String(entry.seed ?? "") === String(seed ?? "")) ??
    null
  );
}

function sortEntitiesByPriority<T extends { default_visible?: boolean; is_official?: boolean; id: string }>(
  items: T[],
) {
  return [...items].sort((left, right) => {
    if ((left.default_visible ?? false) !== (right.default_visible ?? false)) {
      return Number(right.default_visible ?? false) - Number(left.default_visible ?? false);
    }

    if ((left.is_official ?? false) !== (right.is_official ?? false)) {
      return Number(right.is_official ?? false) - Number(left.is_official ?? false);
    }

    return right.id.localeCompare(left.id);
  });
}

function getPrimaryEvaluationForRun(index: ArtifactIndex, runId: string) {
  const evaluations = (index.entities.evaluations as EvaluationEntity[]).filter(
    (evaluation) => evaluation.source_run_id === runId,
  );

  return sortEntitiesByPriority(evaluations)[0] ?? null;
}

function findSeedScopedReport(index: ArtifactIndex, methodToken: string, seedLabel: string) {
  return (
    (index.entities.reports as ReportEntity[]).find((report) => {
      const scope = report.report_scope ?? "";
      return scope.includes(methodToken) && scope.includes(`seed_${seedLabel}`);
    }) ?? null
  );
}

function findScoutReport(index: ArtifactIndex, methodToken: string) {
  return (
    (index.entities.reports as ReportEntity[]).find((report) => {
      const scope = report.report_scope ?? "";
      return scope.includes(methodToken) && scope.includes("scout");
    }) ?? null
  );
}

function getSupportReportForRun(
  index: ArtifactIndex,
  run: RunEntity,
  bundle: FinalRobustnessBundle | null,
) {
  const methodName = getRunMethodName(run);

  if (run.mitigation_method && run.seed !== null && run.seed !== undefined) {
    const seedScoped = findSeedScopedReport(index, run.mitigation_method, String(run.seed));
    if (seedScoped) {
      return seedScoped;
    }
  }

  if (run.mitigation_method) {
    const scoutReport = findScoutReport(index, run.mitigation_method);
    if (scoutReport) {
      return scoutReport;
    }
  }

  const mitigationView = getMitigationComparisonByMethod(index, methodName);
  const aggregateReport = getReportEntityById(index, mitigationView?.aggregate_report_id);
  if (aggregateReport) {
    return aggregateReport;
  }

  const cohortReport = getReportEntityById(index, getSeededCohortByMethod(index, methodName)?.linked_report_id);
  if (cohortReport) {
    return cohortReport;
  }

  return bundle?.report ?? getReportEntityByScope(index, "phase26_robustness_final", true);
}

function buildSeedBreakdown(index: ArtifactIndex, methodName: string): SeedBreakdownRow[] {
  const seededCohort = getSeededCohortByMethod(index, methodName);
  const comparisonView = getMitigationComparisonByMethod(index, methodName);
  const comparisonBySeed = new Map(
    (comparisonView?.per_seed_comparisons ?? []).map((entry) => [String(entry.seed ?? ""), entry]),
  );

  if (seededCohort) {
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
      .sort((left, right) => getSeedSortValue(left.seed) - getSeedSortValue(right.seed));
  }

  return sortEntitiesByPriority(index.entities.runs as RunEntity[])
    .filter((run) => getRunMethodName(run) === methodName)
    .map((run) => {
      const evaluation = getPrimaryEvaluationForRun(index, run.run_id);

      return {
        seed: String(run.seed ?? ""),
        runId: run.run_id,
        evalId: evaluation?.eval_id,
        verdict: run.status ?? undefined,
        metrics: {
          worst_group_f1: evaluation?.headline_metrics?.worst_group_f1,
          ood_macro_f1: null,
          id_macro_f1: evaluation?.headline_metrics?.macro_f1,
          ece: null,
          brier_score: null,
        },
        deltas: {},
      };
    })
    .sort((left, right) => getSeedSortValue(left.seed) - getSeedSortValue(right.seed));
}

export function getRepresentativeRunIdForMethod(
  index: ArtifactIndex,
  methodName: string,
  includeExploratory = false,
) {
  const runs = getRunEntities(index, includeExploratory)
    .filter((run) => getRunMethodName(run) === methodName)
    .sort((left, right) => {
      if ((left.default_visible ?? false) !== (right.default_visible ?? false)) {
        return Number(right.default_visible ?? false) - Number(left.default_visible ?? false);
      }

      if ((left.is_official ?? false) !== (right.is_official ?? false)) {
        return Number(right.is_official ?? false) - Number(left.is_official ?? false);
      }

      return getSeedSortValue(left.seed) - getSeedSortValue(right.seed);
    });

  return runs[0]?.run_id ?? null;
}

function buildRunCardModel(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  run: RunEntity,
): RunCardModel {
  const methodName = getRunMethodName(run);
  const lane = getRunLane(run);
  const methodSummary = buildMethodSummaryLookup(bundle).get(methodName);
  const perSeedComparison = findPerSeedComparison(index, methodName, String(run.seed ?? ""));
  const verdict =
    (typeof perSeedComparison?.verdict === "string" ? perSeedComparison.verdict : null) ??
    methodSummary?.primary_verdict ??
    methodSummary?.stability_label ??
    run.status ??
    "unknown";

  return {
    runId: run.run_id,
    displayName: getRunDisplayName(run),
    methodName,
    laneKey: lane.laneKey,
    laneLabel: lane.laneLabel,
    seedLabel: getSeedLabel(run.seed),
    verdict,
    summaryLabel: methodSummary?.story_note ?? run.notes ?? "Saved run ready for drillthrough.",
    isOfficial: run.is_official === true,
    isExploratory: run.is_official !== true,
    timestamp: run.timestamp ?? null,
  };
}

function buildRunMetricModels(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  run: RunEntity,
): RunDetailMetricModel[] {
  const methodName = getRunMethodName(run);
  const methodSummary = buildMethodSummaryLookup(bundle).get(methodName);
  const perSeedMetrics = findSeededMetricEntry(index, run.run_id);
  const perSeedComparison = findPerSeedComparison(index, methodName, String(run.seed ?? ""));
  const evaluation = getPrimaryEvaluationForRun(index, run.run_id);

  const worstGroup = (perSeedMetrics?.worst_group_f1 as number | null | undefined) ??
    (evaluation?.headline_metrics?.worst_group_f1 as number | null | undefined) ??
    methodSummary?.metrics.mean.worst_group_f1;
  const ood = (perSeedMetrics?.ood_macro_f1 as number | null | undefined) ??
    methodSummary?.metrics.mean.ood_macro_f1;
  const id = (perSeedMetrics?.id_macro_f1 as number | null | undefined) ??
    (evaluation?.headline_metrics?.macro_f1 as number | null | undefined) ??
    methodSummary?.metrics.mean.id_macro_f1;
  const ece = (perSeedMetrics?.ece as number | null | undefined) ?? methodSummary?.metrics.mean.ece;
  const brier =
    (perSeedMetrics?.brier_score as number | null | undefined) ?? methodSummary?.metrics.mean.brier_score;
  const deltas = (perSeedComparison?.deltas ?? {}) as Record<string, number | null | undefined>;

  return [
    {
      label: "Worst Group",
      value:
        methodSummary?.comparison_mode === "baseline_metric"
          ? formatMetric(worstGroup)
          : formatSignedMetric(worstGroup),
      note:
        deltas.worst_group_f1_delta !== undefined
          ? `Δ ${formatSignedMetric(deltas.worst_group_f1_delta)} vs baseline`
          : undefined,
      comparisonMode: methodSummary?.comparison_mode,
    },
    {
      label: "OOD",
      value:
        methodSummary?.comparison_mode === "baseline_metric" ? formatMetric(ood) : formatSignedMetric(ood),
      note:
        deltas.ood_macro_f1_delta !== undefined
          ? `Δ ${formatSignedMetric(deltas.ood_macro_f1_delta)} vs baseline`
          : undefined,
      comparisonMode: methodSummary?.comparison_mode,
    },
    {
      label: "ID",
      value:
        methodSummary?.comparison_mode === "baseline_metric" ? formatMetric(id) : formatSignedMetric(id),
      note:
        deltas.id_macro_f1_delta !== undefined
          ? `Δ ${formatSignedMetric(deltas.id_macro_f1_delta)} vs baseline`
          : undefined,
      comparisonMode: methodSummary?.comparison_mode,
    },
    {
      label: "Calibration",
      value: `ECE ${methodSummary?.comparison_mode === "baseline_metric" ? formatMetric(ece) : formatSignedMetric(ece)} / Brier ${methodSummary?.comparison_mode === "baseline_metric" ? formatMetric(brier) : formatSignedMetric(brier)}`,
      note:
        deltas.ece_delta !== undefined || deltas.brier_score_delta !== undefined
          ? `Δ ECE ${formatSignedMetric(deltas.ece_delta)} / Brier ${formatSignedMetric(deltas.brier_score_delta)}`
          : undefined,
      invertPolarity: true,
      comparisonMode: methodSummary?.comparison_mode,
    },
  ];
}

function buildRunActionGroups(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  run: RunEntity,
): EvidenceActionGroup[] {
  const evaluation = getPrimaryEvaluationForRun(index, run.run_id);
  const report = getSupportReportForRun(index, run, bundle);

  const groups: EvidenceActionGroup[] = [];

  const lineageActions = uniqueActions([
    toPathAction(run.metadata_path, "View metadata"),
    toEvidenceAction(run.artifact_refs, "metrics_json", "Open metrics JSON"),
    toEvidenceAction(run.artifact_refs, "selected_checkpoint", "Open selected checkpoint"),
    toEvidenceAction(run.artifact_refs, "training_history_json", "View training history"),
    toEvidenceAction(run.artifact_refs, "predictions.id_test", "Open ID predictions"),
    toEvidenceAction(run.artifact_refs, "predictions.ood_test", "Open OOD predictions"),
    toEvidenceAction(run.artifact_refs, "predictions.validation", "Open validation predictions"),
  ]);

  if (lineageActions.length > 0) {
    groups.push({ title: "Run artifacts", actions: lineageActions });
  }

  const evaluationActions = evaluation
    ? uniqueActions([
        toPathAction(evaluation.metadata_path, "View evaluation metadata"),
        toEvidenceAction(
          evaluation.payload_refs ?? evaluation.artifact_refs,
          "overall_metrics_json",
          "Open evaluation metrics",
        ),
        toEvidenceAction(evaluation.artifact_refs, "id_ood_comparison_csv", "View ID vs OOD table"),
        toEvidenceAction(evaluation.artifact_refs, "split_metrics_csv", "View split metrics"),
        toEvidenceAction(evaluation.artifact_refs, "subgroup_metrics_csv", "View subgroup metrics"),
      ])
    : [];

  if (evaluationActions.length > 0) {
    groups.push({ title: "Evaluation artifacts", actions: evaluationActions });
  }

  const reportActions = report ? buildDefaultReportActions(report) : [];
  if (reportActions.length > 0) {
    groups.push({ title: "Supporting report", actions: reportActions });
  }

  return groups;
}

export function buildRunLaneModels(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  includeExploratory = false,
): RunLaneModel[] {
  const laneMap = new Map<string, { label: string; description: string; exploratory: boolean; runs: RunCardModel[] }>();

  const sortedRuns = getRunEntities(index, includeExploratory).sort((left, right) => {
    const leftLane = getRunLane(left).laneKey;
    const rightLane = getRunLane(right).laneKey;

    if (leftLane !== rightLane) {
      return (
        (LANE_ORDER[leftLane] ?? Number.MAX_SAFE_INTEGER) -
        (LANE_ORDER[rightLane] ?? Number.MAX_SAFE_INTEGER)
      );
    }

    if ((left.is_official ?? false) !== (right.is_official ?? false)) {
      return Number(right.is_official ?? false) - Number(left.is_official ?? false);
    }

    return getSeedSortValue(left.seed) - getSeedSortValue(right.seed);
  });

  for (const run of sortedRuns) {
    const lane = getRunLane(run);
    const existing = laneMap.get(lane.laneKey) ?? {
      label: lane.laneLabel,
      description: lane.description,
      exploratory: lane.isExploratoryLane,
      runs: [],
    };

    existing.runs.push(buildRunCardModel(index, bundle, run));
    laneMap.set(lane.laneKey, existing);
  }

  return [...laneMap.entries()]
    .sort((left, right) => (LANE_ORDER[left[0]] ?? Number.MAX_SAFE_INTEGER) - (LANE_ORDER[right[0]] ?? Number.MAX_SAFE_INTEGER))
    .map(([laneKey, lane]) => {
      const seedGroups = new Map<string, RunCardModel[]>();

      for (const run of lane.runs) {
        const group = seedGroups.get(run.seedLabel) ?? [];
        group.push(run);
        seedGroups.set(run.seedLabel, group);
      }

      return {
        laneKey,
        laneLabel: lane.label,
        description: lane.description,
        isExploratoryLane: lane.exploratory,
        seedGroups: [...seedGroups.entries()]
          .sort(
            (left, right) =>
              getSeedSortValue(left[0]) - getSeedSortValue(right[0]),
          )
          .map(([seedLabel, runs]) => ({
            seedLabel,
            runs: runs.sort((left, right) => left.displayName.localeCompare(right.displayName)),
          })),
      };
    });
}

export function buildRunDetailModel(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  runId: string | null,
): RunDetailModel | null {
  if (!runId) {
    return null;
  }

  const run = (index.entities.runs as RunEntity[]).find((candidate) => candidate.run_id === runId);
  if (!run) {
    return null;
  }

  const methodName = getRunMethodName(run);
  const methodSummary = buildMethodSummaryLookup(bundle).get(methodName);
  const card = buildRunCardModel(index, bundle, run);
  const parentRun = run.parent_run_id
    ? (index.entities.runs as RunEntity[]).find((candidate) => candidate.run_id === run.parent_run_id) ?? null
    : null;

  const lineage = [
    {
      label: "Parent run",
      value: parentRun ? `${getRunDisplayName(parentRun)} · ${parentRun.run_id}` : "Root run",
    },
    {
      label: "Method lane",
      value: card.laneLabel,
    },
    {
      label: "Experiment group",
      value: run.experiment_group ?? "Unknown experiment group",
    },
    {
      label: "Cohort membership",
      value:
        run.is_official === true
          ? "Official seeded evidence"
          : run.tags?.includes("scout")
            ? "Exploratory scout"
            : "Exploratory or historical evidence",
    },
  ];

  return {
    runId: run.run_id,
    displayName: card.displayName,
    methodLabel: formatLabel(methodName),
    seedLabel: card.seedLabel,
    verdict: card.verdict,
    summaryLabel: card.summaryLabel,
    storyNote: methodSummary?.story_note ?? run.notes ?? undefined,
    isOfficial: card.isOfficial,
    isExploratory: card.isExploratory,
    lineage,
    metrics: buildRunMetricModels(index, bundle, run),
    actionGroups: buildRunActionGroups(index, bundle, run),
  };
}

export function buildEvidenceDrawerModel(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  runId: string | null,
): EvidenceDrawerModel | null {
  const detail = buildRunDetailModel(index, bundle, runId);
  if (!detail) {
    return null;
  }

  const run = (index.entities.runs as RunEntity[]).find((candidate) => candidate.run_id === runId);
  if (!run) {
    return null;
  }

  return {
    run: buildRunCardModel(index, bundle, run),
    detail,
  };
}

function buildEntityCardScope(entity: { is_official?: boolean }): EvidenceScope {
  return entity.is_official === true ? "official" : "exploratory";
}

export function buildEvidenceSections(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle | null,
  includeExploratory = false,
): EvidenceSectionModel[] {
  const reports = sortEntitiesByPriority(getReportEntities(index, includeExploratory)).map(
    (report): EvidenceEntityCardModel => ({
      id: report.id,
      title: formatLabel(report.report_scope ?? report.id),
      subtitle: report.report_scope ?? report.id,
      scope: buildEntityCardScope(report),
      badgeLabel: report.is_official === true ? "Official report" : "Exploratory report",
      description: report.metadata_path,
      actions: uniqueActions([
        ...buildDefaultReportActions(report),
        toPathAction(report.metadata_path, "View metadata"),
      ]),
    }),
  );

  const evaluations = sortEntitiesByPriority(getEvaluationEntities(index, includeExploratory)).map(
    (evaluation): EvidenceEntityCardModel => {
      const sourceRun = (index.entities.runs as RunEntity[]).find(
        (run) => run.run_id === evaluation.source_run_id,
      );

      return {
        id: evaluation.id,
        title: sourceRun ? getRunDisplayName(sourceRun) : `Evaluation ${evaluation.eval_id ?? evaluation.id}`,
        subtitle: evaluation.eval_id ?? evaluation.id,
        scope: buildEntityCardScope(evaluation),
        badgeLabel: evaluation.is_official === true ? "Official eval" : "Exploratory eval",
        description: sourceRun ? `${getSeedLabel(sourceRun.seed)} · ${sourceRun.run_id}` : evaluation.metadata_path,
        actions: uniqueActions([
          toPathAction(evaluation.metadata_path, "View metadata"),
          toEvidenceAction(evaluation.payload_refs ?? evaluation.artifact_refs, "overall_metrics_json", "Open evaluation metrics"),
          toEvidenceAction(evaluation.artifact_refs, "id_ood_comparison_csv", "View ID vs OOD table"),
          toEvidenceAction(evaluation.artifact_refs, "split_metrics_csv", "View split metrics"),
        ]),
      };
    },
  );

  const runs = sortEntitiesByPriority(getRunEntities(index, includeExploratory)).map(
    (run): EvidenceEntityCardModel => {
      const detail = buildRunDetailModel(index, bundle, run.run_id);

      return {
        id: run.id,
        title: getRunDisplayName(run),
        subtitle: run.run_id,
        scope: buildEntityCardScope(run),
        badgeLabel: detail?.verdict ?? run.status ?? "unknown",
        description: `${getSeedLabel(run.seed)} · ${formatLabel(getRunMethodName(run))}`,
        actions: uniqueActions([
          toPathAction(run.metadata_path, "View metadata"),
          toEvidenceAction(run.artifact_refs, "metrics_json", "Open metrics JSON"),
          toEvidenceAction(run.artifact_refs, "selected_checkpoint", "Open selected checkpoint"),
          toEvidenceAction(run.artifact_refs, "predictions.id_test", "Open ID predictions"),
          toEvidenceAction(run.artifact_refs, "predictions.ood_test", "Open OOD predictions"),
        ]),
      };
    },
  );

  return [
    {
      key: "reports",
      title: "Reports",
      description: "Official comparison packages first, with exploratory references opt-in only.",
      items: reports,
    },
    {
      key: "evaluations",
      title: "Evaluations",
      description: "Saved shift-eval bundles linked directly from the manifest.",
      items: evaluations,
    },
    {
      key: "runs",
      title: "Runs",
      description: "Metadata, checkpoints, and prediction artifacts grouped around each saved run.",
      items: runs,
    },
  ];
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
      representativeRunId: getRepresentativeRunIdForMethod(index, summary.method_name, true),
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
        representativeRunId: getRepresentativeRunIdForMethod(index, entry.method_name, true),
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
      actions: uniqueActions([
        toEvidenceAction(bundle.report.artifact_refs, "report_markdown", "View supporting report"),
        toEvidenceAction(bundle.report.payload_refs ?? bundle.report.artifact_refs, "report_data_json", "Open report payload"),
        toEvidenceAction(bundle.report.artifact_refs, config.tableRefKey, "View raw metrics table"),
      ]),
      items,
    };
  });
}

function buildVerdictLaneItems(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle,
  domain: FailureDomainKey,
  includeExploratory = false,
) {
  return getFailureDomainSource(bundle, domain)
    .filter((entry) => includeExploratory || entry.is_exploratory !== true)
    .sort((left, right) => getMethodOrder(left.method_name) - getMethodOrder(right.method_name))
    .map((entry) => ({
      methodName: entry.method_name,
      displayName: entry.display_name,
      verdict: entry.primary_verdict ?? entry.stability_label ?? "unknown",
      comparisonMode: entry.comparison_mode,
      isExploratory: entry.is_exploratory,
      representativeRunId: getRepresentativeRunIdForMethod(index, entry.method_name, true),
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
}

function buildVerdictLane(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle,
  closeout: ResearchCloseout | null,
  includeExploratory: boolean,
  key: "robustness" | "calibration",
): VerdictLaneModel {
  if (key === "calibration") {
    const items = buildVerdictLaneItems(index, bundle, "calibration", includeExploratory);
    const temperatureScaling = buildMethodSummaryLookup(bundle).get("temperature_scaling");

    return {
      key,
      label: "Calibration",
      verdict:
        temperatureScaling?.primary_verdict ??
        temperatureScaling?.stability_label ??
        "stable",
      description: "Why reliability moved more cleanly than robustness in the official package.",
      summary:
        temperatureScaling?.story_note ??
        "Temperature scaling remains the cleanest official calibration win.",
      sourceDomain: "calibration",
      dominant: false,
      actions: uniqueActions([
        toEvidenceAction(bundle.report.artifact_refs, "report_markdown", "View report"),
        toEvidenceAction(
          bundle.report.payload_refs ?? bundle.report.artifact_refs,
          "report_data_json",
          "Open report payload",
        ),
        toEvidenceAction(
          bundle.report.artifact_refs,
          FAILURE_DOMAIN_CONFIG.calibration.tableRefKey,
          "View raw metrics table",
        ),
      ]),
      items,
    };
  }

  return {
    key,
    label: "Robustness",
    verdict: closeout?.final_robustness_verdict ?? bundle.summary.final_robustness_verdict ?? "still_mixed",
    description: "Why the final verdict still turns on worst-group and OOD tradeoffs under shift.",
    summary:
      closeout?.summary_bullets?.[0] ??
      closeout?.recommendation_reason ??
      "Robustness remains mixed because no official lane produces a clean, stable win.",
    sourceDomain: "worst_group",
    dominant: true,
    actions: uniqueActions([
      toEvidenceAction(bundle.report.artifact_refs, "report_markdown", "View report"),
      toEvidenceAction(
        bundle.report.payload_refs ?? bundle.report.artifact_refs,
        "report_data_json",
        "Open report payload",
      ),
      toEvidenceAction(
        bundle.report.artifact_refs,
        FAILURE_DOMAIN_CONFIG.worst_group.tableRefKey,
        "View raw metrics table",
      ),
    ]),
    items: buildVerdictLaneItems(index, bundle, "worst_group", includeExploratory),
  };
}

export function buildVerdictWorkspaceModel(
  index: ArtifactIndex,
  bundle: FinalRobustnessBundle,
  includeExploratory = false,
): VerdictWorkspaceModel {
  const closeout = getPrimaryResearchCloseout(index, includeExploratory);
  const lanes = [
    buildVerdictLane(index, bundle, closeout, includeExploratory, "robustness"),
    buildVerdictLane(index, bundle, closeout, includeExploratory, "calibration"),
  ];

  return {
    finalVerdict:
      closeout?.final_robustness_verdict ??
      bundle.summary.final_robustness_verdict ??
      "unknown",
    dominantLaneKey: "robustness",
    supportingReportScope: bundle.report.report_scope ?? bundle.report.id,
    primaryActions: uniqueActions([
      toEvidenceAction(bundle.report.artifact_refs, "report_markdown", "View report"),
      toEvidenceAction(
        bundle.report.payload_refs ?? bundle.report.artifact_refs,
        "report_data_json",
        "Open report payload",
      ),
      toEvidenceAction(
        bundle.report.artifact_refs,
        FAILURE_DOMAIN_CONFIG.worst_group.tableRefKey,
        "View raw metrics table",
      ),
    ]),
    summaryBullets: closeout?.summary_bullets ?? [],
    recommendationReason: closeout?.recommendation_reason,
    nextStep: closeout?.next_step,
    lanes,
  };
}
