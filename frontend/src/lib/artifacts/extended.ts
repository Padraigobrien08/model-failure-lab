import {
  type ArtifactDatasetHealthSummary,
  type ArtifactDatasetVersionRecord,
  type ArtifactFailureClusterDetail,
  type ArtifactFailureClusterEvidenceRef,
  type ArtifactFailureClusterOccurrence,
  type ArtifactFailureClusterSummary,
  type ArtifactGovernancePolicy,
  type ArtifactHistoryComparisonRow,
  type ArtifactHistoryRunRow,
  type ArtifactHistorySnapshot,
  type ArtifactMetricTrend,
  type ArtifactRecurringFailurePattern,
  type ArtifactSourceDescriptor,
  type ComparisonSignalDriver,
} from "@/lib/artifacts/types";

export const ARTIFACT_DATASET_FAMILIES_PATH =
  "/__failure_lab__/artifacts/dataset-families.json";
export const ARTIFACT_GATE_PATH = "/__failure_lab__/artifacts/gate.json";
export const ARTIFACT_HISTORY_PATH = "/__failure_lab__/artifacts/history.json";
export const ARTIFACT_CLUSTER_DETAIL_PATH =
  "/__failure_lab__/artifacts/cluster-detail.json";

export type DatasetFamilySummary = {
  familyId: string;
  versionCount: number;
  latestDatasetId: string | null;
  latestVersionTag: string | null;
  latestCreatedAt: string | null;
  caseCount: number;
  sourceDatasetId: string | null;
  primaryFailureType: string | null;
  healthLabel: string;
  recentFailRate: number | null;
};

export type DatasetFamiliesResponse = {
  source: ArtifactSourceDescriptor;
  families: DatasetFamilySummary[];
};

export type GateWaiver = {
  comparisonId: string;
  reason: string;
  owner: string | null;
  expiresAt: string | null;
  active: boolean;
};

export type GateDecisionRow = {
  comparisonId: string;
  action: string;
  severity: number;
  policyRule: string;
  blocked: boolean;
  waived: boolean;
  waiver: GateWaiver | null;
};

export type GateResponse = {
  source: ArtifactSourceDescriptor;
  blocked: boolean;
  policy: ArtifactGovernancePolicy;
  rows: GateDecisionRow[];
};

export type ArtifactHistorySnapshotResponse = ArtifactHistorySnapshot & {
  source: ArtifactSourceDescriptor;
};

export type ArtifactClusterDetailResponse = ArtifactFailureClusterDetail & {
  source: ArtifactSourceDescriptor;
};

