import {
  ARTIFACT_QUERY_PATH,
  ARTIFACT_OVERVIEW_PATH,
  COMPARISON_DETAIL_PATH,
  COMPARISONS_INDEX_PATH,
  DEFAULT_ARTIFACT_SOURCE,
  RUN_DETAIL_PATH,
  RUNS_INDEX_PATH,
  type ArtifactCollectionSummary,
  type ArtifactInsightEvidenceRef,
  type ArtifactInsightPattern,
  type ArtifactInsightReport,
  type ArtifactInsightSampling,
  type ArtifactQueryAggregateRow,
  type ArtifactQueryCaseRow,
  type ArtifactQueryDeltaRow,
  type ArtifactQueryFacets,
  type ArtifactQueryFilters,
  type ArtifactQueryResponse,
  type ArtifactOverview,
  type ArtifactOverviewStatus,
  type ComparisonCaseDeltaRecord,
  type ComparisonDetail,
  type ComparisonDeltaMetrics,
  type ComparisonInventory,
  type ComparisonInventoryItem,
  type ComparisonMetricsSnapshot,
  type ComparisonTransitionSummaryRow,
  type ArtifactSourceDescriptor,
  type FailureLabelRecord,
  type RunCaseRecord,
  type RunDetail,
  type RunDetailSummaryRow,
  type RunInventory,
  type RunInventoryItem,
  type RunTagSlice,
} from "@/lib/artifacts/types";

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

function requireCollection(value: unknown, field: string): ArtifactCollectionSummary {
  if (value === null || typeof value !== "object") {
    throw new Error(`${field} must be an object`);
  }
  const summary = value as Record<string, unknown>;
  return {
    count: requireCount(summary.count, `${field}.count`),
    ids: requireStringArray(summary.ids, `${field}.ids`),
  };
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

export function buildArtifactQueryPath(searchParams: URLSearchParams): string {
  const query = searchParams.toString();
  return query.length > 0 ? `${ARTIFACT_QUERY_PATH}?${query}` : ARTIFACT_QUERY_PATH;
}

function requireQueryFilters(value: unknown, field: string): ArtifactQueryFilters {
  const filters = requireObject(value, field);
  return {
    failureType: requireStringOrNull(filters.failureType, `${field}.failureType`),
    model: requireStringOrNull(filters.model, `${field}.model`),
    dataset: requireStringOrNull(filters.dataset, `${field}.dataset`),
    runId: requireStringOrNull(filters.runId, `${field}.runId`),
    promptId: requireStringOrNull(filters.promptId, `${field}.promptId`),
    reportId: requireStringOrNull(filters.reportId, `${field}.reportId`),
    baselineRunId: requireStringOrNull(filters.baselineRunId, `${field}.baselineRunId`),
    candidateRunId: requireStringOrNull(filters.candidateRunId, `${field}.candidateRunId`),
    delta: requireStringOrNull(filters.delta, `${field}.delta`),
    aggregateBy: requireStringOrNull(filters.aggregateBy, `${field}.aggregateBy`),
    lastN:
      filters.lastN == null ? null : requireCount(filters.lastN, `${field}.lastN`),
    since: requireStringOrNull(filters.since, `${field}.since`),
    until: requireStringOrNull(filters.until, `${field}.until`),
    limit: requireCount(filters.limit, `${field}.limit`),
  };
}

function requireQueryFacets(value: unknown, field: string): ArtifactQueryFacets {
  const facets = requireObject(value, field);
  return {
    models: requireStringArray(facets.models, `${field}.models`),
    datasets: requireStringArray(facets.datasets, `${field}.datasets`),
    failureTypes: requireStringArray(facets.failureTypes, `${field}.failureTypes`),
    deltaTypes: requireStringArray(facets.deltaTypes, `${field}.deltaTypes`),
  };
}

function requireInsightEvidenceRefs(
  value: unknown,
  field: string,
): ArtifactInsightEvidenceRef[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const ref = requireObject(entry, `${field}[${index}]`);
    const kind = requireString(ref.kind, `${field}[${index}].kind`);
    if (kind !== "run_case" && kind !== "comparison_case") {
      throw new Error(`${field}[${index}].kind must be run_case or comparison_case`);
    }
    return {
      kind,
      label: requireString(ref.label, `${field}[${index}].label`),
      runId: requireStringOrNull(ref.run_id, `${field}[${index}].run_id`),
      reportId: requireStringOrNull(ref.report_id, `${field}[${index}].report_id`),
      caseId: requireStringOrNull(ref.case_id, `${field}[${index}].case_id`),
      promptId: requireStringOrNull(ref.prompt_id, `${field}[${index}].prompt_id`),
      section: requireStringOrNull(ref.section, `${field}[${index}].section`),
      transitionType: requireStringOrNull(
        ref.transition_type,
        `${field}[${index}].transition_type`,
      ),
    };
  });
}

