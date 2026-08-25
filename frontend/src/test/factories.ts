/**
 * Shared typed builders for the operator-console test suite.
 *
 * Two kinds of builders live here:
 *
 * 1. Parsed (camelCase) builders — used for the App's initial-state test seams
 *    (`initialArtifactState`, `initialRunInventoryState`, …) and for components
 *    rendered directly (HarvestDialog). These match the TS types exactly.
 *
 * 2. Wire builders (suffixed `Wire`) — JSON payloads served through stubbed
 *    `fetch` to the page-level loaders (`loadComparisonDetail`, `loadRunDetail`,
 *    `loadArtifactQuery`, `loadArtifactDatasetVersions`, `loadClusterDetail`,
 *    `evolveArtifactDataset`). Field casing follows what each validator in
 *    load.ts / extended.ts actually reads (mostly snake_case; comparison/run
 *    detail payloads are camelCase except the governance recommendation).
 */

import type {
  DatasetFamiliesState,
  GateState,
} from "@/app/router";
import type {
  DatasetFamiliesResponse,
  DatasetFamilySummary,
  GateDecisionRow,
  GateResponse,
} from "@/lib/artifacts/extended";
import type {
  ArtifactGovernancePolicy,
  ArtifactGovernanceRecommendation,
  ArtifactOverview,
  ArtifactShellState,
  ArtifactSourceDescriptor,
  ComparisonInventoryItem,
  ComparisonInventoryState,
  ComparisonSignal,
  RunDetail,
  RunCaseRecord,
  RunInventoryItem,
  RunInventoryState,
} from "@/lib/artifacts/types";

// ---------------------------------------------------------------------------
// Canonical ids shared across tests
// ---------------------------------------------------------------------------

export const BASELINE_RUN_ID = "run_base_001";
export const CANDIDATE_RUN_ID = "run_cand_002";
export const REPORT_ID = "cmp_001";
export const DATASET_ID = "qa-failures-v1";
export const FAMILY_ID = "qa-regressions";
export const CLUSTER_ID = "cluster_hallu_01";

export const SOURCE: ArtifactSourceDescriptor = {
  label: "Local artifact root",
  path: "/work/failure-lab-workspace",
  runsPath: "runs/",
  reportsPath: "reports/",
};

// ---------------------------------------------------------------------------
// Overview / shell state
// ---------------------------------------------------------------------------

export function buildOverview(
  runIds: string[] = [BASELINE_RUN_ID, CANDIDATE_RUN_ID],
  comparisonIds: string[] = [REPORT_ID],
): ArtifactOverview {
  return {
    status: "ready",
    source: SOURCE,
    runs: { count: runIds.length, ids: runIds },
    comparisons: { count: comparisonIds.length, ids: comparisonIds },
    issues: [],
    message: null,
  };
}

export function buildReadyArtifactState(
  runIds?: string[],
  comparisonIds?: string[],
): ArtifactShellState {
  return { status: "ready", overview: buildOverview(runIds, comparisonIds) };
}

// ---------------------------------------------------------------------------
// Run inventory
// ---------------------------------------------------------------------------

export function buildRunInventoryItem(
  overrides: Partial<RunInventoryItem> = {},
): RunInventoryItem {
  return {
    runId: BASELINE_RUN_ID,
    dataset: DATASET_ID,
    model: "demo-baseline",
    createdAt: "2026-08-01T10:00:00Z",
    status: "completed",
    attemptedCaseCount: 12,
    failureRate: 0.25,
    classificationCoverage: 1,
    executionErrorCount: 0,
    ...overrides,
  };
}

export function defaultRuns(): RunInventoryItem[] {
  return [
    buildRunInventoryItem(),
    buildRunInventoryItem({
      runId: CANDIDATE_RUN_ID,
      model: "demo-candidate",
      createdAt: "2026-08-02T10:00:00Z",
      failureRate: 0.35,
    }),
  ];
}