export type HistorySnapshotParams =
  | { dataset: string; limit?: number }
  | { model: string; limit?: number }
  | { familyId: string; limit?: number };

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${field} must be a non-empty string`);
  }
  return value;
}

function requireStringArray(value: unknown, field: string): string[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((item, index) => requireString(item, `${field}[${index}]`));
}

function requireCount(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    throw new Error(`${field} must be a non-negative integer`);
  }
  return value;
}

function requireObject(value: unknown, field: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function requireNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new Error(`${field} must be a number`);
  }
  return value;
}

function requireBoolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(`${field} must be a boolean`);
  }
  return value;
}

function requireNumberOrNull(value: unknown, field: string): number | null {
  if (value == null) {
    return null;
  }
  return requireNumber(value, field);
}

function requireStringOrNull(value: unknown, field: string): string | null {
  if (value == null) {
    return null;
  }
  return requireString(value, field);
}

function requireSource(value: unknown, field: string): ArtifactSourceDescriptor {
  const source = requireObject(value, field);
  return {
    label: requireString(source.label, `${field}.label`),
    path: requireString(source.path, `${field}.path`),
    runsPath: requireString(source.runsPath, `${field}.runsPath`),
    reportsPath: requireString(source.reportsPath, `${field}.reportsPath`),
  };
}

function requireDatasetFamilySummaries(
  value: unknown,
  field: string,
): DatasetFamilySummary[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      familyId: requireString(row.family_id, `${field}[${index}].family_id`),
      versionCount: requireCount(row.version_count, `${field}[${index}].version_count`),
      latestDatasetId: requireStringOrNull(
        row.latest_dataset_id,
        `${field}[${index}].latest_dataset_id`,
      ),
      latestVersionTag: requireStringOrNull(
        row.latest_version_tag,
        `${field}[${index}].latest_version_tag`,
      ),
      latestCreatedAt: requireStringOrNull(
        row.latest_created_at,
        `${field}[${index}].latest_created_at`,
      ),
      caseCount: requireCount(row.case_count, `${field}[${index}].case_count`),
      sourceDatasetId: requireStringOrNull(
        row.source_dataset_id,
        `${field}[${index}].source_dataset_id`,
      ),
      primaryFailureType: requireStringOrNull(
        row.primary_failure_type,
        `${field}[${index}].primary_failure_type`,
      ),
      healthLabel: requireString(row.health_label, `${field}[${index}].health_label`),
      recentFailRate: requireNumberOrNull(
        row.recent_fail_rate,
        `${field}[${index}].recent_fail_rate`,
      ),
    };
  });
}

export function validateDatasetFamiliesResponse(payload: unknown): DatasetFamiliesResponse {
  const data = requireObject(payload, "dataset_families");
  return {
    source: requireSource(data.source, "dataset_families.source"),
    families: requireDatasetFamilySummaries(data.families, "dataset_families.families"),
  };
}

function requireGateWaiver(value: unknown, field: string): GateWaiver {
  const data = requireObject(value, field);
  return {
    comparisonId: requireString(data.comparison_id, `${field}.comparison_id`),
    reason: requireString(data.reason, `${field}.reason`),
    owner: requireStringOrNull(data.owner, `${field}.owner`),
    expiresAt: requireStringOrNull(data.expires_at, `${field}.expires_at`),
    active: requireBoolean(data.active, `${field}.active`),
  };
}

function requireGateDecisionRows(value: unknown, field: string): GateDecisionRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      comparisonId: requireString(row.comparison_id, `${field}[${index}].comparison_id`),
      action: requireString(row.action, `${field}[${index}].action`),
      severity: requireNumber(row.severity, `${field}[${index}].severity`),
      policyRule: requireString(row.policy_rule, `${field}[${index}].policy_rule`),
      blocked: requireBoolean(row.blocked, `${field}[${index}].blocked`),
      waived: requireBoolean(row.waived, `${field}[${index}].waived`),
      waiver:
        row.waiver == null
          ? null
          : requireGateWaiver(row.waiver, `${field}[${index}].waiver`),
    };
  });
}

function requireGovernancePolicy(value: unknown, field: string): ArtifactGovernancePolicy {
  const data = requireObject(value, field);
  return {
    minimumSeverity: requireNumber(data.minimum_severity, `${field}.minimum_severity`),
    topN: requireCount(data.top_n, `${field}.top_n`),
    failureType: requireStringOrNull(data.failure_type, `${field}.failure_type`),
    familyId: requireStringOrNull(data.family_id, `${field}.family_id`),
    familyCaseCap:
      data.family_case_cap == null
        ? null
        : requireCount(data.family_case_cap, `${field}.family_case_cap`),
    maxDuplicateRatio: requireNumberOrNull(
      data.max_duplicate_ratio,
      `${field}.max_duplicate_ratio`,
    ),
    recurrenceWindow:
      data.recurrence_window == null
        ? 5
        : requireCount(data.recurrence_window, `${field}.recurrence_window`),
    recurrenceThreshold:
      data.recurrence_threshold == null
        ? null
        : requireCount(data.recurrence_threshold, `${field}.recurrence_threshold`),
    strategy: requireString(data.strategy, `${field}.strategy`),
  };
}

export function validateGateResponse(payload: unknown): GateResponse {
  const data = requireObject(payload, "gate");
  return {
    source: requireSource(data.source, "gate.source"),
    blocked: requireBoolean(data.blocked, "gate.blocked"),
    policy: requireGovernancePolicy(data.policy, "gate.policy"),
    rows: requireGateDecisionRows(data.rows, "gate.rows"),
  };
}

function requireComparisonSignalDrivers(
  value: unknown,
  field: string,
): ComparisonSignalDriver[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      driverRank:
        row.driver_rank == null
          ? index
          : requireCount(row.driver_rank, `${field}[${index}].driver_rank`),
      failureType: requireString(row.failure_type, `${field}[${index}].failure_type`),
      delta: requireNumber(row.delta, `${field}[${index}].delta`),
      direction: requireString(row.direction, `${field}[${index}].direction`),
      caseIds: requireStringArray(row.case_ids, `${field}[${index}].case_ids`),
    };
  });
}

function requireMetricTrend(value: unknown, field: string): ArtifactMetricTrend {
  const data = requireObject(value, field);
  return {
    label: requireString(data.label, `${field}.label`),
    delta: requireNumberOrNull(data.delta, `${field}.delta`),
    sampleCount: requireCount(data.sample_count, `${field}.sample_count`),
    firstValue: requireNumberOrNull(data.first_value, `${field}.first_value`),
    lastValue: requireNumberOrNull(data.last_value, `${field}.last_value`),
    volatility: requireNumberOrNull(data.volatility, `${field}.volatility`),
    volatilityLabel: requireString(data.volatility_label, `${field}.volatility_label`),
  };
}

function requireRecurringFailurePatterns(
  value: unknown,
  field: string,
): ArtifactRecurringFailurePattern[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      failureType: requireString(row.failure_type, `${field}[${index}].failure_type`),
      occurrences: requireCount(row.occurrences, `${field}[${index}].occurrences`),
      comparisonIds: requireStringArray(
        row.comparison_ids,
        `${field}[${index}].comparison_ids`,
      ),
      latestDelta: requireNumberOrNull(row.latest_delta, `${field}[${index}].latest_delta`),
    };
  });
}

function requireClusterEvidenceRef(
  value: unknown,
  field: string,
): ArtifactFailureClusterEvidenceRef {
  const row = requireObject(value, field);
  const kind = requireString(row.kind, `${field}.kind`);
  if (kind !== "run_case" && kind !== "comparison_case") {
    throw new Error(`${field}.kind must be run_case or comparison_case`);
  }
  return {
    kind,
    label: requireString(row.label, `${field}.label`),
    runId: requireStringOrNull(row.run_id, `${field}.run_id`),
    reportId: requireStringOrNull(row.report_id, `${field}.report_id`),
    caseId: requireStringOrNull(row.case_id, `${field}.case_id`),
    promptId: requireStringOrNull(row.prompt_id, `${field}.prompt_id`),
    section: requireStringOrNull(row.section, `${field}.section`),
    transitionType: requireStringOrNull(row.transition_type, `${field}.transition_type`),
  };
}

function requireClusterEvidenceRefs(
  value: unknown,
  field: string,
): ArtifactFailureClusterEvidenceRef[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => requireClusterEvidenceRef(entry, `${field}[${index}]`));
}

function requireClusterKind(
  value: unknown,
  field: string,
): "run_case" | "comparison_delta" {
  const kind = requireString(value, field);
  if (kind !== "run_case" && kind !== "comparison_delta") {
    throw new Error(`${field} must be run_case or comparison_delta`);
  }
  return kind;
}

function requireClusterSummary(value: unknown, field: string): ArtifactFailureClusterSummary {
  const row = requireObject(value, field);
  return {
    clusterId: requireString(row.cluster_id, `${field}.cluster_id`),
    clusterKind: requireClusterKind(row.cluster_kind, `${field}.cluster_kind`),
    label: requireString(row.label, `${field}.label`),
    summary: requireString(row.summary, `${field}.summary`),
    occurrenceCount: requireCount(row.occurrence_count, `${field}.occurrence_count`),
    scopeCount: requireCount(row.scope_count, `${field}.scope_count`),
    firstSeenAt: requireString(row.first_seen_at, `${field}.first_seen_at`),
    lastSeenAt: requireString(row.last_seen_at, `${field}.last_seen_at`),
    datasets: requireStringArray(row.datasets, `${field}.datasets`),
    models: requireStringArray(row.models, `${field}.models`),
    failureTypes: requireStringArray(row.failure_types, `${field}.failure_types`),
    transitionTypes: requireStringArray(row.transition_types, `${field}.transition_types`),
    recentSeverity: requireNumberOrNull(row.recent_severity, `${field}.recent_severity`),
    representativeEvidence: requireClusterEvidenceRefs(
      row.representative_evidence,
      `${field}.representative_evidence`,
    ),
  };
}

function requireClusterSummaries(
  value: unknown,
  field: string,
): ArtifactFailureClusterSummary[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => requireClusterSummary(entry, `${field}[${index}]`));
}

function requireClusterOccurrences(
  value: unknown,
  field: string,
): ArtifactFailureClusterOccurrence[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      clusterId: requireString(row.cluster_id, `${field}[${index}].cluster_id`),
      clusterKind: requireClusterKind(row.cluster_kind, `${field}[${index}].cluster_kind`),
      createdAt: requireString(row.created_at, `${field}[${index}].created_at`),
      datasetScope: requireStringOrNull(row.dataset_scope, `${field}[${index}].dataset_scope`),
      dataset: requireStringOrNull(row.dataset, `${field}[${index}].dataset`),
      runId: requireStringOrNull(row.run_id, `${field}[${index}].run_id`),
      model: requireStringOrNull(row.model, `${field}[${index}].model`),
      reportId: requireStringOrNull(row.report_id, `${field}[${index}].report_id`),
      caseId: requireString(row.case_id, `${field}[${index}].case_id`),
      promptId: requireString(row.prompt_id, `${field}[${index}].prompt_id`),
      prompt: requireString(row.prompt, `${field}[${index}].prompt`),
      tags: requireStringArray(row.tags, `${field}[${index}].tags`),
      failureType: requireStringOrNull(row.failure_type, `${field}[${index}].failure_type`),
      expectationVerdict: requireStringOrNull(
        row.expectation_verdict,
        `${field}[${index}].expectation_verdict`,
      ),
      errorStage: requireStringOrNull(row.error_stage, `${field}[${index}].error_stage`),
      deltaKind: requireStringOrNull(row.delta_kind, `${field}[${index}].delta_kind`),
      transitionType: requireStringOrNull(
        row.transition_type,
        `${field}[${index}].transition_type`,
      ),
      baselineRunId: requireStringOrNull(
        row.baseline_run_id,
        `${field}[${index}].baseline_run_id`,
      ),
      candidateRunId: requireStringOrNull(
        row.candidate_run_id,
        `${field}[${index}].candidate_run_id`,
      ),
      baselineModel: requireStringOrNull(
        row.baseline_model,
        `${field}[${index}].baseline_model`,
      ),
      candidateModel: requireStringOrNull(
        row.candidate_model,
        `${field}[${index}].candidate_model`,
      ),
      baselineFailureType: requireStringOrNull(
        row.baseline_failure_type,
        `${field}[${index}].baseline_failure_type`,
      ),
      candidateFailureType: requireStringOrNull(
        row.candidate_failure_type,
        `${field}[${index}].candidate_failure_type`,
      ),
      baselineExpectationVerdict: requireStringOrNull(
        row.baseline_expectation_verdict,
        `${field}[${index}].baseline_expectation_verdict`,
      ),
      candidateExpectationVerdict: requireStringOrNull(
        row.candidate_expectation_verdict,
        `${field}[${index}].candidate_expectation_verdict`,
      ),
      signalVerdict: requireStringOrNull(
        row.signal_verdict,
        `${field}[${index}].signal_verdict`,
      ),
      severity: requireNumberOrNull(row.severity, `${field}[${index}].severity`),
      evidenceRef: requireClusterEvidenceRef(
        row.evidence_ref,
        `${field}[${index}].evidence_ref`,
      ),
    };
  });
}

function requireHistoryRunRows(value: unknown, field: string): ArtifactHistoryRunRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      runId: requireString(row.run_id, `${field}[${index}].run_id`),
      dataset: requireString(row.dataset, `${field}[${index}].dataset`),
      model: requireString(row.model, `${field}[${index}].model`),
      createdAt: requireString(row.created_at, `${field}[${index}].created_at`),
      status: requireString(row.status, `${field}[${index}].status`),
      attemptedCaseCount: requireCount(
        row.attempted_case_count,
        `${field}[${index}].attempted_case_count`,
      ),
      classifiedCaseCount: requireCount(
        row.classified_case_count,
        `${field}[${index}].classified_case_count`,
      ),
      executionErrorCount: requireCount(
        row.execution_error_count,
        `${field}[${index}].execution_error_count`,
      ),
      unclassifiedCount: requireCount(
        row.unclassified_count,
        `${field}[${index}].unclassified_count`,
      ),
      successfulModelInvocationCount: requireCount(
        row.successful_model_invocation_count,
        `${field}[${index}].successful_model_invocation_count`,
      ),
      failureCaseCount: requireCount(
        row.failure_case_count,
        `${field}[${index}].failure_case_count`,
      ),
      failureRate: requireNumberOrNull(row.failure_rate, `${field}[${index}].failure_rate`),
      classificationCoverage: requireNumberOrNull(
        row.classification_coverage,
        `${field}[${index}].classification_coverage`,
      ),
      executionSuccessRate: requireNumberOrNull(
        row.execution_success_rate,
        `${field}[${index}].execution_success_rate`,
      ),
    };
  });
}

function requireHistoryComparisonRows(
  value: unknown,
  field: string,
): ArtifactHistoryComparisonRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      reportId: requireString(row.report_id, `${field}[${index}].report_id`),
      createdAt: requireString(row.created_at, `${field}[${index}].created_at`),
      dataset: requireStringOrNull(row.dataset, `${field}[${index}].dataset`),
      baselineRunId: requireString(row.baseline_run_id, `${field}[${index}].baseline_run_id`),
      candidateRunId: requireString(
        row.candidate_run_id,
        `${field}[${index}].candidate_run_id`,
      ),
      baselineModel: requireStringOrNull(
        row.baseline_model,
        `${field}[${index}].baseline_model`,
      ),
      candidateModel: requireStringOrNull(
        row.candidate_model,
        `${field}[${index}].candidate_model`,
      ),
      status: requireString(row.status, `${field}[${index}].status`),
      compatible: requireBoolean(row.compatible, `${field}[${index}].compatible`),
      signalVerdict: requireString(row.signal_verdict, `${field}[${index}].signal_verdict`),
      regressionScore: requireNumber(
        row.regression_score,
        `${field}[${index}].regression_score`,
      ),
      improvementScore: requireNumber(
        row.improvement_score,
        `${field}[${index}].improvement_score`,
      ),
      netScore: requireNumber(row.net_score, `${field}[${index}].net_score`),
      severity: requireNumber(row.severity, `${field}[${index}].severity`),
      topDrivers: requireComparisonSignalDrivers(
        row.top_drivers,
        `${field}[${index}].top_drivers`,
      ),
    };
  });
}

function requireDatasetVersionRecords(
  value: unknown,
  field: string,
): ArtifactDatasetVersionRecord[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      familyId: requireString(row.family_id, `${field}[${index}].family_id`),
      datasetId: requireString(row.dataset_id, `${field}[${index}].dataset_id`),
      versionNumber: requireCount(row.version_number, `${field}[${index}].version_number`),
      versionTag: requireString(row.version_tag, `${field}[${index}].version_tag`),
      createdAt: requireStringOrNull(row.created_at, `${field}[${index}].created_at`),
      caseCount: requireCount(row.case_count, `${field}[${index}].case_count`),
      path: requireString(row.path, `${field}[${index}].path`),
      parentDatasetId: requireStringOrNull(
        row.parent_dataset_id,
        `${field}[${index}].parent_dataset_id`,
      ),
      sourceComparisonId: requireStringOrNull(
        row.source_comparison_id,
        `${field}[${index}].source_comparison_id`,
      ),
      signalVerdict: requireStringOrNull(
        row.signal_verdict,
        `${field}[${index}].signal_verdict`,
      ),
      severity: requireNumberOrNull(row.severity, `${field}[${index}].severity`),
    };
  });
}

function requireDatasetHealthSummary(
  value: unknown,
  field: string,
): ArtifactDatasetHealthSummary {
  const data = requireObject(value, field);
  return {
    familyId: requireString(data.family_id, `${field}.family_id`),
    healthLabel: requireString(data.health_label, `${field}.health_label`),
    trend: requireMetricTrend(data.trend, `${field}.trend`),
    versionCount: requireCount(data.version_count, `${field}.version_count`),
    evaluationRunCount: requireCount(
      data.evaluation_run_count,
      `${field}.evaluation_run_count`,
    ),
    recentFailRate: requireNumberOrNull(data.recent_fail_rate, `${field}.recent_fail_rate`),
    previousFailRate: requireNumberOrNull(
      data.previous_fail_rate,
      `${field}.previous_fail_rate`,
    ),
    latestDatasetId: requireStringOrNull(data.latest_dataset_id, `${field}.latest_dataset_id`),
    latestVersionTag: requireStringOrNull(
      data.latest_version_tag,
      `${field}.latest_version_tag`,
    ),
    latestCreatedAt: requireStringOrNull(
      data.latest_created_at,
      `${field}.latest_created_at`,
    ),
    sourceDatasetId: requireStringOrNull(
      data.source_dataset_id,
      `${field}.source_dataset_id`,
    ),
    primaryFailureType: requireStringOrNull(
      data.primary_failure_type,
      `${field}.primary_failure_type`,
    ),
  };
}

export function validateHistorySnapshotResponse(
  payload: unknown,
): ArtifactHistorySnapshotResponse {
  const data = requireObject(payload, "history");
  return {
    source: requireSource(data.source, "history.source"),
    scopeKind: requireString(data.scope_kind, "history.scope_kind"),
    scopeValue: requireString(data.scope_value, "history.scope_value"),
    runHistory: requireHistoryRunRows(data.run_history, "history.run_history"),
    comparisonHistory: requireHistoryComparisonRows(
      data.comparison_history,
      "history.comparison_history",
    ),
    runTrend:
      data.run_trend == null ? null : requireMetricTrend(data.run_trend, "history.run_trend"),
    comparisonTrend:
      data.comparison_trend == null
        ? null
        : requireMetricTrend(data.comparison_trend, "history.comparison_trend"),
    recurringFailures: requireRecurringFailurePatterns(
      data.recurring_failures,
      "history.recurring_failures",
    ),
    recurringClusters: requireClusterSummaries(
      data.recurring_clusters ?? [],
      "history.recurring_clusters",
    ),
    datasetVersions: requireDatasetVersionRecords(
      data.dataset_versions,
      "history.dataset_versions",
    ),
    datasetHealth:
      data.dataset_health == null
        ? null
        : requireDatasetHealthSummary(data.dataset_health, "history.dataset_health"),
  };
}

export function validateClusterDetailResponse(payload: unknown): ArtifactClusterDetailResponse {
  const data = requireObject(payload, "cluster_detail");
  return {
    source: requireSource(data.source, "cluster_detail.source"),
    summary: requireClusterSummary(data.summary, "cluster_detail.summary"),
    occurrences: requireClusterOccurrences(data.occurrences, "cluster_detail.occurrences"),
  };
}

async function fetchArtifactJson(
  requestPath: string,
  fallbackLabel: string,
  fetchImpl: typeof fetch,
): Promise<unknown> {
  const response = await fetchImpl(requestPath);
  if (!response.ok) {
    let message = `${fallbackLabel} request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload && typeof payload === "object" && typeof payload.message === "string") {
        message = payload.message;
      }
    } catch {
      // Keep the status-based fallback message.
    }
    throw new Error(message);
  }
  return response.json();
}