function requireInsightPatterns(value: unknown, field: string): ArtifactInsightPattern[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const pattern = requireObject(entry, `${field}[${index}]`);
    return {
      kind: requireString(pattern.kind, `${field}[${index}].kind`),
      label: requireString(pattern.label, `${field}[${index}].label`),
      summary: requireString(pattern.summary, `${field}[${index}].summary`),
      groupKey: requireStringOrNull(pattern.group_key, `${field}[${index}].group_key`),
      count: requireCount(pattern.count, `${field}[${index}].count`),
      share: requireNumberOrNull(pattern.share, `${field}[${index}].share`),
      evidenceRefs: requireInsightEvidenceRefs(
        pattern.evidence_refs,
        `${field}[${index}].evidence_refs`,
      ),
    };
  });
}

function requireInsightSampling(value: unknown, field: string): ArtifactInsightSampling {
  const sampling = requireObject(value, field);
  return {
    totalMatches: requireCount(sampling.total_matches, `${field}.total_matches`),
    sampledMatches: requireCount(sampling.sampled_matches, `${field}.sampled_matches`),
    sampleLimit: requireCount(sampling.sample_limit, `${field}.sample_limit`),
    truncated:
      typeof sampling.truncated === "boolean"
        ? sampling.truncated
        : (() => {
            throw new Error(`${field}.truncated must be a boolean`);
          })(),
    strategy: requireString(sampling.strategy, `${field}.strategy`),
  };
}

function requireInsightReport(
  value: unknown,
  field: string,
): ArtifactInsightReport | null {
  if (value == null) {
    return null;
  }
  const report = requireObject(value, field);
  const analysisMode = requireString(report.analysis_mode, `${field}.analysis_mode`);
  const sourceKind = requireString(report.source_kind, `${field}.source_kind`);
  if (analysisMode !== "heuristic" && analysisMode !== "llm") {
    throw new Error(`${field}.analysis_mode must be heuristic or llm`);
  }
  if (
    sourceKind !== "cases" &&
    sourceKind !== "deltas" &&
    sourceKind !== "aggregates" &&
    sourceKind !== "comparison"
  ) {
    throw new Error(`${field}.source_kind must be cases, deltas, aggregates, or comparison`);
  }
  return {
    analysisMode,
    sourceKind,
    title: requireString(report.title, `${field}.title`),
    summary: requireString(report.summary, `${field}.summary`),
    generatedBy: requireString(report.generated_by, `${field}.generated_by`),
    sampling: requireInsightSampling(report.sampling, `${field}.sampling`),
    patterns: requireInsightPatterns(report.patterns, `${field}.patterns`),
    anomalies: requireInsightPatterns(report.anomalies, `${field}.anomalies`),
    evidenceLinks: requireInsightEvidenceRefs(report.evidence_links, `${field}.evidence_links`),
  };
}

