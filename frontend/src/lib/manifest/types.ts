export type ArtifactRef = {
  exists?: boolean;
  path: string;
};

export type ArtifactRefValue = ArtifactRef | ArtifactRefMap | null;

export interface ArtifactRefMap {
  [key: string]: ArtifactRefValue;
}

export type ArtifactEntity = {
  id: string;
  entity_type?: string;
  default_visible?: boolean;
  is_official?: boolean;
  metadata_path?: string;
  experiment_group?: string;
  status?: string;
  seed?: number | string | null;
  artifact_refs?: ArtifactRefMap;
};

export type RunEntity = ArtifactEntity & {
  completed_at?: string | null;
  dataset_name?: string;
  duration_seconds?: number | null;
  experiment_group?: string;
  experiment_type?: string | null;
  mitigation_method?: string | null;
  model_name?: string;
  notes?: string | null;
  parent_run_id?: string | null;
  run_id: string;
  seed?: number | string | null;
  started_at?: string | null;
  status?: string;
  tags?: string[];
  timestamp?: string | null;
  training_summary?: {
    best_epoch?: number;
    best_validation_metric_name?: string;
    best_validation_metric_value?: number;
    completed_epochs?: number;
    selected_checkpoint_path?: string;
    train_sample_count?: number;
    validation_sample_count?: number;
  } | null;
};

export type EvaluationEntity = ArtifactEntity & {
  dataset_name?: string;
  eval_id?: string;
  experiment_group?: string;
  headline_metrics?: AggregateMetrics;
  mitigation_method?: string | null;
  model_name?: string;
  payload_refs?: ArtifactRefMap;
  seed?: number | string | null;
  source_parent_run_id?: string | null;
  source_run_id?: string | null;
  status?: string;
  tags?: string[];
};

export type AggregateMetrics = Record<string, number | null | undefined>;

export type FailureDomainKey = "worst_group" | "ood" | "id" | "calibration";

export type MetricComparisonMode = "baseline_metric" | "delta_vs_baseline" | string;

export type SeededCohort = {
  cohort_id: string;
  display_name: string;
  cohort_type: "baseline" | "mitigation";
  model_name: string;
  mitigation_method?: string | null;
  default_visible?: boolean;
  is_official?: boolean;
  aggregate_metrics?: {
    mean?: AggregateMetrics;
    std?: AggregateMetrics;
  };
  per_seed_metrics?: Array<Record<string, unknown>>;
  linked_report_id?: string;
};

export type MitigationComparisonView = {
  view_id: string;
  mitigation_method: string;
  default_visible?: boolean;
  is_official?: boolean;
  aggregate_report_id?: string;
  aggregate_report_scope?: string;
  stability_assessment?: {
    label?: string;
    rationale?: string;
  };
  comparison_summary?: Record<string, unknown>;
  per_seed_comparisons?: Array<Record<string, unknown>>;
};

export type StabilityPackage = {
  view_id?: string;
  default_visible?: boolean;
  is_official?: boolean;
  milestone_assessment?: {
    dataset_expansion_recommendation?: string;
    recommendation_reason?: string;
    next_step?: string;
    v1_1_findings_status?: string;
  };
  cohort_summaries?: Record<string, string>;
  artifact_refs?: ArtifactRefMap;
};

export type ResearchCloseout = {
  view_id: string;
  default_visible?: boolean;
  is_official?: boolean;
  final_robustness_verdict?: string;
  dataset_expansion_decision?: string;
  recommendation_reason?: string;
  next_step?: string;
  findings_doc_path?: string;
  ui_entrypoint_path?: string;
  reopen_conditions?: string[];
  summary_bullets?: string[];
  official_methods?: string[];
  exploratory_methods?: string[];
  artifact_refs?: ArtifactRefMap;
};

export type ReportEntity = ArtifactEntity & {
  report_id?: string;
  report_scope?: string;
  payload_refs?: ArtifactRefMap;
  artifact_refs?: ArtifactRefMap;
  summary_snapshot?: Record<string, unknown>;
};