export async function loadDatasetFamilies(
  fetchImpl: typeof fetch = fetch,
): Promise<DatasetFamiliesResponse> {
  const payload = await fetchArtifactJson(
    ARTIFACT_DATASET_FAMILIES_PATH,
    "dataset families",
    fetchImpl,
  );
  return validateDatasetFamiliesResponse(payload);
}

export async function loadGate(fetchImpl: typeof fetch = fetch): Promise<GateResponse> {
  const payload = await fetchArtifactJson(ARTIFACT_GATE_PATH, "regression gate", fetchImpl);
  return validateGateResponse(payload);
}

export async function loadHistorySnapshot(
  params: HistorySnapshotParams,
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactHistorySnapshotResponse> {
  const requestUrl = new URL(ARTIFACT_HISTORY_PATH, "http://failure-lab.local");
  if ("dataset" in params) {
    requestUrl.searchParams.set("dataset", params.dataset);
  } else if ("model" in params) {
    requestUrl.searchParams.set("model", params.model);
  } else {
    requestUrl.searchParams.set("familyId", params.familyId);
  }
  if (params.limit != null) {
    requestUrl.searchParams.set("limit", String(params.limit));
  }
  const payload = await fetchArtifactJson(
    `${requestUrl.pathname}${requestUrl.search}`,
    "history snapshot",
    fetchImpl,
  );
  return validateHistorySnapshotResponse(payload);
}

export async function loadClusterDetail(
  clusterId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactClusterDetailResponse> {
  const requestUrl = new URL(ARTIFACT_CLUSTER_DETAIL_PATH, "http://failure-lab.local");
  requestUrl.searchParams.set("clusterId", clusterId);
  const payload = await fetchArtifactJson(
    `${requestUrl.pathname}${requestUrl.search}`,
    "cluster detail",
    fetchImpl,
  );
  return validateClusterDetailResponse(payload);
}