export function buildReadyRunInventoryState(
  runs: RunInventoryItem[] = defaultRuns(),
): RunInventoryState {
  return {
    status: "ready",
    inventory: { source: SOURCE, runs },
    message: null,
  };
}

// ---------------------------------------------------------------------------
// Signal / governance
// ---------------------------------------------------------------------------

export function buildSignal(overrides: Partial<ComparisonSignal> = {}): ComparisonSignal {
  return {
    verdict: "regression",
    reason: "failure rate increased on shared cases",
    regressionScore: 0.3,
    improvementScore: 0.1,
    netScore: -0.2,
    severity: 0.42,
    topDrivers: [
      {
        driverRank: 0,
        failureType: "hallucination",
        delta: 0.2,
        direction: "regression",
        caseIds: ["case_reg", "case_swap"],
      },
      {
        driverRank: 1,
        failureType: "refusal",
        delta: -0.1,
        direction: "improvement",
        caseIds: ["case_fix"],
      },
    ],
    ...overrides,
  };
}

export function buildGovernancePolicy(): ArtifactGovernancePolicy {
  return {
    minimumSeverity: 0.25,
    topN: 10,
    failureType: null,
    familyId: null,
    familyCaseCap: null,
    maxDuplicateRatio: null,
    recurrenceWindow: 5,
    recurrenceThreshold: null,
    strategy: "top_regressions",
  };
}

export function buildGovernanceRecommendation(
  overrides: Partial<ArtifactGovernanceRecommendation> = {},
): ArtifactGovernanceRecommendation {
  return {
    comparisonId: REPORT_ID,
    action: "evolve",
    policyRule: "severity_above_threshold",
    rationale: "Recurring hallucination regressions warrant evolving the family.",
    policy: buildGovernancePolicy(),
    signal: buildSignal(),
    matchedFamily: {
      familyId: FAMILY_ID,
      matchKind: "dataset",
      exists: true,
      versionCount: 2,
      latestDatasetId: "qa-regressions-v2",
      currentCaseCount: 12,
      proposedAdditionCount: 2,
      duplicateCaseCount: 0,
      duplicateRatio: 0,
      projectedCaseCount: 14,
      familyCaseCap: null,
      capReached: false,
      duplicateRatioExceeded: false,
    },
    selectedCaseCount: 2,
    evidenceCaseIds: ["case_reg", "case_swap"],
    previewCases: [],
    historyContext: null,
    clusterContext: [],
    escalation: null,
    lifecycleRecommendation: null,
    ...overrides,
  };
}

/** Snake_case wire form of the governance recommendation (strict in load.ts). */
export function buildGovernanceRecommendationWire(): Record<string, unknown> {
  return {
    comparison_id: REPORT_ID,
    action: "evolve",
    policy_rule: "severity_above_threshold",
    rationale: "Recurring hallucination regressions warrant evolving the family.",
    policy: {
      minimum_severity: 0.25,
      top_n: 10,
      failure_type: null,
      family_id: null,
      family_case_cap: null,
      max_duplicate_ratio: null,
      recurrence_window: 5,
      recurrence_threshold: null,
      strategy: "top_regressions",
    },
    signal: buildSignal(),
    matched_family: {
      family_id: FAMILY_ID,
      match_kind: "dataset",
      exists: true,
      version_count: 2,
      latest_dataset_id: "qa-regressions-v2",
      current_case_count: 12,
      proposed_addition_count: 2,
      duplicate_case_count: 0,
      duplicate_ratio: 0,
      projected_case_count: 14,
      family_case_cap: null,
      cap_reached: false,
      duplicate_ratio_exceeded: false,
    },
    selected_case_count: 2,
    evidence_case_ids: ["case_reg", "case_swap"],
    preview_cases: [],
    history_context: null,
    cluster_context: [],
    escalation: null,
    lifecycle_recommendation: null,
  };
}

// ---------------------------------------------------------------------------
// Comparison inventory
// ---------------------------------------------------------------------------