function requireArtifactQueryCaseRows(value: unknown, field: string): ArtifactQueryCaseRow[] {
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
      caseId: requireString(row.case_id, `${field}[${index}].case_id`),
      promptId: requireString(row.prompt_id, `${field}[${index}].prompt_id`),
      prompt: requireString(row.prompt, `${field}[${index}].prompt`),
      tags: requireStringArray(row.tags, `${field}[${index}].tags`),
      failureType: requireStringOrNull(row.failure_type, `${field}[${index}].failure_type`),
      expectationVerdict: requireStringOrNull(
        row.expectation_verdict,
        `${field}[${index}].expectation_verdict`,
      ),
      explanation: requireStringOrNull(row.explanation, `${field}[${index}].explanation`),
      confidence: requireNumberOrNull(row.confidence, `${field}[${index}].confidence`),
      errorStage: requireStringOrNull(row.error_stage, `${field}[${index}].error_stage`),
    };
  });
}

function requireArtifactQueryDeltaRows(value: unknown, field: string): ArtifactQueryDeltaRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      reportId: requireString(row.report_id, `${field}[${index}].report_id`),
      createdAt: requireString(row.created_at, `${field}[${index}].created_at`),
      dataset: requireStringOrNull(row.dataset, `${field}[${index}].dataset`),
      caseId: requireString(row.case_id, `${field}[${index}].case_id`),
      promptId: requireString(row.prompt_id, `${field}[${index}].prompt_id`),
      prompt: requireString(row.prompt, `${field}[${index}].prompt`),
      tags: requireStringArray(row.tags, `${field}[${index}].tags`),
      transitionType: requireString(row.transition_type, `${field}[${index}].transition_type`),
      transitionLabel: requireString(row.transition_label, `${field}[${index}].transition_label`),
      deltaKind: requireString(row.delta_kind, `${field}[${index}].delta_kind`),
      baselineRunId: requireString(row.baseline_run_id, `${field}[${index}].baseline_run_id`),
      candidateRunId: requireString(row.candidate_run_id, `${field}[${index}].candidate_run_id`),
      baselineModel: requireStringOrNull(row.baseline_model, `${field}[${index}].baseline_model`),
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
      baselineExplanation: requireStringOrNull(
        row.baseline_explanation,
        `${field}[${index}].baseline_explanation`,
      ),
      candidateExplanation: requireStringOrNull(
        row.candidate_explanation,
        `${field}[${index}].candidate_explanation`,
      ),
    };
  });
}

function requireArtifactQueryAggregateRows(
  value: unknown,
  field: string,
): ArtifactQueryAggregateRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }
  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      groupKey: requireString(row.group_key, `${field}[${index}].group_key`),
      groupLabel: requireString(row.group_label, `${field}[${index}].group_label`),
      caseCount: requireCount(row.case_count, `${field}[${index}].case_count`),
    };
  });
}

export function validateArtifactQueryResponse(payload: unknown): ArtifactQueryResponse {
  const data = requireObject(payload, "query");
  const mode = requireString(data.mode, "query.mode");
  const base = {
    source: requireSource(data.source, "query.source"),
    filters: requireQueryFilters(data.filters, "query.filters"),
    facets: requireQueryFacets(data.facets, "query.facets"),
    insightReport: requireInsightReport(data.insight_report, "query.insight_report"),
  };
  if (mode === "cases") {
    return {
      ...base,
      mode,
      rows: requireArtifactQueryCaseRows(data.rows, "query.rows"),
    };
  }
  if (mode === "deltas") {
    return {
      ...base,
      mode,
      rows: requireArtifactQueryDeltaRows(data.rows, "query.rows"),
    };
  }
  if (mode === "aggregates") {
    return {
      ...base,
      mode,
      rows: requireArtifactQueryAggregateRows(data.rows, "query.rows"),
    };
  }
  throw new Error("query.mode must be cases, deltas, or aggregates");
}