export type FinalRobustnessMethodSummary = {
  comparison_mode: MetricComparisonMode;
  display_name: string;
  evidence_scope: string;
  is_exploratory: boolean;
  method_name: string;
  metrics: {
    mean: AggregateMetrics;
    std: AggregateMetrics;
  };
  primary_verdict?: string;
  promotion_decision?: string | null;
  seed_count?: number;
  seeded_interpretation?: string | null;
  stability_label?: string | null;
  story_note?: string;
  verdict_counts?: Record<string, number> | null;
};

export type FailureDomainSummaryItem = {
  comparison_mode: MetricComparisonMode;
  display_name: string;
  evidence_scope: string;
  is_exploratory: boolean;
  method_name: string;
  metric_key?: string;
  mean?: number | null;
  std?: number | null;
  ece_mean?: number | null;
  ece_std?: number | null;
  brier_score_mean?: number | null;
  brier_score_std?: number | null;
  primary_verdict?: string;
  promotion_decision?: string | null;
  seed_count?: number;
  seeded_interpretation?: string | null;
  stability_label?: string | null;
  story_note?: string;
};

export type PromotionAudit = {
  audit_name?: string;
  candidate_display_name?: string;
  candidate_method?: string;
  candidate_metrics?: AggregateMetrics;
  candidate_verdict?: string;
  dataset_expansion_recommendation?: string;
  decision?: string;
  decision_reason?: string;
  reference_method?: string;
  reference_stability_label?: string;
};

export type FinalRobustnessReportData = {
  official_method_summaries: FinalRobustnessMethodSummary[];
  exploratory_method_summaries: FinalRobustnessMethodSummary[];
  worst_group_summary: FailureDomainSummaryItem[];
  ood_summary: FailureDomainSummaryItem[];
  id_summary: FailureDomainSummaryItem[];
  calibration_summary: FailureDomainSummaryItem[];
  final_robustness_verdict?: string;
  promotion_audit?: PromotionAudit;
};

export type FinalRobustnessReportSummary = {
  final_robustness_verdict?: string;
  headline_findings: string[];
  key_takeaway?: string;
  next_step?: string;
  official_methods: FinalRobustnessMethodSummary[];
  exploratory_methods: FinalRobustnessMethodSummary[];
};

export type FinalRobustnessBundle = {
  report: ReportEntity;
  data: FinalRobustnessReportData;
  summary: FinalRobustnessReportSummary;
};

export type EvidenceAction = {
  label: string;
  path: string;
};

export type EvidenceScope = "official" | "exploratory";

export type WorkbenchSelection = {
  scope: EvidenceScope;
  verdict: string | null;
  lane: string | null;
  method: string | null;
  run: string | null;
  artifact: string | null;
  domain: FailureDomainKey | null;
};

export type BreadcrumbItemModel = {
  label: string;
  value: string;
  href: string;
  isActive: boolean;
};

export type SeedBreakdownRow = {
  seed: string;
  runId?: string;
  evalId?: string;
  verdict?: string;
  metrics: AggregateMetrics;
  deltas: AggregateMetrics;
  note?: string;
};

export type ComparisonCardMetric = {
  label: string;
  value: number | null | undefined;
  std: number | null | undefined;
  comparisonMode: MetricComparisonMode;
  invertPolarity?: boolean;
};

export type ComparisonCardModel = {
  methodName: string;
  displayName: string;
  verdict: string;
  comparisonMode: MetricComparisonMode;
  storyNote?: string;
  seedCount: number;
  seededInterpretation?: string | null;
  isExploratory: boolean;
  representativeRunId?: string | null;
  metrics: {
    worstGroup: ComparisonCardMetric;
    ood: ComparisonCardMetric;
    id: ComparisonCardMetric;
    ece: ComparisonCardMetric;
    brier: ComparisonCardMetric;
  };
  seedBreakdown: SeedBreakdownRow[];
  actions: EvidenceAction[];
};

