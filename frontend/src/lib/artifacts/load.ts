import {
  ARTIFACT_OVERVIEW_PATH,
  COMPARISONS_INDEX_PATH,
  DEFAULT_ARTIFACT_SOURCE,
  RUN_DETAIL_PATH,
  RUNS_INDEX_PATH,
  type ArtifactCollectionSummary,
  type ArtifactOverview,
  type ArtifactOverviewStatus,
  type ComparisonInventory,
  type ComparisonInventoryItem,
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

export function buildRunDetailPath(runId: string): string {
  const params = new URLSearchParams({ runId });
  return `${RUN_DETAIL_PATH}?${params.toString()}`;
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