export async function loadArtifactQuery(
  searchParams: URLSearchParams,
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactQueryResponse> {
  const response = await fetchImpl(buildArtifactQueryPath(searchParams));
  if (!response.ok) {
    throw new Error(`artifact query request failed with status ${response.status}`);
  }
  const payload = await response.json();
  return validateArtifactQueryResponse(payload);
}

export function validateArtifactOverview(payload: unknown): ArtifactOverview {
  if (payload === null || typeof payload !== "object") {
    throw new Error("artifact overview payload must be an object");
  }

  const data = payload as Record<string, unknown>;
  const status = requireString(data.status, "status");
  if (status !== "ready" && status !== "empty" && status !== "incompatible") {
    throw new Error("status must be ready, empty, or incompatible");
  }

  const issuesValue = data.issues;
  const issues =
    issuesValue === undefined ? [] : requireStringArray(issuesValue, "issues");
  const messageValue = data.message;

  return {
    status: status as ArtifactOverviewStatus,
    source: requireSource(data.source, "source"),
    runs: requireCollection(data.runs, "runs"),
    comparisons: requireCollection(data.comparisons, "comparisons"),
    issues,
    message:
      messageValue == null ? null : requireString(messageValue, "message"),
  };
}

export async function loadArtifactOverview(
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactOverview> {
  const response = await fetchImpl(ARTIFACT_OVERVIEW_PATH);
  if (!response.ok) {
    throw new Error(`artifact overview request failed with status ${response.status}`);
  }

  const payload = await response.json();
  return validateArtifactOverview(payload);
}

function requireRunInventoryItems(value: unknown, field: string): RunInventoryItem[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((item, index) => {
    if (item === null || typeof item !== "object") {
      throw new Error(`${field}[${index}] must be an object`);
    }

    const row = item as Record<string, unknown>;
    return {
      runId: requireString(row.run_id, `${field}[${index}].run_id`),
      dataset: requireString(row.dataset, `${field}[${index}].dataset`),
      model: requireString(row.model, `${field}[${index}].model`),
      createdAt: requireString(row.created_at, `${field}[${index}].created_at`),
      status: requireString(row.status, `${field}[${index}].status`),
    };
  });
}

function requireComparisonInventoryItems(
  value: unknown,
  field: string,
): ComparisonInventoryItem[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((item, index) => {
    if (item === null || typeof item !== "object") {
      throw new Error(`${field}[${index}] must be an object`);
    }

    const row = item as Record<string, unknown>;
    return {
      reportId: requireString(row.report_id, `${field}[${index}].report_id`),
      baselineRunId: requireString(
        row.baseline_run_id,
        `${field}[${index}].baseline_run_id`,
      ),
      candidateRunId: requireString(
        row.candidate_run_id,
        `${field}[${index}].candidate_run_id`,
      ),
      dataset: requireStringOrNull(row.dataset, `${field}[${index}].dataset`),
      createdAt: requireString(row.created_at, `${field}[${index}].created_at`),
      status: requireString(row.status, `${field}[${index}].status`),
      compatible:
        typeof row.compatible === "boolean"
          ? row.compatible
          : (() => {
              throw new Error(`${field}[${index}].compatible must be a boolean`);
            })(),
    };
  });
}

function requireFailureLabelRecord(
  value: unknown,
  field: string,
): FailureLabelRecord | null {
  if (value == null) {
    return null;
  }

  const label = requireObject(value, field);
  return {
    failureType: requireString(label.failureType, `${field}.failureType`),
    failureSubtype: requireStringOrNull(label.failureSubtype, `${field}.failureSubtype`),
  };
}

function requireIntRecord(
  value: unknown,
  field: string,
): Record<string, number> {
  const record = requireObject(value, field);
  return Object.fromEntries(
    Object.entries(record).map(([key, entryValue]) => [key, requireCount(entryValue, `${field}.${key}`)]),
  );
}

function requireSummaryRows(
  value: unknown,
  field: string,
): RunDetailSummaryRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      label: requireString(row.label, `${field}[${index}].label`),
      count: requireCount(row.count, `${field}[${index}].count`),
      share: requireNumberOrNull(row.share, `${field}[${index}].share`),
      caseIds: requireStringArray(row.caseIds, `${field}[${index}].caseIds`),
    };
  });
}

function requireTagSlices(value: unknown, field: string): RunTagSlice[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      tag: requireString(row.tag, `${field}[${index}].tag`),
      attemptedCaseCount: requireCount(
        row.attemptedCaseCount,
        `${field}[${index}].attemptedCaseCount`,
      ),
      classifiedCaseCount: requireCount(
        row.classifiedCaseCount,
        `${field}[${index}].classifiedCaseCount`,
      ),
      failureCaseCount: requireCount(
        row.failureCaseCount,
        `${field}[${index}].failureCaseCount`,
      ),
      failureRate: requireNumberOrNull(
        row.failureRate,
        `${field}[${index}].failureRate`,
      ),
      expectationVerdictCounts: requireIntRecord(
        row.expectationVerdictCounts,
        `${field}[${index}].expectationVerdictCounts`,
      ),
    };
  });
}

