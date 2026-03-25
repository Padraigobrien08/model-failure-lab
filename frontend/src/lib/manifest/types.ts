export type ArtifactRef = {
  exists?: boolean;
  path: string;
};

export type ArtifactRefMap = Record<string, ArtifactRef>;

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
