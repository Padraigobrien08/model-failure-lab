export type ArtifactRef = {
  exists?: boolean;
  path: string;
};

export type ArtifactRefMap = Record<string, ArtifactRef>;

export type ArtifactEntity = {
  id: string;
  default_visible?: boolean;
  is_official?: boolean;
  metadata_path?: string;
  experiment_group?: string;
  status?: string;
  seed?: number | string | null;
  artifact_refs?: ArtifactRefMap;
};

export type AggregateMetrics = Record<string, number | null | undefined>;

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