function requireRunCaseRecords(value: unknown, field: string): RunCaseRecord[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    const expectation = requireObject(row.expectation, `${field}[${index}].expectation`);
    const classificationValue = row.classification;
    const errorValue = row.error;

    return {
      caseId: requireString(row.caseId, `${field}[${index}].caseId`),
      promptId: requireString(row.promptId, `${field}[${index}].promptId`),
      prompt: requireString(row.prompt, `${field}[${index}].prompt`),
      tags: requireStringArray(row.tags, `${field}[${index}].tags`),
      outputText: requireStringOrNull(row.outputText, `${field}[${index}].outputText`),
      expectation: {
        expectedFailure: requireFailureLabelRecord(
          expectation.expectedFailure,
          `${field}[${index}].expectation.expectedFailure`,
        ),
        observedFailure: requireFailureLabelRecord(
          expectation.observedFailure,
          `${field}[${index}].expectation.observedFailure`,
        ),
        verdict: requireStringOrNull(
          expectation.verdict,
          `${field}[${index}].expectation.verdict`,
        ),
      },
      classification:
        classificationValue == null
          ? null
          : (() => {
              const classification = requireObject(
                classificationValue,
                `${field}[${index}].classification`,
              );
              return {
                failure: requireFailureLabelRecord(
                  classification.failure,
                  `${field}[${index}].classification.failure`,
                )!,
                confidence: requireNumberOrNull(
                  classification.confidence,
                  `${field}[${index}].classification.confidence`,
                ),
                explanation: requireStringOrNull(
                  classification.explanation,
                  `${field}[${index}].classification.explanation`,
                ),
              };
            })(),
      error:
        errorValue == null
          ? null
          : (() => {
              const error = requireObject(errorValue, `${field}[${index}].error`);
              return {
                stage: requireString(error.stage, `${field}[${index}].error.stage`),
                type: requireString(error.type, `${field}[${index}].error.type`),
                message: requireString(error.message, `${field}[${index}].error.message`),
              };
            })(),
    };
  });
}

export function validateRunInventory(payload: unknown): RunInventory {
  if (payload === null || typeof payload !== "object") {
    throw new Error("run inventory payload must be an object");
  }

  const data = payload as Record<string, unknown>;
  return {
    source: requireSource(data.source, "source"),
    runs: requireRunInventoryItems(data.runs, "runs"),
  };
}

export async function loadRunInventory(
  fetchImpl: typeof fetch = fetch,
): Promise<RunInventory> {
  const response = await fetchImpl(RUNS_INDEX_PATH);
  if (!response.ok) {
    throw new Error(`run inventory request failed with status ${response.status}`);
  }

  const payload = await response.json();
  return validateRunInventory(payload);
}

export function validateComparisonInventory(payload: unknown): ComparisonInventory {
  if (payload === null || typeof payload !== "object") {
    throw new Error("comparison inventory payload must be an object");
  }

  const data = payload as Record<string, unknown>;
  return {
    source: requireSource(data.source, "source"),
    comparisons: requireComparisonInventoryItems(data.comparisons, "comparisons"),
  };
}

export async function loadComparisonInventory(
  fetchImpl: typeof fetch = fetch,
): Promise<ComparisonInventory> {
  const response = await fetchImpl(COMPARISONS_INDEX_PATH);
  let payload: unknown = null;

  try {
    payload = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`comparison inventory request failed with status ${response.status}`);
    }
    throw new Error("comparison inventory response was not valid JSON");
  }

  if (!response.ok) {
    const data = payload as Record<string, unknown> | null;
    const message =
      data !== null && typeof data.message === "string"
        ? data.message
        : `comparison inventory request failed with status ${response.status}`;
    throw new Error(message);
  }

  return validateComparisonInventory(payload);
}

