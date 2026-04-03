import path from "node:path";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import type { IncomingMessage, ServerResponse } from "node:http";
import { promisify } from "node:util";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const ARTIFACT_OVERVIEW_PATH = "/__failure_lab__/artifacts/overview.json";
const RUNS_INDEX_PATH = "/__failure_lab__/artifacts/runs.json";
const COMPARISONS_INDEX_PATH = "/__failure_lab__/artifacts/comparisons.json";
const COMPARISON_DETAIL_PATH = "/__failure_lab__/artifacts/comparison-detail.json";
const RUN_DETAIL_PATH = "/__failure_lab__/artifacts/run-detail.json";
const ARTIFACT_QUERY_PATH = "/__failure_lab__/artifacts/query.json";
const ARTIFACT_ROOT_ENV = "FAILURE_LAB_ARTIFACT_ROOT";
const RUN_FILENAME = "run.json";
const RESULTS_FILENAME = "results.json";
const REPORT_FILENAME = "report.json";
const REPORT_DETAILS_FILENAME = "report_details.json";
const execFileAsync = promisify(execFile);

type ArtifactSourceConfig = {
  label: string;
  path: string;
  runsPath: string;
  reportsPath: string;
  isDefault: boolean;
};

type RunInventoryRow = {
  run_id: string;
  dataset: string;
  model: string;
  created_at: string;
  status: string;
};

type ComparisonInventoryRow = {
  report_id: string;
  baseline_run_id: string;
  candidate_run_id: string;
  dataset: string | null;
  created_at: string;
  status: string;
  compatible: boolean;
};

type ComparisonMetricsPayload = {
  attemptedCaseCount: number;
  classifiedCaseCount: number;
  executionErrorCount: number;
  unclassifiedCount: number;
  successfulModelInvocationCount: number;
  failureRate: number | null;
  classificationCoverage: number | null;
  executionSuccessRate: number | null;
};

type ComparisonDeltaMetricsPayload = {
  failureRate: number | null;
  classificationCoverage: number | null;
  executionSuccessRate: number | null;
};

type ComparisonTransitionSummaryRowPayload = {
  transitionType: string;
  label: string;
  count: number;
  caseIds: string[];
};

type ComparisonCaseDeltaPayload = {
  caseId: string;
  prompt: string;
  tags: string[];
  transitionType: string;
  transitionLabel: string;
  baselineFailureType: string | null;
  candidateFailureType: string | null;
  baselineExpectationVerdict: string | null;
  candidateExpectationVerdict: string | null;
  baselineErrorStage: string | null;
  candidateErrorStage: string | null;
  baselineExplanation: string | null;
  candidateExplanation: string | null;
};

type ComparisonDetailPayload = {
  source: {
    label: string;
    path: string;
    runsPath: string;
    reportsPath: string;
  };
  comparison: {
    reportId: string;
    createdAt: string;
    status: string;
    baselineRunId: string;
    candidateRunId: string;
    dataset: string | null;
    baselineDataset: string | null;
    candidateDataset: string | null;
    compatible: boolean;
    reason: string | null;
    comparisonMode: string | null;
    metricsComputedOn: string | null;
  };
  metrics: {
    baseline: ComparisonMetricsPayload;
    candidate: ComparisonMetricsPayload;
    delta: ComparisonDeltaMetricsPayload;
  };
  coverage: {
    sharedCaseCount: number;
    baselineOnlyCaseCount: number;
    candidateOnlyCaseCount: number;
    sharedCaseIds: string[];
    baselineOnlyCaseIds: string[];
    candidateOnlyCaseIds: string[];
  };
  transitions: {
    counts: Record<string, number>;
    summary: ComparisonTransitionSummaryRowPayload[];
  };
  caseDeltas: ComparisonCaseDeltaPayload[];
};

type FailureLabelPayload = {
  failureType: string;
  failureSubtype: string | null;
};

type RunDetailSummaryRowPayload = {
  label: string;
  count: number;
  share: number | null;
  caseIds: string[];
};

type RunTagSlicePayload = {
  tag: string;
  attemptedCaseCount: number;
  classifiedCaseCount: number;
  failureCaseCount: number;
  failureRate: number | null;
  expectationVerdictCounts: Record<string, number>;
};

type RunCasePayload = {
  caseId: string;
  promptId: string;
  prompt: string;
  tags: string[];
  outputText: string | null;
  expectation: {
    expectedFailure: FailureLabelPayload | null;
    observedFailure: FailureLabelPayload | null;
    verdict: string | null;
  };
  classification: {
    failure: FailureLabelPayload;
    confidence: number | null;
    explanation: string | null;
  } | null;
  error: {
    stage: string;
    type: string;
    message: string;
  } | null;
};

type RunDetailPayload = {
  source: {
    label: string;
    path: string;
    runsPath: string;
    reportsPath: string;
  };
  run: {
    runId: string;
    dataset: string;
    model: string;
    createdAt: string;
    status: string;
    reportId: string;
    adapterId: string | null;
    classifierId: string | null;
    runSeed: number | null;
  };
  metrics: {
    attemptedCaseCount: number;
    classifiedCaseCount: number;
    executionErrorCount: number;
    unclassifiedCount: number;
    successfulModelInvocationCount: number;
    failureCaseCount: number;
    failureRate: number | null;
    classificationCoverage: number | null;
    executionSuccessRate: number | null;
  };
  summary: {
    failureTypes: RunDetailSummaryRowPayload[];
    expectationVerdicts: RunDetailSummaryRowPayload[];
    tagSlices: RunTagSlicePayload[];
  };
  lenses: {
    mismatchCaseIds: string[];
    notableCaseIds: string[];
    allCaseIds: string[];
    errorCaseIds: string[];
  };
  cases: RunCasePayload[];
};