export function buildComparisonInventoryItem(
  overrides: Partial<ComparisonInventoryItem> = {},
): ComparisonInventoryItem {
  return {
    reportId: REPORT_ID,
    baselineRunId: BASELINE_RUN_ID,
    candidateRunId: CANDIDATE_RUN_ID,
    dataset: DATASET_ID,
    createdAt: "2026-08-03T10:00:00Z",
    status: "completed",
    compatible: true,
    signalVerdict: "regression",
    regressionScore: 0.3,
    improvementScore: 0.1,
    netScore: -0.2,
    severity: 0.42,
    topDrivers: buildSignal().topDrivers,
    ...overrides,
  };
}

export function buildReadyComparisonInventoryState(
  comparisons: ComparisonInventoryItem[] = [buildComparisonInventoryItem()],
): ComparisonInventoryState {
  return {
    status: "ready",
    inventory: { source: SOURCE, comparisons },
    message: null,
  };
}

// ---------------------------------------------------------------------------
// Dataset families (initial state, camelCase)
// ---------------------------------------------------------------------------

export function buildDatasetFamily(
  overrides: Partial<DatasetFamilySummary> = {},
): DatasetFamilySummary {
  return {
    familyId: FAMILY_ID,
    versionCount: 2,
    latestDatasetId: "qa-regressions-v2",
    latestVersionTag: "v2",
    latestCreatedAt: "2026-08-10T09:00:00Z",
    caseCount: 12,
    sourceDatasetId: DATASET_ID,
    primaryFailureType: "hallucination",
    healthLabel: "healthy",
    recentFailRate: 0.1,
    ...overrides,
  };
}

export function buildDatasetFamiliesState(
  families: DatasetFamilySummary[] = [
    buildDatasetFamily(),
    buildDatasetFamily({
      familyId: "safety-regressions",
      versionCount: 1,
      latestDatasetId: "safety-regressions-v1",
      latestVersionTag: "v1",
      caseCount: 5,
      primaryFailureType: "refusal",
      healthLabel: "regressing",
      recentFailRate: 0.4,
    }),
  ],
): DatasetFamiliesState {
  const data: DatasetFamiliesResponse = { source: SOURCE, families };
  return { status: "ready", data, message: null };
}

// ---------------------------------------------------------------------------
// Gate (initial state, camelCase)
// ---------------------------------------------------------------------------

export function buildGateState(
  variant: "blocked" | "clear" = "blocked",
  rowOverrides: Partial<GateDecisionRow>[] = [],
): GateState {
  const blocked = variant === "blocked";
  const rows: GateDecisionRow[] = [
    {
      comparisonId: REPORT_ID,
      verdict: blocked ? "regression" : "improvement",
      action: blocked ? "block" : "allow",
      severity: 0.42,
      policyRule: "severity_above_threshold",
      blocked,
      waived: false,
      waiver: null,
      blockReason: blocked ? "signal verdict: regression" : null,
    },
    {
      comparisonId: "cmp_waived_002",
      verdict: "regression",
      action: "allow",
      severity: 0.3,
      policyRule: "severity_above_threshold",
      blocked: false,
      waived: true,
      blockReason: "signal verdict: regression",
      waiver: {
        comparisonId: "cmp_waived_002",
        reason: "known flake",
        owner: "maya",
        expiresAt: "2026-09-01",
        active: true,
      },
    },
  ];
  rowOverrides.forEach((override, index) => {
    rows[index] = { ...rows[index], ...override };
  });
  const data: GateResponse = {
    source: SOURCE,
    blocked,
    policy: buildGovernancePolicy(),
    policySource: "default",
    waiverSource: null,
    rows,
  };
  return { status: "ready", data, message: null };
}

// ---------------------------------------------------------------------------
// Comparison detail (wire payload for comparison-detail.json)
// ---------------------------------------------------------------------------

type ComparisonDetailWireOverrides = {
  signal?: ComparisonSignal;
  governanceRecommendation?: Record<string, unknown> | null;
  deltaFailureRate?: number | null;
};