export function buildComparisonDetailPath(reportId: string): string {
  const params = new URLSearchParams({ reportId });
  return `${COMPARISON_DETAIL_PATH}?${params.toString()}`;
}

export function buildRunDetailPath(runId: string): string {
  const params = new URLSearchParams({ runId });
  return `${RUN_DETAIL_PATH}?${params.toString()}`;
}

function requireComparisonMetricsSnapshot(
  value: unknown,
  field: string,
): ComparisonMetricsSnapshot {
  const metrics = requireObject(value, field);
  return {
    attemptedCaseCount: requireCount(metrics.attemptedCaseCount, `${field}.attemptedCaseCount`),
    classifiedCaseCount: requireCount(
      metrics.classifiedCaseCount,
      `${field}.classifiedCaseCount`,
    ),
    executionErrorCount: requireCount(
      metrics.executionErrorCount,
      `${field}.executionErrorCount`,
    ),
    unclassifiedCount: requireCount(metrics.unclassifiedCount, `${field}.unclassifiedCount`),
    successfulModelInvocationCount: requireCount(
      metrics.successfulModelInvocationCount,
      `${field}.successfulModelInvocationCount`,
    ),
    failureRate: requireNumberOrNull(metrics.failureRate, `${field}.failureRate`),
    classificationCoverage: requireNumberOrNull(
      metrics.classificationCoverage,
      `${field}.classificationCoverage`,
    ),
    executionSuccessRate: requireNumberOrNull(
      metrics.executionSuccessRate,
      `${field}.executionSuccessRate`,
    ),
  };
}

function requireComparisonDeltaMetrics(
  value: unknown,
  field: string,
): ComparisonDeltaMetrics {
  const metrics = requireObject(value, field);
  return {
    failureRate: requireNumberOrNull(metrics.failureRate, `${field}.failureRate`),
    classificationCoverage: requireNumberOrNull(
      metrics.classificationCoverage,
      `${field}.classificationCoverage`,
    ),
    executionSuccessRate: requireNumberOrNull(
      metrics.executionSuccessRate,
      `${field}.executionSuccessRate`,
    ),
  };
}

function requireComparisonTransitionSummaryRows(
  value: unknown,
  field: string,
): ComparisonTransitionSummaryRow[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      transitionType: requireString(row.transitionType, `${field}[${index}].transitionType`),
      label: requireString(row.label, `${field}[${index}].label`),
      count: requireCount(row.count, `${field}[${index}].count`),
      caseIds: requireStringArray(row.caseIds, `${field}[${index}].caseIds`),
    };
  });
}

function requireComparisonCaseDeltas(
  value: unknown,
  field: string,
): ComparisonCaseDeltaRecord[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((entry, index) => {
    const row = requireObject(entry, `${field}[${index}]`);
    return {
      caseId: requireString(row.caseId, `${field}[${index}].caseId`),
      promptId: requireString(row.promptId, `${field}[${index}].promptId`),
      prompt: requireString(row.prompt, `${field}[${index}].prompt`),
      tags: requireStringArray(row.tags, `${field}[${index}].tags`),
      transitionType: requireString(row.transitionType, `${field}[${index}].transitionType`),
      transitionLabel: requireString(
        row.transitionLabel,
        `${field}[${index}].transitionLabel`,
      ),
      baselineFailureType: requireStringOrNull(
        row.baselineFailureType,
        `${field}[${index}].baselineFailureType`,
      ),
      candidateFailureType: requireStringOrNull(
        row.candidateFailureType,
        `${field}[${index}].candidateFailureType`,
      ),
      baselineExpectationVerdict: requireStringOrNull(
        row.baselineExpectationVerdict,
        `${field}[${index}].baselineExpectationVerdict`,
      ),
      candidateExpectationVerdict: requireStringOrNull(
        row.candidateExpectationVerdict,
        `${field}[${index}].candidateExpectationVerdict`,
      ),
      baselineErrorStage: requireStringOrNull(
        row.baselineErrorStage,
        `${field}[${index}].baselineErrorStage`,
      ),
      candidateErrorStage: requireStringOrNull(
        row.candidateErrorStage,
        `${field}[${index}].candidateErrorStage`,
      ),
      baselineExplanation: requireStringOrNull(
        row.baselineExplanation,
        `${field}[${index}].baselineExplanation`,
      ),
      candidateExplanation: requireStringOrNull(
        row.candidateExplanation,
        `${field}[${index}].candidateExplanation`,
      ),
    };
  });
}