function failureLabArtifactsPlugin(): Plugin {
  const repoRoot = path.resolve(__dirname, "..");
  const artifactSource = resolveArtifactSource(repoRoot);
  const queryBridgePath = path.join(repoRoot, "scripts", "query_bridge.py");

  function resolveArtifactSource(rootPath: string): ArtifactSourceConfig {
    const override = process.env[ARTIFACT_ROOT_ENV]?.trim();
    const artifactRoot =
      override && override.length > 0 ? path.resolve(rootPath, override) : rootPath;
    return {
      label: override ? "Configured artifact store" : "Repo root artifact store",
      path: artifactRoot,
      runsPath: path.join(artifactRoot, "runs"),
      reportsPath: path.join(artifactRoot, "reports"),
      isDefault: !override,
    };
  }

  function sourcePayload(source: ArtifactSourceConfig) {
    return {
      label: source.label,
      path: source.path,
      runsPath: source.runsPath,
      reportsPath: source.reportsPath,
    };
  }

  async function invokeQueryBridge<T>(
    command: string,
    args: string[] = [],
  ): Promise<T> {
    const pythonPathEntries = [path.join(repoRoot, "src")];
    if (process.env.PYTHONPATH) {
      pythonPathEntries.push(process.env.PYTHONPATH);
    }

    const { stdout, stderr } = await execFileAsync(
      "python3",
      [queryBridgePath, command, "--root", artifactSource.path, ...args],
      {
        cwd: repoRoot,
        env: {
          ...process.env,
          PYTHONPATH: pythonPathEntries.join(path.delimiter),
        },
      },
    );

    if (stderr.trim().length > 0) {
      process.stderr.write(stderr);
    }

    return JSON.parse(stdout) as T;
  }

  function requireStringField(
    payload: Record<string, unknown>,
    key: string,
    label: string,
  ): string {
    const value = payload[key];
    if (typeof value !== "string" || value.trim().length === 0) {
      throw new Error(`${label} must be a non-empty string`);
    }
    return value;
  }

  function optionalStringField(
    payload: Record<string, unknown>,
    key: string,
    label: string,
  ): string | null {
    const value = payload[key];
    if (value == null) {
      return null;
    }
    return requireStringField(payload, key, label);
  }

  function requireNumberField(
    payload: Record<string, unknown>,
    key: string,
    label: string,
  ): number {
    const value = payload[key];
    if (typeof value !== "number" || Number.isNaN(value)) {
      throw new Error(`${label} must be a number`);
    }
    return value;
  }

  function optionalNumberField(
    payload: Record<string, unknown>,
    key: string,
    label: string,
  ): number | null {
    const value = payload[key];
    if (value == null) {
      return null;
    }
    return requireNumberField(payload, key, label);
  }

  function requireObjectField(
    payload: Record<string, unknown>,
    key: string,
    label: string,
  ): Record<string, unknown> {
    const value = payload[key];
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      throw new Error(`${label} must be an object`);
    }
    return value as Record<string, unknown>;
  }

  function requireStringArrayField(
    payload: Record<string, unknown>,
    key: string,
    label: string,
  ): string[] {
    const value = payload[key];
    if (!Array.isArray(value)) {
      throw new Error(`${label} must be an array`);
    }
    return value.map((entry, index) => {
      if (typeof entry !== "string" || entry.trim().length === 0) {
        throw new Error(`${label}[${index}] must be a non-empty string`);
      }
      return entry;
    });
  }

  async function readJsonRecord(
    filePath: string,
    label: string,
  ): Promise<Record<string, unknown>> {
    const payload = JSON.parse(await fs.readFile(filePath, "utf-8")) as unknown;
    if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error(`${label} must contain a JSON object`);
    }
    return payload as Record<string, unknown>;
  }

  function optionalFailureLabelPayload(
    value: unknown,
    label: string,
  ): FailureLabelPayload | null {
    if (value == null) {
      return null;
    }
    if (typeof value !== "object" || Array.isArray(value)) {
      throw new Error(`${label} must be an object or null`);
    }

    const payload = value as Record<string, unknown>;
    return {
      failureType: requireStringField(payload, "failure_type", `${label}.failure_type`),
      failureSubtype: optionalStringField(
        payload,
        "failure_subtype",
        `${label}.failure_subtype`,
      ),
    };
  }

  function readRunStatus(
    resultsPayload: Record<string, unknown>,
    runPayload: Record<string, unknown>,
  ): string {
    const resultStatus = resultsPayload.status;
    if (typeof resultStatus === "string" && resultStatus.trim().length > 0) {
      return resultStatus;
    }

    const metadata = runPayload.metadata;
    if (metadata !== null && typeof metadata === "object") {
      const metadataStatus = (metadata as Record<string, unknown>).status;
      if (typeof metadataStatus === "string" && metadataStatus.trim().length > 0) {
        return metadataStatus;
      }
    }

    throw new Error("status must be present in results.json or run metadata");
  }

  async function collectRunInventory(
    runsPath: string,
  ): Promise<{ rows: RunInventoryRow[]; issues: string[] }> {
    const issues: string[] = [];
    let entries: Array<{ isDirectory: () => boolean; name: string }>;

    try {
      entries = (await fs.readdir(runsPath, { withFileTypes: true })) as Array<{
        isDirectory: () => boolean;
        name: string;
      }>;
    } catch (error) {
      const code = error instanceof Error && "code" in error ? String(error.code) : null;
      if (code === "ENOENT") {
        return { rows: [], issues };
      }
      throw error;
    }

    const rows: RunInventoryRow[] = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) {
        continue;
      }

      const entryPath = path.join(runsPath, entry.name);
      const runPath = path.join(entryPath, RUN_FILENAME);
      const resultsPath = path.join(entryPath, RESULTS_FILENAME);

      try {
        const runPayload = JSON.parse(await fs.readFile(runPath, "utf-8")) as Record<
          string,
          unknown
        >;
        const resultsPayload = JSON.parse(
          await fs.readFile(resultsPath, "utf-8"),
        ) as Record<string, unknown>;

        rows.push({
          run_id: requireStringField(runPayload, "run_id", `${entry.name}.run_id`),
          dataset: requireStringField(runPayload, "dataset", `${entry.name}.dataset`),
          model: requireStringField(runPayload, "model", `${entry.name}.model`),
          created_at: requireStringField(runPayload, "created_at", `${entry.name}.created_at`),
          status: readRunStatus(resultsPayload, runPayload),
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "unknown error";
        issues.push(`run ${entry.name} could not be indexed: ${message}`);
      }
    }

    rows.sort((left, right) => {
      if (left.created_at !== right.created_at) {
        return right.created_at.localeCompare(left.created_at);
      }
      return right.run_id.localeCompare(left.run_id);
    });

    return { rows, issues };
  }

  function readComparisonStatus(reportPayload: Record<string, unknown>): string {
    const status = reportPayload.status;
    if (status !== null && typeof status === "object") {
      const overall = (status as Record<string, unknown>).overall;
      if (typeof overall === "string" && overall.trim().length > 0) {
        return overall;
      }
    }

    return "comparison_ready";
  }

  async function collectComparisonInventory(
    reportsPath: string,
  ): Promise<{ rows: ComparisonInventoryRow[]; issues: string[] }> {
    const issues: string[] = [];
    let entries: Array<{ isDirectory: () => boolean; name: string }>;

    try {
      entries = (await fs.readdir(reportsPath, { withFileTypes: true })) as Array<{
        isDirectory: () => boolean;
        name: string;
      }>;
    } catch (error) {
      const code = error instanceof Error && "code" in error ? String(error.code) : null;
      if (code === "ENOENT") {
        return { rows: [], issues };
      }
      throw error;
    }

    const rows: ComparisonInventoryRow[] = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) {
        continue;
      }

      const entryPath = path.join(reportsPath, entry.name);
      const reportPath = path.join(entryPath, REPORT_FILENAME);
      const reportDetailsPath = path.join(entryPath, REPORT_DETAILS_FILENAME);

      let reportPayload: Record<string, unknown>;
      try {
        reportPayload = await readJsonRecord(reportPath, `${entry.name}.report`);
      } catch (error) {
        const message = error instanceof Error ? error.message : "unknown error";
        issues.push(`report ${entry.name} could not be read: ${message}`);
        continue;
      }

      const metadata =
        reportPayload.metadata !== null && typeof reportPayload.metadata === "object"
          ? (reportPayload.metadata as Record<string, unknown>)
          : null;
      const reportKind = metadata?.report_kind;
      if (reportKind !== "comparison") {
        continue;
      }

      try {
        await fs.access(reportDetailsPath);
      } catch {
        issues.push(`comparison ${entry.name} is missing ${REPORT_DETAILS_FILENAME}`);
        continue;
      }

      try {
        const comparison = requireObjectField(
          reportPayload,
          "comparison",
          `${entry.name}.comparison`,
        );
        rows.push({
          report_id: requireStringField(
            reportPayload,
            "report_id",
            `${entry.name}.report_id`,
          ),
          baseline_run_id: requireStringField(
            comparison,
            "baseline_run_id",
            `${entry.name}.comparison.baseline_run_id`,
          ),
          candidate_run_id: requireStringField(
            comparison,
            "candidate_run_id",
            `${entry.name}.comparison.candidate_run_id`,
          ),
          dataset:
            typeof comparison.dataset_id === "string" && comparison.dataset_id.trim().length > 0
              ? comparison.dataset_id
              : null,
          created_at: requireStringField(
            reportPayload,
            "created_at",
            `${entry.name}.created_at`,
          ),
          status: readComparisonStatus(reportPayload),
          compatible:
            typeof comparison.compatible === "boolean"
              ? comparison.compatible
              : (() => {
                  throw new Error(`${entry.name}.comparison.compatible must be a boolean`);
                })(),
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "unknown error";
        issues.push(`comparison ${entry.name} could not be indexed: ${message}`);
      }
    }

    rows.sort((left, right) => {
      if (left.created_at !== right.created_at) {
        return right.created_at.localeCompare(left.created_at);
      }
      return right.report_id.localeCompare(left.report_id);
    });

    return { rows, issues };
  }

  function requireMetricSnapshotPayload(
    value: unknown,
    label: string,
  ): ComparisonMetricsPayload {
    const metrics = requireObjectField({ value }, "value", label);
    return {
      attemptedCaseCount: requireNumberField(
        metrics,
        "attempted_case_count",
        `${label}.attempted_case_count`,
      ),
      classifiedCaseCount: requireNumberField(
        metrics,
        "classified_case_count",
        `${label}.classified_case_count`,
      ),
      executionErrorCount: requireNumberField(
        metrics,
        "execution_error_count",
        `${label}.execution_error_count`,
      ),
      unclassifiedCount: requireNumberField(
        metrics,
        "unclassified_count",
        `${label}.unclassified_count`,
      ),
      successfulModelInvocationCount: requireNumberField(
        metrics,
        "successful_model_invocation_count",
        `${label}.successful_model_invocation_count`,
      ),
      failureRate: optionalNumberField(metrics, "failure_rate", `${label}.failure_rate`),
      classificationCoverage: optionalNumberField(
        metrics,
        "classification_coverage",
        `${label}.classification_coverage`,
      ),
      executionSuccessRate: optionalNumberField(
        metrics,
        "execution_success_rate",
        `${label}.execution_success_rate`,
      ),
    };
  }

  function requireComparisonDeltaPayload(
    value: unknown,
    label: string,
  ): ComparisonDeltaMetricsPayload {
    const delta = requireObjectField({ value }, "value", label);
    return {
      failureRate: optionalNumberField(delta, "failure_rate", `${label}.failure_rate`),
      classificationCoverage: optionalNumberField(
        delta,
        "classification_coverage",
        `${label}.classification_coverage`,
      ),
      executionSuccessRate: optionalNumberField(
        delta,
        "execution_success_rate",
        `${label}.execution_success_rate`,
      ),
    };
  }

  function requireTransitionSummaryPayload(
    value: unknown,
    label: string,
  ): ComparisonTransitionSummaryRowPayload[] {
    if (!Array.isArray(value)) {
      throw new Error(`${label} must be an array`);
    }

    return value.map((entry, index) => {
      const row = requireObjectField({ value: entry }, "value", `${label}[${index}]`);
      return {
        transitionType: requireStringField(
          row,
          "transition_type",
          `${label}[${index}].transition_type`,
        ),
        label: requireStringField(row, "label", `${label}[${index}].label`),
        count: requireNumberField(row, "count", `${label}[${index}].count`),
        caseIds: requireStringArrayField(row, "case_ids", `${label}[${index}].case_ids`),
      };
    });
  }

  function requireCaseDeltaPayloads(
    value: unknown,
    label: string,
  ): ComparisonCaseDeltaPayload[] {
    if (!Array.isArray(value)) {
      throw new Error(`${label} must be an array`);
    }

    return value.map((entry, index) => {
      const row = requireObjectField({ value: entry }, "value", `${label}[${index}]`);
      return {
        caseId: requireStringField(row, "case_id", `${label}[${index}].case_id`),
        prompt: requireStringField(row, "prompt", `${label}[${index}].prompt`),
        tags: requireStringArrayField(row, "tags", `${label}[${index}].tags`),
        transitionType: requireStringField(
          row,
          "transition_type",
          `${label}[${index}].transition_type`,
        ),
        transitionLabel: requireStringField(
          row,
          "transition_label",
          `${label}[${index}].transition_label`,
        ),
        baselineFailureType: optionalStringField(
          row,
          "baseline_failure_type",
          `${label}[${index}].baseline_failure_type`,
        ),
        candidateFailureType: optionalStringField(
          row,
          "candidate_failure_type",
          `${label}[${index}].candidate_failure_type`,
        ),
        baselineExpectationVerdict: optionalStringField(
          row,
          "baseline_expectation_verdict",
          `${label}[${index}].baseline_expectation_verdict`,
        ),
        candidateExpectationVerdict: optionalStringField(
          row,
          "candidate_expectation_verdict",
          `${label}[${index}].candidate_expectation_verdict`,
        ),
        baselineErrorStage: optionalStringField(
          row,
          "baseline_error_stage",
          `${label}[${index}].baseline_error_stage`,
        ),
        candidateErrorStage: optionalStringField(
          row,
          "candidate_error_stage",
          `${label}[${index}].candidate_error_stage`,
        ),
        baselineExplanation: optionalStringField(
          row,
          "baseline_explanation",
          `${label}[${index}].baseline_explanation`,
        ),
        candidateExplanation: optionalStringField(
          row,
          "candidate_explanation",
          `${label}[${index}].candidate_explanation`,
        ),
      };
    });
  }

  async function collectComparisonDetail(
    reportId: string,
    reportsPath: string,
    runsPath: string,
  ): Promise<ComparisonDetailPayload> {
    const reportDir = path.join(reportsPath, reportId);
    const reportPayload = await readJsonRecord(
      path.join(reportDir, REPORT_FILENAME),
      `${reportId}.report`,
    );
    const reportDetailsPayload = await readJsonRecord(
      path.join(reportDir, REPORT_DETAILS_FILENAME),
      `${reportId}.report_details`,
    );

    const metadata =
      reportPayload.metadata !== null && typeof reportPayload.metadata === "object"
        ? (reportPayload.metadata as Record<string, unknown>)
        : null;
    if (metadata?.report_kind !== "comparison") {
      throw new Error(`${reportId} is not a comparison report`);
    }

    const comparison = requireObjectField(
      reportPayload,
      "comparison",
      `${reportId}.comparison`,
    );
    const metrics = requireObjectField(reportPayload, "metrics", `${reportId}.metrics`);
    const compatibility = requireObjectField(
      reportDetailsPayload,
      "compatibility",
      `${reportId}.report_details.compatibility`,
    );

    return {
      source: sourcePayload(artifactSource),
      comparison: {
        reportId: requireStringField(reportPayload, "report_id", `${reportId}.report_id`),
        createdAt: requireStringField(reportPayload, "created_at", `${reportId}.created_at`),
        status: readComparisonStatus(reportPayload),
        baselineRunId: requireStringField(
          comparison,
          "baseline_run_id",
          `${reportId}.comparison.baseline_run_id`,
        ),
        candidateRunId: requireStringField(
          comparison,
          "candidate_run_id",
          `${reportId}.comparison.candidate_run_id`,
        ),
        dataset: optionalStringField(comparison, "dataset_id", `${reportId}.comparison.dataset_id`),
        baselineDataset: optionalStringField(
          compatibility,
          "baseline_dataset_id",
          `${reportId}.report_details.compatibility.baseline_dataset_id`,
        ),
        candidateDataset: optionalStringField(
          compatibility,
          "candidate_dataset_id",
          `${reportId}.report_details.compatibility.candidate_dataset_id`,
        ),
        compatible:
          typeof comparison.compatible === "boolean"
            ? comparison.compatible
            : (() => {
                throw new Error(`${reportId}.comparison.compatible must be a boolean`);
              })(),
        reason: optionalStringField(comparison, "reason", `${reportId}.comparison.reason`),
        comparisonMode:
          metadata === null
            ? null
            : optionalStringField(
                metadata,
                "comparison_mode",
                `${reportId}.metadata.comparison_mode`,
              ),
        metricsComputedOn: optionalStringField(
          comparison,
          "metrics_computed_on",
          `${reportId}.comparison.metrics_computed_on`,
        ),
      },
      metrics: {
        baseline: requireMetricSnapshotPayload(metrics.baseline, `${reportId}.metrics.baseline`),
        candidate: requireMetricSnapshotPayload(
          metrics.candidate,
          `${reportId}.metrics.candidate`,
        ),
        delta: requireComparisonDeltaPayload(metrics.delta, `${reportId}.metrics.delta`),
      },
      coverage: {
        sharedCaseCount: requireNumberField(
          compatibility,
          "shared_case_count",
          `${reportId}.report_details.compatibility.shared_case_count`,
        ),
        baselineOnlyCaseCount: requireNumberField(
          compatibility,
          "baseline_only_case_count",
          `${reportId}.report_details.compatibility.baseline_only_case_count`,
        ),
        candidateOnlyCaseCount: requireNumberField(
          compatibility,
          "candidate_only_case_count",
          `${reportId}.report_details.compatibility.candidate_only_case_count`,
        ),
        sharedCaseIds:
          reportDetailsPayload.shared_case_ids === undefined
            ? []
            : requireStringArrayField(
                reportDetailsPayload,
                "shared_case_ids",
                `${reportId}.report_details.shared_case_ids`,
              ),
        baselineOnlyCaseIds:
          reportDetailsPayload.baseline_only_case_ids !== undefined
            ? requireStringArrayField(
                reportDetailsPayload,
                "baseline_only_case_ids",
                `${reportId}.report_details.baseline_only_case_ids`,
              )
            : requireStringArrayField(
                reportDetailsPayload,
                "baseline_case_ids",
                `${reportId}.report_details.baseline_case_ids`,
              ),
        candidateOnlyCaseIds:
          reportDetailsPayload.candidate_only_case_ids !== undefined
            ? requireStringArrayField(
                reportDetailsPayload,
                "candidate_only_case_ids",
                `${reportId}.report_details.candidate_only_case_ids`,
              )
            : requireStringArrayField(
                reportDetailsPayload,
                "candidate_case_ids",
                `${reportId}.report_details.candidate_case_ids`,
              ),
      },
      transitions: {
        counts: Object.fromEntries(
          Object.entries(
            requireObjectField(
              reportDetailsPayload,
              "case_transition_counts",
              `${reportId}.report_details.case_transition_counts`,
            ),
          ).map(([key, value]) => [
            key,
            requireNumberField(
              { value },
              "value",
              `${reportId}.report_details.case_transition_counts.${key}`,
            ),
          ]),
        ),
        summary: requireTransitionSummaryPayload(
          reportDetailsPayload.case_transition_summary,
          `${reportId}.report_details.case_transition_summary`,
        ),
      },
      caseDeltas: requireCaseDeltaPayloads(
        reportDetailsPayload.case_deltas,
        `${reportId}.report_details.case_deltas`,
      ),
    };
  }

  function readRunReportStatus(
    reportPayload: Record<string, unknown>,
    resultsPayload: Record<string, unknown>,
    runPayload: Record<string, unknown>,
  ): string {
    const status = reportPayload.status;
    if (status !== null && typeof status === "object") {
      const overall = (status as Record<string, unknown>).overall;
      if (typeof overall === "string" && overall.trim().length > 0) {
        return overall;
      }
    }

    return readRunStatus(resultsPayload, runPayload);
  }

  function collectCaseIds(
    rows: unknown,
    label: string,
  ): string[] {
    if (!Array.isArray(rows)) {
      throw new Error(`${label} must be an array`);
    }

    return rows.map((entry, index) => {
      if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
        throw new Error(`${label}[${index}] must be an object`);
      }
      return requireStringField(
        entry as Record<string, unknown>,
        "case_id",
        `${label}[${index}].case_id`,
      );
    });
  }

  async function collectRunDetail(
    runId: string,
    runsPath: string,
    reportsPath: string,
  ): Promise<RunDetailPayload> {
    const runDir = path.join(runsPath, runId);
    const reportDir = path.join(reportsPath, `${runId}_report`);
    const runPayload = await readJsonRecord(path.join(runDir, RUN_FILENAME), `${runId}.run`);
    const resultsPayload = await readJsonRecord(
      path.join(runDir, RESULTS_FILENAME),
      `${runId}.results`,
    );
    const reportPayload = await readJsonRecord(
      path.join(reportDir, REPORT_FILENAME),
      `${runId}.report`,
    );
    const reportDetailsPayload = await readJsonRecord(
      path.join(reportDir, REPORT_DETAILS_FILENAME),
      `${runId}.report_details`,
    );

    const casePayloads = resultsPayload.cases;
    if (!Array.isArray(casePayloads)) {
      throw new Error(`${runId}.results.cases must be an array`);
    }

    const cases: RunCasePayload[] = casePayloads.map((entry, index) => {
      if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
        throw new Error(`${runId}.results.cases[${index}] must be an object`);
      }
      const payload = entry as Record<string, unknown>;
      const prompt = requireObjectField(
        payload,
        "prompt",
        `${runId}.results.cases[${index}].prompt`,
      );
      const expectation = requireObjectField(
        payload,
        "expectation",
        `${runId}.results.cases[${index}].expectation`,
      );
      const outputValue = payload.output;
      const classificationValue = payload.classification;
      const errorValue = payload.error;

      const outputText =
        outputValue == null
          ? null
          : requireStringField(
              requireObjectField(payload, "output", `${runId}.results.cases[${index}].output`),
              "text",
              `${runId}.results.cases[${index}].output.text`,
            );

      const classification =
        classificationValue == null
          ? null
          : (() => {
              const rawClassification = requireObjectField(
                payload,
                "classification",
                `${runId}.results.cases[${index}].classification`,
              );
              const failure = optionalFailureLabelPayload(
                {
                  failure_type: rawClassification.failure_type,
                  failure_subtype: rawClassification.failure_subtype,
                },
                `${runId}.results.cases[${index}].classification.failure`,
              );
              if (failure === null) {
                throw new Error(
                  `${runId}.results.cases[${index}].classification.failure must be present`,
                );
              }
              return {
                failure,
                confidence: optionalNumberField(
                  rawClassification,
                  "confidence",
                  `${runId}.results.cases[${index}].classification.confidence`,
                ),
                explanation: optionalStringField(
                  rawClassification,
                  "explanation",
                  `${runId}.results.cases[${index}].classification.explanation`,
                ),
              };
            })();

      const error =
        errorValue == null
          ? null
          : (() => {
              const rawError = requireObjectField(
                payload,
                "error",
                `${runId}.results.cases[${index}].error`,
              );
              return {
                stage: requireStringField(
                  rawError,
                  "stage",
                  `${runId}.results.cases[${index}].error.stage`,
                ),
                type: requireStringField(
                  rawError,
                  "type",
                  `${runId}.results.cases[${index}].error.type`,
                ),
                message: requireStringField(
                  rawError,
                  "message",
                  `${runId}.results.cases[${index}].error.message`,
                ),
              };
            })();

      return {
        caseId: requireStringField(payload, "case_id", `${runId}.results.cases[${index}].case_id`),
        promptId: requireStringField(prompt, "id", `${runId}.results.cases[${index}].prompt.id`),
        prompt: requireStringField(
          prompt,
          "prompt",
          `${runId}.results.cases[${index}].prompt.prompt`,
        ),
        tags: requireStringArrayField(
          prompt,
          "tags",
          `${runId}.results.cases[${index}].prompt.tags`,
        ),
        outputText,
        expectation: {
          expectedFailure: optionalFailureLabelPayload(
            expectation.expected_failure,
            `${runId}.results.cases[${index}].expectation.expected_failure`,
          ),
          observedFailure: optionalFailureLabelPayload(
            expectation.observed_failure,
            `${runId}.results.cases[${index}].expectation.observed_failure`,
          ),
          verdict: optionalStringField(
            expectation,
            "expectation_verdict",
            `${runId}.results.cases[${index}].expectation.expectation_verdict`,
          ),
        },
        classification,
        error,
      };
    });

    const metrics = requireObjectField(reportPayload, "metrics", `${runId}.report.metrics`);
    const failureBreakdown = reportDetailsPayload.failure_type_breakdown;
    if (!Array.isArray(failureBreakdown)) {
      throw new Error(`${runId}.report_details.failure_type_breakdown must be an array`);
    }

    const failureTypes: RunDetailSummaryRowPayload[] = failureBreakdown.map((entry, index) => {
      if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
        throw new Error(`${runId}.report_details.failure_type_breakdown[${index}] must be an object`);
      }
      const row = entry as Record<string, unknown>;
      return {
        label: requireStringField(
          row,
          "failure_type",
          `${runId}.report_details.failure_type_breakdown[${index}].failure_type`,
        ),
        count: requireNumberField(
          row,
          "count",
          `${runId}.report_details.failure_type_breakdown[${index}].count`,
        ),
        share: optionalNumberField(
          row,
          "rate",
          `${runId}.report_details.failure_type_breakdown[${index}].rate`,
        ),
        caseIds: requireStringArrayField(
          row,
          "case_ids",
          `${runId}.report_details.failure_type_breakdown[${index}].case_ids`,
        ),
      };
    });

    const expectationBreakdown = reportDetailsPayload.expectation_verdict_breakdown;
    if (!Array.isArray(expectationBreakdown)) {
      throw new Error(`${runId}.report_details.expectation_verdict_breakdown must be an array`);
    }
    const verdictRows = expectationBreakdown.map((entry, index) => {
      if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
        throw new Error(
          `${runId}.report_details.expectation_verdict_breakdown[${index}] must be an object`,
        );
      }
      return entry as Record<string, unknown>;
    });
    const verdictTotal = verdictRows.reduce(
      (total, row) =>
        total +
        requireNumberField(
          row,
          "count",
          `${runId}.report_details.expectation_verdict_breakdown.count`,
        ),
      0,
    );
    const expectationVerdicts: RunDetailSummaryRowPayload[] = verdictRows.map((row, index) => {
      const count = requireNumberField(
        row,
        "count",
        `${runId}.report_details.expectation_verdict_breakdown[${index}].count`,
      );
      return {
        label: requireStringField(
          row,
          "expectation_verdict",
          `${runId}.report_details.expectation_verdict_breakdown[${index}].expectation_verdict`,
        ),
        count,
        share: verdictTotal > 0 ? count / verdictTotal : null,
        caseIds: requireStringArrayField(
          row,
          "case_ids",
          `${runId}.report_details.expectation_verdict_breakdown[${index}].case_ids`,
        ),
      };
    });

    const tagBreakdown = reportDetailsPayload.tag_breakdown;
    if (!Array.isArray(tagBreakdown)) {
      throw new Error(`${runId}.report_details.tag_breakdown must be an array`);
    }
    const tagSlices: RunTagSlicePayload[] = tagBreakdown.map((entry, index) => {
      if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
        throw new Error(`${runId}.report_details.tag_breakdown[${index}] must be an object`);
      }
      const row = entry as Record<string, unknown>;
      const verdictCounts = requireObjectField(
        row,
        "expectation_verdict_counts",
        `${runId}.report_details.tag_breakdown[${index}].expectation_verdict_counts`,
      );
      return {
        tag: requireStringField(row, "tag", `${runId}.report_details.tag_breakdown[${index}].tag`),
        attemptedCaseCount: requireNumberField(
          row,
          "attempted_case_count",
          `${runId}.report_details.tag_breakdown[${index}].attempted_case_count`,
        ),
        classifiedCaseCount: requireNumberField(
          row,
          "classified_case_count",
          `${runId}.report_details.tag_breakdown[${index}].classified_case_count`,
        ),
        failureCaseCount: requireNumberField(
          row,
          "failure_case_count",
          `${runId}.report_details.tag_breakdown[${index}].failure_case_count`,
        ),
        failureRate: optionalNumberField(
          row,
          "failure_rate",
          `${runId}.report_details.tag_breakdown[${index}].failure_rate`,
        ),
        expectationVerdictCounts: Object.fromEntries(
          Object.entries(verdictCounts).map(([key, value]) => {
            if (typeof value !== "number" || Number.isNaN(value)) {
              throw new Error(
                `${runId}.report_details.tag_breakdown[${index}].expectation_verdict_counts.${key} must be a number`,
              );
            }
            return [key, value];
          }),
        ),
      };
    });

    const expectationMismatches = requireObjectField(
      reportDetailsPayload,
      "expectation_mismatches",
      `${runId}.report_details.expectation_mismatches`,
    );
    const mismatchCaseIds = [
      ...collectCaseIds(
        expectationMismatches.unexpected_failure ?? [],
        `${runId}.report_details.expectation_mismatches.unexpected_failure`,
      ),
      ...collectCaseIds(
        expectationMismatches.missed_expected ?? [],
        `${runId}.report_details.expectation_mismatches.missed_expected`,
      ),
    ];
    const notableCaseIds = collectCaseIds(
      reportDetailsPayload.notable_cases ?? [],
      `${runId}.report_details.notable_cases`,
    );
    const errorCaseIds = Array.from(
      new Set([
        ...collectCaseIds(
          reportDetailsPayload.execution_errors ?? [],
          `${runId}.report_details.execution_errors`,
        ),
        ...collectCaseIds(
          reportDetailsPayload.unclassified_cases ?? [],
          `${runId}.report_details.unclassified_cases`,
        ),
      ]),
    );

    const metadata =
      reportPayload.metadata !== null && typeof reportPayload.metadata === "object"
        ? (reportPayload.metadata as Record<string, unknown>)
        : null;

    return {
      source: sourcePayload(artifactSource),
      run: {
        runId: requireStringField(runPayload, "run_id", `${runId}.run.run_id`),
        dataset: requireStringField(runPayload, "dataset", `${runId}.run.dataset`),
        model: requireStringField(runPayload, "model", `${runId}.run.model`),
        createdAt: requireStringField(runPayload, "created_at", `${runId}.run.created_at`),
        status: readRunReportStatus(reportPayload, resultsPayload, runPayload),
        reportId: requireStringField(reportPayload, "report_id", `${runId}.report.report_id`),
        adapterId:
          metadata !== null
            ? optionalStringField(metadata, "adapter_id", `${runId}.report.metadata.adapter_id`)
            : null,
        classifierId:
          metadata !== null
            ? optionalStringField(
                metadata,
                "classifier_id",
                `${runId}.report.metadata.classifier_id`,
              )
            : null,
        runSeed:
          metadata !== null && typeof metadata.run_seed === "number" && Number.isInteger(metadata.run_seed)
            ? metadata.run_seed
            : null,
      },
      metrics: {
        attemptedCaseCount: requireNumberField(
          metrics,
          "attempted_case_count",
          `${runId}.report.metrics.attempted_case_count`,
        ),
        classifiedCaseCount: requireNumberField(
          metrics,
          "classified_case_count",
          `${runId}.report.metrics.classified_case_count`,
        ),
        executionErrorCount: requireNumberField(
          metrics,
          "execution_error_count",
          `${runId}.report.metrics.execution_error_count`,
        ),
        unclassifiedCount: requireNumberField(
          metrics,
          "unclassified_count",
          `${runId}.report.metrics.unclassified_count`,
        ),
        successfulModelInvocationCount: requireNumberField(
          metrics,
          "successful_model_invocation_count",
          `${runId}.report.metrics.successful_model_invocation_count`,
        ),
        failureCaseCount: requireNumberField(
          metrics,
          "failure_case_count",
          `${runId}.report.metrics.failure_case_count`,
        ),
        failureRate: optionalNumberField(
          metrics,
          "failure_rate",
          `${runId}.report.metrics.failure_rate`,
        ),
        classificationCoverage: optionalNumberField(
          metrics,
          "classification_coverage",
          `${runId}.report.metrics.classification_coverage`,
        ),
        executionSuccessRate: optionalNumberField(
          metrics,
          "execution_success_rate",
          `${runId}.report.metrics.execution_success_rate`,
        ),
      },
      summary: {
        failureTypes,
        expectationVerdicts,
        tagSlices,
      },
      lenses: {
        mismatchCaseIds,
        notableCaseIds,
        allCaseIds: cases.map((caseRow) => caseRow.caseId),
        errorCaseIds,
      },
      cases,
    };
  }

  async function buildArtifactOverview() {
    const [overview, runInventory, comparisonInventory] = await Promise.all([
      invokeQueryBridge<{ comparison_count: number; run_count: number }>("overview"),
      invokeQueryBridge<RunInventoryRow[]>("runs"),
      invokeQueryBridge<ComparisonInventoryRow[]>("comparisons"),
    ]);
    const issues: string[] = [];
    const status =
      issues.length > 0
        ? "incompatible"
        : overview.run_count === 0 && overview.comparison_count === 0
          ? "empty"
          : "ready";

    return {
      status,
      source: sourcePayload(artifactSource),
      runs: {
        count: overview.run_count,
        ids: runInventory.map((row) => row.run_id),
      },
      comparisons: {
        count: overview.comparison_count,
        ids: comparisonInventory.map((row) => row.report_id),
      },
      issues,
      message:
        status === "empty"
          ? artifactSource.isDefault
            ? "No saved engine artifacts were found in the default local root."
            : "No saved engine artifacts were found in the configured artifact root."
          : status === "incompatible"
            ? "One or more saved artifact directories do not match the supported run/report contract."
            : null,
    };
  }

  async function handleArtifactOverview(
    _req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    try {
      const payload = await buildArtifactOverview();
      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(payload));
    } catch (error) {
      res.statusCode = 500;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          status: "incompatible",
          source: sourcePayload(artifactSource),
          runs: { count: 0, ids: [] },
          comparisons: { count: 0, ids: [] },
          issues: [error instanceof Error ? error.message : "artifact overview failed"],
          message: "The artifact source could not be scanned.",
        }),
      );
    }
  }

  async function handleRunsIndex(
    _req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    try {
      const runInventory = await invokeQueryBridge<RunInventoryRow[]>("runs");

      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          source: sourcePayload(artifactSource),
          runs: runInventory,
        }),
      );
    } catch (error) {
      res.statusCode = 500;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          source: sourcePayload(artifactSource),
          runs: [],
          issues: [error instanceof Error ? error.message : "run inventory failed"],
        }),
      );
    }
  }

  async function handleComparisonsIndex(
    _req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    try {
      const comparisonInventory = await invokeQueryBridge<ComparisonInventoryRow[]>(
        "comparisons",
      );

      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          source: sourcePayload(artifactSource),
          comparisons: comparisonInventory,
        }),
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "comparison inventory failed";
      res.statusCode = 500;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          source: sourcePayload(artifactSource),
          comparisons: [],
          message,
          issues: [message],
        }),
      );
    }
  }

  async function handleArtifactQuery(
    req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    const requestUrl = new URL(req.url ?? ARTIFACT_QUERY_PATH, "http://failure-lab.local");
    const mode = requestUrl.searchParams.get("mode") ?? "cases";
    const args = ["--mode", mode];
    const optionMap: Array<[string, string]> = [
      ["failureType", "--failure-type"],
      ["model", "--model"],
      ["dataset", "--dataset"],
      ["runId", "--run-id"],
      ["reportId", "--report-id"],
      ["baselineRunId", "--baseline-run-id"],
      ["candidateRunId", "--candidate-run-id"],
      ["delta", "--delta"],
      ["aggregateBy", "--aggregate-by"],
      ["lastN", "--last-n"],
      ["since", "--since"],
      ["until", "--until"],
      ["limit", "--limit"],
    ];

    for (const [searchKey, argName] of optionMap) {
      const value = requestUrl.searchParams.get(searchKey);
      if (value && value.trim().length > 0) {
        args.push(argName, value);
      }
    }

    try {
      const payload = await invokeQueryBridge("query", args);
      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(payload));
    } catch (error) {
      const message = error instanceof Error ? error.message : "artifact query failed";
      res.statusCode = 500;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message }));
    }
  }

  async function handleComparisonDetail(
    req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    const requestUrl = new URL(req.url ?? COMPARISON_DETAIL_PATH, "http://failure-lab.local");
    const reportId = requestUrl.searchParams.get("reportId");
    if (!reportId) {
      res.statusCode = 400;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message: "reportId query parameter is required" }));
      return;
    }

    try {
      const payload = await collectComparisonDetail(
        reportId,
        artifactSource.reportsPath,
        artifactSource.runsPath,
      );
      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(payload));
    } catch (error) {
      const message = error instanceof Error ? error.message : "comparison detail failed";
      const statusCode =
        message.includes("ENOENT") ||
        message.includes("no such file") ||
        message.includes("not a comparison report")
          ? 404
          : 500;
      res.statusCode = statusCode;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message }));
    }
  }

  async function handleRunDetail(
    req: IncomingMessage,
    res: ServerResponse,
  ): Promise<void> {
    const requestUrl = new URL(req.url ?? RUN_DETAIL_PATH, "http://failure-lab.local");
    const runId = requestUrl.searchParams.get("runId");
    if (!runId) {
      res.statusCode = 400;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message: "runId query parameter is required" }));
      return;
    }

    try {
      const payload = await collectRunDetail(
        runId,
        artifactSource.runsPath,
        artifactSource.reportsPath,
      );
      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(payload));
    } catch (error) {
      const message = error instanceof Error ? error.message : "run detail failed";
      const statusCode =
        message.includes("ENOENT") || message.includes("no such file")
          ? 404
          : 500;
      res.statusCode = statusCode;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message }));
    }
  }

  function registerArtifactMiddleware(
    middlewares: {
      use: (
        handler: (
          req: IncomingMessage,
          res: ServerResponse,
          next: (error?: unknown) => void,
        ) => void,
      ) => void;
    },
  ) {
    middlewares.use((req, res, next) => {
      const pathname = new URL(req.url ?? "/", "http://failure-lab.local").pathname;

      if (pathname === ARTIFACT_OVERVIEW_PATH) {
        void handleArtifactOverview(req, res).catch(next);
        return;
      }

      if (pathname === RUNS_INDEX_PATH) {
        void handleRunsIndex(req, res).catch(next);
        return;
      }

      if (pathname === COMPARISONS_INDEX_PATH) {
        void handleComparisonsIndex(req, res).catch(next);
        return;
      }

      if (pathname === COMPARISON_DETAIL_PATH) {
        void handleComparisonDetail(req, res).catch(next);
        return;
      }

      if (pathname === RUN_DETAIL_PATH) {
        void handleRunDetail(req, res).catch(next);
        return;
      }

      if (pathname === ARTIFACT_QUERY_PATH) {
        void handleArtifactQuery(req, res).catch(next);
        return;
      }

      next();
    });
  }

  return {
    name: "failure-lab-artifacts",
    configureServer(server: {
      middlewares: {
        use: (
          handler: (
            req: IncomingMessage,
            res: ServerResponse,
            next: (error?: unknown) => void,
          ) => void,
        ) => void;
      };
    }) {
      registerArtifactMiddleware(server.middlewares);
    },
    configurePreviewServer(server: {
      middlewares: {
        use: (
          handler: (
            req: IncomingMessage,
            res: ServerResponse,
            next: (error?: unknown) => void,
          ) => void,
        ) => void;
      };
    }) {
      registerArtifactMiddleware(server.middlewares);
    },
  };
}

export default defineConfig({
  plugins: [react(), failureLabArtifactsPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5174,
  },
});