export function buildComparisonDetail(
  overrides: ComparisonDetailWireOverrides = {},
): Record<string, unknown> {
  const snapshot = (failureRate: number) => ({
    attemptedCaseCount: 12,
    classifiedCaseCount: 12,
    executionErrorCount: 0,
    unclassifiedCount: 0,
    successfulModelInvocationCount: 12,
    failureRate,
    classificationCoverage: 1,
    executionSuccessRate: 1,
  });
  const caseDelta = (partial: Record<string, unknown>) => ({
    tags: ["qa"],
    baselineFailureType: null,
    candidateFailureType: null,
    baselineExpectationVerdict: null,
    candidateExpectationVerdict: null,
    baselineErrorStage: null,
    candidateErrorStage: null,
    baselineExplanation: null,
    candidateExplanation: null,
    ...partial,
  });
  return {
    source: SOURCE,
    comparison: {
      reportId: REPORT_ID,
      createdAt: "2026-08-03T10:00:00Z",
      status: "completed",
      baselineRunId: BASELINE_RUN_ID,
      candidateRunId: CANDIDATE_RUN_ID,
      dataset: DATASET_ID,
      baselineDataset: DATASET_ID,
      candidateDataset: DATASET_ID,
      compatible: true,
      reason: null,
      comparisonMode: "shared_cases",
      metricsComputedOn: "shared",
    },
    signal: overrides.signal ?? buildSignal(),
    metrics: {
      baseline: snapshot(0.2),
      candidate: snapshot(0.3),
      delta: {
        failureRate:
          overrides.deltaFailureRate !== undefined ? overrides.deltaFailureRate : 0.1,
        classificationCoverage: 0,
        executionSuccessRate: -0.05,
      },
    },
    coverage: {
      sharedCaseCount: 10,
      baselineOnlyCaseCount: 1,
      candidateOnlyCaseCount: 1,
      sharedCaseIds: ["case_reg", "case_swap", "case_fix"],
      baselineOnlyCaseIds: ["case_bonly"],
      candidateOnlyCaseIds: ["case_conly"],
    },
    transitions: {
      counts: {
        no_failure_to_failure: 1,
        failure_type_swap: 1,
        failure_to_no_failure: 1,
      },
      summary: [
        {
          transitionType: "no_failure_to_failure",
          label: "New failures",
          count: 1,
          caseIds: ["case_reg"],
        },
        {
          transitionType: "failure_type_swap",
          label: "Failure type changed",
          count: 1,
          caseIds: ["case_swap"],
        },
        {
          transitionType: "failure_to_no_failure",
          label: "Fixed",
          count: 1,
          caseIds: ["case_fix"],
        },
      ],
    },
    caseDeltas: [
      caseDelta({
        caseId: "case_fix",
        promptId: "p_fix",
        prompt: "Summarize the safety policy in one sentence.",
        transitionType: "failure_to_no_failure",
        transitionLabel: "Fixed",
        baselineFailureType: "hallucination",
        baselineExplanation: "Baseline invented a policy clause.",
      }),
      caseDelta({
        caseId: "case_reg",
        promptId: "p_reg",
        prompt: "Cite the source for the 2019 revenue figure.",
        transitionType: "no_failure_to_failure",
        transitionLabel: "New failures",
        candidateFailureType: "hallucination",
        candidateExplanation: "Model invented a citation that does not exist.",
      }),
      caseDelta({
        caseId: "case_swap",
        promptId: "p_swap",
        prompt: "Explain the refund process step by step.",
        transitionType: "failure_type_swap",
        transitionLabel: "Failure type changed",
        baselineFailureType: "refusal",
        candidateFailureType: "hallucination",
        candidateExplanation: "Answer fabricated a refund window.",
      }),
    ],
    insightReport: null,
    governanceRecommendation:
      overrides.governanceRecommendation !== undefined
        ? overrides.governanceRecommendation
        : buildGovernanceRecommendationWire(),
  };
}