export function validateComparisonDetail(payload: unknown): ComparisonDetail {
  const data = requireObject(payload, "comparison detail payload");
  const comparison = requireObject(data.comparison, "comparison");
  const metrics = requireObject(data.metrics, "metrics");
  const coverage = requireObject(data.coverage, "coverage");
  const transitions = requireObject(data.transitions, "transitions");

  return {
    source: requireSource(data.source, "source"),
    comparison: {
      reportId: requireString(comparison.reportId, "comparison.reportId"),
      createdAt: requireString(comparison.createdAt, "comparison.createdAt"),
      status: requireString(comparison.status, "comparison.status"),
      baselineRunId: requireString(comparison.baselineRunId, "comparison.baselineRunId"),
      candidateRunId: requireString(comparison.candidateRunId, "comparison.candidateRunId"),
      dataset: requireStringOrNull(comparison.dataset, "comparison.dataset"),
      baselineDataset: requireStringOrNull(
        comparison.baselineDataset,
        "comparison.baselineDataset",
      ),
      candidateDataset: requireStringOrNull(
        comparison.candidateDataset,
        "comparison.candidateDataset",
      ),
      compatible:
        typeof comparison.compatible === "boolean"
          ? comparison.compatible
          : (() => {
              throw new Error("comparison.compatible must be a boolean");
            })(),
      reason: requireStringOrNull(comparison.reason, "comparison.reason"),
      comparisonMode: requireStringOrNull(
        comparison.comparisonMode,
        "comparison.comparisonMode",
      ),
      metricsComputedOn: requireStringOrNull(
        comparison.metricsComputedOn,
        "comparison.metricsComputedOn",
      ),
    },
    metrics: {
      baseline: requireComparisonMetricsSnapshot(metrics.baseline, "metrics.baseline"),
      candidate: requireComparisonMetricsSnapshot(metrics.candidate, "metrics.candidate"),
      delta: requireComparisonDeltaMetrics(metrics.delta, "metrics.delta"),
    },
    coverage: {
      sharedCaseCount: requireCount(coverage.sharedCaseCount, "coverage.sharedCaseCount"),
      baselineOnlyCaseCount: requireCount(
        coverage.baselineOnlyCaseCount,
        "coverage.baselineOnlyCaseCount",
      ),
      candidateOnlyCaseCount: requireCount(
        coverage.candidateOnlyCaseCount,
        "coverage.candidateOnlyCaseCount",
      ),
      sharedCaseIds: requireStringArray(coverage.sharedCaseIds, "coverage.sharedCaseIds"),
      baselineOnlyCaseIds: requireStringArray(
        coverage.baselineOnlyCaseIds,
        "coverage.baselineOnlyCaseIds",
      ),
      candidateOnlyCaseIds: requireStringArray(
        coverage.candidateOnlyCaseIds,
        "coverage.candidateOnlyCaseIds",
      ),
    },
    transitions: {
      counts: requireIntRecord(transitions.counts, "transitions.counts"),
      summary: requireComparisonTransitionSummaryRows(
        transitions.summary,
        "transitions.summary",
      ),
    },
    caseDeltas: requireComparisonCaseDeltas(data.caseDeltas, "caseDeltas"),
    insightReport: requireInsightReport(data.insightReport, "insightReport"),
  };
}

export async function loadComparisonDetail(
  reportId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ComparisonDetail> {
  const response = await fetchImpl(buildComparisonDetailPath(reportId));
  let payload: unknown = null;

  try {
    payload = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`comparison detail request failed with status ${response.status}`);
    }
    throw new Error("comparison detail response was not valid JSON");
  }

  if (!response.ok) {
    const data = payload as Record<string, unknown> | null;
    const message =
      data !== null && typeof data.message === "string"
        ? data.message
        : `comparison detail request failed with status ${response.status}`;
    throw new Error(message);
  }

  return validateComparisonDetail(payload);
}