export type FailureDomainItemModel = {
  methodName: string;
  displayName: string;
  verdict: string;
  comparisonMode: MetricComparisonMode;
  isExploratory: boolean;
  representativeRunId?: string | null;
  storyNote?: string;
  seedCount: number;
  mean?: number | null;
  std?: number | null;
  eceMean?: number | null;
  eceStd?: number | null;
  brierMean?: number | null;
  brierStd?: number | null;
  seedBreakdown: SeedBreakdownRow[];
};

export type FailureDomainModel = {
  domain: FailureDomainKey;
  label: string;
  description: string;
  actions: EvidenceAction[];
  items: FailureDomainItemModel[];
};

export type ArtifactIndex = {
  schema_version: string;
  generated_at?: string;
  artifact_root?: string;
  default_filters?: {
    official_only?: boolean;
  };
  entities: {
    runs: ArtifactEntity[];
    evaluations: ArtifactEntity[];
    reports: ArtifactEntity[];
  };
  views: {
    seeded_cohorts: SeededCohort[];
    mitigation_comparisons: MitigationComparisonView[];
    stability_packages: StabilityPackage[];
    research_closeout: ResearchCloseout[];
  };
};

export type RunCardModel = {
  runId: string;
  displayName: string;
  methodName: string;
  laneKey: string;
  laneLabel: string;
  seedLabel: string;
  verdict: string;
  summaryLabel: string;
  isOfficial: boolean;
  isExploratory: boolean;
  timestamp?: string | null;
};

export type RunSeedGroupModel = {
  seedLabel: string;
  runs: RunCardModel[];
};

export type RunLaneModel = {
  laneKey: string;
  laneLabel: string;
  description: string;
  isExploratoryLane: boolean;
  seedGroups: RunSeedGroupModel[];
};

export type RunDetailMetricModel = {
  label: string;
  value: string;
  note?: string;
  invertPolarity?: boolean;
  comparisonMode?: MetricComparisonMode;
};

export type RunLineageItemModel = {
  label: string;
  value: string;
  path?: string;
};

export type EvidenceActionGroup = {
  title: string;
  actions: EvidenceAction[];
};

export type RunDetailModel = {
  runId: string;
  displayName: string;
  methodLabel: string;
  seedLabel: string;
  verdict: string;
  summaryLabel: string;
  storyNote?: string;
  isOfficial: boolean;
  isExploratory: boolean;
  lineage: RunLineageItemModel[];
  metrics: RunDetailMetricModel[];
  actionGroups: EvidenceActionGroup[];
};

export type EvidenceDrawerModel = {
  run: RunCardModel;
  detail: RunDetailModel;
};

export type EvidenceEntityCardModel = {
  id: string;
  title: string;
  subtitle: string;
  scope: EvidenceScope;
  badgeLabel: string;
  description?: string;
  actions: EvidenceAction[];
};

export type EvidenceSectionModel = {
  key: "reports" | "evaluations" | "runs";
  title: string;
  description: string;
  items: EvidenceEntityCardModel[];
};

export type OverviewSnapshot = {
  seededCohorts: SeededCohort[];
  mitigationLabels: Record<string, string>;
  finalRobustnessVerdict?: string;
  datasetExpansionRecommendation?: string;
  recommendationReason?: string;
  nextStep?: string;
  reopenConditions: string[];
  summaryBullets: string[];
  inventoryCounts: {
    runs: number;
    evaluations: number;
    reports: number;
  };
  officialMethods: string[];
  exploratoryMethods: string[];
};

export type VerdictLaneModel = {
  key: string;
  label: string;
  verdict: string;
  description: string;
  summary: string;
  sourceDomain: FailureDomainKey;
  dominant: boolean;
  actions: EvidenceAction[];
  items: FailureDomainItemModel[];
};

export type VerdictWorkspaceModel = {
  finalVerdict: string;
  dominantLaneKey: string;
  supportingReportScope: string;
  primaryActions: EvidenceAction[];
  summaryBullets: string[];
  recommendationReason?: string;
  nextStep?: string;
  lanes: VerdictLaneModel[];
};