// ---------------------------------------------------------------------------
// Run detail (wire payload for run-detail.json — camelCase per validateRunDetail)
// ---------------------------------------------------------------------------

function runCase(partial: Partial<RunCaseRecord> & { caseId: string }): RunCaseRecord {
  return {
    promptId: `p_${partial.caseId}`,
    prompt: `Prompt for ${partial.caseId}`,
    tags: ["qa"],
    outputText: null,
    expectation: { expectedFailure: null, observedFailure: null, verdict: null },
    classification: null,
    error: null,
    ...partial,
  };
}

export function buildRunDetail(
  runId: string = BASELINE_RUN_ID,
  overrides: Partial<RunDetail> = {},
): RunDetail {
  const candidate = runId === CANDIDATE_RUN_ID;
  const cases: RunCaseRecord[] = [
    runCase({
      caseId: "case_reg",
      promptId: "p_reg",
      prompt: "Cite the source for the 2019 revenue figure.",
      outputText: candidate
        ? "Candidate hallucinated a fake citation (Smith 2019)."
        : "Baseline answer with the correct citation.",
      expectation: {
        expectedFailure: null,
        observedFailure: candidate
          ? { failureType: "hallucination", failureSubtype: null }
          : null,
        verdict: candidate ? "mismatch" : "match",
      },
      classification: {
        failure: candidate
          ? { failureType: "hallucination", failureSubtype: "fabricated_source" }
          : { failureType: "no_failure", failureSubtype: null },
        confidence: candidate ? 0.8 : 0.9,
        explanation: candidate ? "Invented a source that does not exist." : null,
      },
    }),
    runCase({
      caseId: "case_swap",
      promptId: "p_swap",
      prompt: "Explain the refund process step by step.",
      outputText: candidate
        ? "Candidate fabricated a 90-day refund window."
        : "Baseline refused to answer the refund question.",
      expectation: { expectedFailure: null, observedFailure: null, verdict: "mismatch" },
      classification: {
        failure: candidate
          ? { failureType: "hallucination", failureSubtype: null }
          : { failureType: "refusal", failureSubtype: null },
        confidence: 0.7,
        explanation: null,
      },
    }),
    runCase({
      caseId: "case_fix",
      promptId: "p_fix",
      prompt: "Summarize the safety policy in one sentence.",
      outputText: candidate
        ? "Candidate gave a faithful one-sentence summary."
        : "Baseline invented a policy clause.",
      expectation: { expectedFailure: null, observedFailure: null, verdict: "match" },
      classification: {
        failure: candidate
          ? { failureType: "no_failure", failureSubtype: null }
          : { failureType: "hallucination", failureSubtype: null },
        confidence: 0.85,
        explanation: null,
      },
    }),
    runCase({
      caseId: "case_err",
      promptId: "p_err",
      prompt: "Translate the onboarding email to French.",
      error: {
        stage: "model_invocation",
        type: "TimeoutError",
        message: "request timed out after 30s",
      },
    }),
  ];
  return {
    source: SOURCE,
    run: {
      runId,
      dataset: DATASET_ID,
      model: candidate ? "demo-candidate" : "demo-baseline",
      createdAt: candidate ? "2026-08-02T10:00:00Z" : "2026-08-01T10:00:00Z",
      status: "completed",
      reportId: "rep_run_001",
      adapterId: "demo",
      classifierId: "heuristic-v1",
      runSeed: 7,
    },
    metrics: {
      attemptedCaseCount: 4,
      classifiedCaseCount: 3,
      executionErrorCount: 1,
      unclassifiedCount: 0,
      successfulModelInvocationCount: 3,
      failureCaseCount: 1,
      failureRate: 0.25,
      classificationCoverage: 0.75,
      executionSuccessRate: 0.75,
    },
    summary: {
      failureTypes: [
        { label: "no_failure", count: 2, share: 0.5, caseIds: ["case_reg", "case_swap"] },
        { label: "hallucination", count: 1, share: 0.25, caseIds: ["case_fix"] },
      ],
      expectationVerdicts: [
        { label: "match", count: 2, share: 0.5, caseIds: ["case_reg", "case_fix"] },
        { label: "mismatch", count: 1, share: 0.25, caseIds: ["case_swap"] },
      ],
      tagSlices: [
        {
          tag: "qa",
          attemptedCaseCount: 4,
          classifiedCaseCount: 3,
          failureCaseCount: 1,
          failureRate: 0.25,
          expectationVerdictCounts: { match: 2, mismatch: 1 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: ["case_swap"],
      notableCaseIds: ["case_swap", "case_fix"],
      allCaseIds: ["case_reg", "case_swap", "case_fix", "case_err"],
      errorCaseIds: ["case_err"],
    },
    cases,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Dataset versions (wire payload for dataset-versions.json — snake_case)
// ---------------------------------------------------------------------------

export function buildDatasetVersionsResponse(
  familyId: string = FAMILY_ID,
): Record<string, unknown> {
  const version = (n: number) => ({
    family_id: familyId,
    dataset_id: `${familyId}-v${n}`,
    version_number: n,
    version_tag: `v${n}`,
    created_at: `2026-08-0${n + 4}T09:00:00Z`,
    case_count: 10 + n,
    path: `datasets/${familyId}-v${n}.json`,
    parent_dataset_id: n > 1 ? `${familyId}-v${n - 1}` : null,
    source_comparison_id: n > 1 ? REPORT_ID : null,
    signal_verdict: n > 1 ? "regression" : null,
    severity: n > 1 ? 0.42 : null,
  });
  return {
    source: SOURCE,
    family_id: familyId,
    versions: [version(1), version(2)],
    history: null,
    lifecycle_actions: [],
    portfolio_item: null,
    portfolio_plans: [],
    plan_executions: [],
    outcomes: [],
  };
}

// ---------------------------------------------------------------------------
// Query responses (wire payloads for query.json — rows snake_case)
// ---------------------------------------------------------------------------

const QUERY_FILTERS = {
  failureType: null,
  model: null,
  dataset: null,
  runId: null,
  promptId: null,
  reportId: null,
  baselineRunId: null,
  candidateRunId: null,
  delta: null,
  aggregateBy: null,
  clusterKind: null,
  includeNonRecurring: false,
  lastN: null,
  since: null,
  until: null,
  limit: 200,
};

const QUERY_FACETS = {
  models: ["demo-baseline", "demo-candidate"],
  datasets: [DATASET_ID],
  failureTypes: ["hallucination", "refusal"],
  deltaTypes: ["no_failure_to_failure"],
};

export function buildClusterSummaryWire(): Record<string, unknown> {
  return {
    cluster_id: CLUSTER_ID,
    cluster_kind: "comparison_delta",
    label: "Hallucinated citations",
    summary: "Cases where the candidate invents sources that do not exist.",
    occurrence_count: 3,
    scope_count: 2,
    first_seen_at: "2026-08-01T00:00:00Z",
    last_seen_at: "2026-08-20T00:00:00Z",
    datasets: [DATASET_ID],
    models: ["demo-candidate"],
    failure_types: ["hallucination"],
    transition_types: ["no_failure_to_failure"],
    recent_severity: 0.42,
    representative_evidence: [],
  };
}

export function buildQueryResponse(
  mode: "cases" | "deltas" | "aggregates" | "signals" | "clusters",
  rows?: unknown[],
): Record<string, unknown> {
  const base = {
    source: SOURCE,
    mode,
    filters: QUERY_FILTERS,
    facets: QUERY_FACETS,
    insight_report: null,
  };
  if (rows) return { ...base, rows };
  switch (mode) {
    case "cases":
      return {
        ...base,
        rows: [
          {
            run_id: CANDIDATE_RUN_ID,
            dataset: DATASET_ID,
            model: "demo-candidate",
            created_at: "2026-08-02T10:00:00Z",
            case_id: "case_reg",
            prompt_id: "p_reg",
            prompt: "Cite the source for the 2019 revenue figure.",
            tags: ["qa"],
            failure_type: "hallucination",
            expectation_verdict: "mismatch",
            explanation: "Invented a source.",
            confidence: 0.8,
            error_stage: null,
          },
        ],
      };
    case "deltas":
      return {
        ...base,
        rows: [
          {
            report_id: REPORT_ID,
            created_at: "2026-08-03T10:00:00Z",
            dataset: DATASET_ID,
            case_id: "case_reg",
            prompt_id: "p_reg",
            prompt: "Cite the source for the 2019 revenue figure.",
            tags: ["qa"],
            transition_type: "no_failure_to_failure",
            transition_label: "New failures",
            delta_kind: "classification",
            baseline_run_id: BASELINE_RUN_ID,
            candidate_run_id: CANDIDATE_RUN_ID,
            baseline_model: "demo-baseline",
            candidate_model: "demo-candidate",
            baseline_failure_type: null,
            candidate_failure_type: "hallucination",
            baseline_expectation_verdict: null,
            candidate_expectation_verdict: "mismatch",
            baseline_explanation: null,
            candidate_explanation: "Model invented a citation.",
          },
        ],
      };
    case "aggregates":
      return {
        ...base,
        rows: [
          { group_key: "hallucination", group_label: "hallucination", case_count: 5 },
          { group_key: "refusal", group_label: "refusal", case_count: 2 },
        ],
      };
    case "signals":
      return {
        ...base,
        rows: [
          {
            report_id: REPORT_ID,
            created_at: "2026-08-03T10:00:00Z",
            dataset: DATASET_ID,
            baseline_run_id: BASELINE_RUN_ID,
            candidate_run_id: CANDIDATE_RUN_ID,
            baseline_model: "demo-baseline",
            candidate_model: "demo-candidate",
            status: "completed",
            compatible: true,
            signal_verdict: "regression",
            regression_score: 0.3,
            improvement_score: 0.1,
            net_score: -0.2,
            severity: 0.42,
            top_drivers: [
              {
                driver_rank: 0,
                failure_type: "hallucination",
                delta: 0.2,
                direction: "regression",
                case_ids: ["case_reg"],
              },
            ],
            governance_recommendation: null,
            portfolio_item: null,
            portfolio_plans: [],
          },
        ],
      };
    case "clusters":
      return { ...base, rows: [buildClusterSummaryWire()] };
  }
}

export function buildClusterDetailWire(): Record<string, unknown> {
  return {
    source: SOURCE,
    summary: buildClusterSummaryWire(),
    occurrences: [
      {
        cluster_id: CLUSTER_ID,
        cluster_kind: "comparison_delta",
        created_at: "2026-08-20T00:00:00Z",
        dataset_scope: null,
        dataset: DATASET_ID,
        run_id: null,
        model: null,
        report_id: REPORT_ID,
        case_id: "case_reg",
        prompt_id: "p_reg",
        prompt: "Cite the source for the 2019 revenue figure.",
        tags: ["qa"],
        failure_type: null,
        expectation_verdict: null,
        error_stage: null,
        delta_kind: "classification",
        transition_type: "no_failure_to_failure",
        baseline_run_id: BASELINE_RUN_ID,
        candidate_run_id: CANDIDATE_RUN_ID,
        baseline_model: null,
        candidate_model: null,
        baseline_failure_type: null,
        candidate_failure_type: "hallucination",
        baseline_expectation_verdict: null,
        candidate_expectation_verdict: null,
        signal_verdict: "regression",
        severity: 0.42,
        evidence_ref: {
          kind: "comparison_case",
          label: `${REPORT_ID}/case_reg`,
          run_id: null,
          report_id: REPORT_ID,
          case_id: "case_reg",
          prompt_id: "p_reg",
          section: null,
          transition_type: "no_failure_to_failure",
        },
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Dataset evolution receipt (wire payload for dataset-evolve.json — snake_case)
// ---------------------------------------------------------------------------

export function buildDatasetEvolutionWire(): Record<string, unknown> {
  return {
    source: SOURCE,
    dataset_id: "qa-regressions-v3",
    family_id: FAMILY_ID,
    version_number: 3,
    version_tag: "v3",
    parent_dataset_id: "qa-regressions-v2",
    output_path: "datasets/qa-regressions-v3.json",
    previous_case_count: 12,
    added_case_count: 2,
    selected_case_count: 2,
    duplicate_case_count: 0,
    total_case_count: 14,
    comparison_id: REPORT_ID,
    policy: {
      top_n: 10,
      failure_type: null,
      strategy: "top_regressions",
      delta_kind: "regression",
    },
    signal: buildSignal(),
    preview_cases: [
      {
        case_id: "harvest_case_1",
        prompt_id: "p_reg",
        prompt: "Cite the source for the 2019 revenue figure.",
        source_case_id: "case_reg",
        source_report_id: REPORT_ID,
        source_run_id: CANDIDATE_RUN_ID,
        driver_failure_type: "hallucination",
        driver_rank: 0,
        transition_type: "no_failure_to_failure",
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// History snapshot (wire shape for history.json)
// ---------------------------------------------------------------------------

function buildHistoryRunRowWire(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    run_id: BASELINE_RUN_ID,
    dataset: DATASET_ID,
    model: "demo-baseline",
    created_at: "2026-08-01T10:00:00Z",
    status: "completed",
    attempted_case_count: 12,
    classified_case_count: 12,
    execution_error_count: 0,
    unclassified_count: 0,
    successful_model_invocation_count: 12,
    failure_case_count: 3,
    failure_rate: 0.25,
    classification_coverage: 1,
    execution_success_rate: 1,
    ...overrides,
  };
}

export function buildHistorySnapshotWire(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    source: {
      label: SOURCE.label,
      path: SOURCE.path,
      runsPath: SOURCE.runsPath,
      reportsPath: SOURCE.reportsPath,
    },
    scope_kind: "dataset",
    scope_value: DATASET_ID,
    run_history: [
      buildHistoryRunRowWire({
        run_id: CANDIDATE_RUN_ID,
        model: "demo-candidate",
        created_at: "2026-08-02T10:00:00Z",
        failure_case_count: 4,
        failure_rate: 0.35,
      }),
      buildHistoryRunRowWire(),
    ],
    comparison_history: [
      {
        report_id: REPORT_ID,
        created_at: "2026-08-02T11:00:00Z",
        dataset: DATASET_ID,
        baseline_run_id: BASELINE_RUN_ID,
        candidate_run_id: CANDIDATE_RUN_ID,
        baseline_model: "demo-baseline",
        candidate_model: "demo-candidate",
        status: "completed",
        compatible: true,
        signal_verdict: "regression",
        regression_score: 0.42,
        improvement_score: 0.06,
        net_score: -0.36,
        severity: 0.36,
        top_drivers: [
          {
            driver_rank: 0,
            failure_type: "hallucination",
            delta: 0.1,
            direction: "regression",
            case_ids: ["case_reg"],
          },
        ],
      },
    ],
    run_trend: {
      label: "degrading",
      delta: 0.1,
      sample_count: 2,
      first_value: 0.25,
      last_value: 0.35,
      volatility: 0.05,
      volatility_label: "stable",
    },
    comparison_trend: {
      label: "flat",
      delta: 0,
      sample_count: 1,
      first_value: 0.36,
      last_value: 0.36,
      volatility: 0,
      volatility_label: "stable",
    },
    recurring_failures: [
      {
        failure_type: "hallucination",
        occurrences: 2,
        comparison_ids: [REPORT_ID],
        latest_delta: 0.1,
      },
    ],
    recurring_clusters: [],
    dataset_versions: [],
    dataset_health: null,
    ...overrides,
  };
}