export function validateRunDetail(payload: unknown): RunDetail {
  const data = requireObject(payload, "run detail payload");
  const run = requireObject(data.run, "run");
  const metrics = requireObject(data.metrics, "metrics");
  const summary = requireObject(data.summary, "summary");
  const lenses = requireObject(data.lenses, "lenses");

  return {
    source: requireSource(data.source, "source"),
    run: {
      runId: requireString(run.runId, "run.runId"),
      dataset: requireString(run.dataset, "run.dataset"),
      model: requireString(run.model, "run.model"),
      createdAt: requireString(run.createdAt, "run.createdAt"),
      status: requireString(run.status, "run.status"),
      reportId: requireString(run.reportId, "run.reportId"),
      adapterId: requireStringOrNull(run.adapterId, "run.adapterId"),
      classifierId: requireStringOrNull(run.classifierId, "run.classifierId"),
      runSeed:
        run.runSeed == null ? null : requireCount(run.runSeed, "run.runSeed"),
    },
    metrics: {
      attemptedCaseCount: requireCount(metrics.attemptedCaseCount, "metrics.attemptedCaseCount"),
      classifiedCaseCount: requireCount(metrics.classifiedCaseCount, "metrics.classifiedCaseCount"),
      executionErrorCount: requireCount(
        metrics.executionErrorCount,
        "metrics.executionErrorCount",
      ),
      unclassifiedCount: requireCount(metrics.unclassifiedCount, "metrics.unclassifiedCount"),
      successfulModelInvocationCount: requireCount(
        metrics.successfulModelInvocationCount,
        "metrics.successfulModelInvocationCount",
      ),
      failureCaseCount: requireCount(metrics.failureCaseCount, "metrics.failureCaseCount"),
      failureRate: requireNumberOrNull(metrics.failureRate, "metrics.failureRate"),
      classificationCoverage: requireNumberOrNull(
        metrics.classificationCoverage,
        "metrics.classificationCoverage",
      ),
      executionSuccessRate: requireNumberOrNull(
        metrics.executionSuccessRate,
        "metrics.executionSuccessRate",
      ),
    },
    summary: {
      failureTypes: requireSummaryRows(summary.failureTypes, "summary.failureTypes"),
      expectationVerdicts: requireSummaryRows(
        summary.expectationVerdicts,
        "summary.expectationVerdicts",
      ),
      tagSlices: requireTagSlices(summary.tagSlices, "summary.tagSlices"),
    },
    lenses: {
      mismatchCaseIds: requireStringArray(lenses.mismatchCaseIds, "lenses.mismatchCaseIds"),
      notableCaseIds: requireStringArray(lenses.notableCaseIds, "lenses.notableCaseIds"),
      allCaseIds: requireStringArray(lenses.allCaseIds, "lenses.allCaseIds"),
      errorCaseIds: requireStringArray(lenses.errorCaseIds, "lenses.errorCaseIds"),
    },
    cases: requireRunCaseRecords(data.cases, "cases"),
  };
}

export async function loadRunDetail(
  runId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<RunDetail> {
  const response = await fetchImpl(buildRunDetailPath(runId));
  let payload: unknown = null;

  try {
    payload = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`run detail request failed with status ${response.status}`);
    }
    throw new Error("run detail response was not valid JSON");
  }

  if (!response.ok) {
    const data = payload as Record<string, unknown> | null;
    const message =
      data !== null && typeof data.message === "string"
        ? data.message
        : `run detail request failed with status ${response.status}`;
    throw new Error(message);
  }

  return validateRunDetail(payload);
}

export function buildIncompatibleArtifactOverview(message: string): ArtifactOverview {
  return {
    status: "incompatible",
    source: DEFAULT_ARTIFACT_SOURCE,
    runs: { count: 0, ids: [] },
    comparisons: { count: 0, ids: [] },
    issues: [message],
    message,
  };
}
