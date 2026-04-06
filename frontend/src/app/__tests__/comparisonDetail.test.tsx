import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { App } from "@/app/App";
import type {
  ArtifactShellState,
  RunDetail,
  ComparisonDetail,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";

const nativeScrollIntoView = HTMLElement.prototype.scrollIntoView;
const DEFAULT_SOURCE = {
  label: "Repo root artifact store",
  path: "/tmp/model-failure-lab",
  runsPath: "/tmp/model-failure-lab/runs",
  reportsPath: "/tmp/model-failure-lab/reports",
};
const CONFIGURED_SOURCE = {
  label: "Configured artifact store",
  path: "/tmp/external-artifacts",
  runsPath: "/tmp/external-artifacts/runs",
  reportsPath: "/tmp/external-artifacts/reports",
};

function buildSignal(
  verdict: string,
  severity: number,
  drivers: Array<{ failureType: string; delta: number; caseIds: string[] }>,
) {
  return {
    verdict,
    reason: null,
    regressionScore:
      verdict === "regression" ? severity : drivers.reduce((total, driver) => total + Math.max(driver.delta, 0), 0),
    improvementScore:
      verdict === "improvement" ? severity : drivers.reduce((total, driver) => total + Math.abs(Math.min(driver.delta, 0)), 0),
    netScore:
      verdict === "improvement"
        ? -severity
        : verdict === "regression"
          ? severity
          : 0,
    severity,
    topDrivers: drivers.map((driver, index) => ({
      driverRank: index,
      failureType: driver.failureType,
      delta: driver.delta,
      direction: driver.delta >= 0 ? "regression" : "improvement",
      caseIds: driver.caseIds,
    })),
  };
}

function buildGovernanceRecommendation(
  overrides: Partial<NonNullable<ComparisonDetail["governanceRecommendation"]>> = {},
) {
  return {
    comparisonId: "compare_alpha_to_beta",
    action: "ignore" as const,
    policyRule: "non_regression_signal",
    rationale:
      "Signal verdict is `improvement`, so the comparison does not qualify for regression-pack governance.",
    policy: {
      minimumSeverity: 0.05,
      topN: 10,
      failureType: null,
      familyId: null,
      familyCaseCap: 200,
      maxDuplicateRatio: 0.6,
      recurrenceWindow: 5,
      recurrenceThreshold: 2,
      strategy: "exact_suggested_family_then_health_guards",
    },
    signal: buildSignal("improvement", 0.25, [
      {
        failureType: "hallucination",
        delta: -0.25,
        caseIds: ["case-002"],
      },
      {
        failureType: "reasoning",
        delta: 0.125,
        caseIds: ["case-004"],
      },
    ]),
    matchedFamily: {
      familyId: "regression-reasoning-failures-v1-reasoning",
      matchKind: "suggested_new",
      exists: false,
      versionCount: 0,
      latestDatasetId: null,
      currentCaseCount: 0,
      proposedAdditionCount: 0,
      duplicateCaseCount: 0,
      duplicateRatio: 0,
      projectedCaseCount: 0,
      familyCaseCap: 200,
      capReached: false,
      duplicateRatioExceeded: false,
    },
    selectedCaseCount: 0,
    evidenceCaseIds: [],
    previewCases: [],
    historyContext: null,
    escalation: null,
    lifecycleRecommendation: null,
    ...overrides,
  };
}

function buildClusterContext(
  overrides: Partial<
    NonNullable<NonNullable<ComparisonDetail["governanceRecommendation"]>["clusterContext"]>[number]
  > = {},
) {
  return {
    clusterId: "cd_reasoning_failure_to_no_failure",
    clusterKind: "comparison_delta" as const,
    label: "reasoning · failure to no failure",
    summary:
      "Reasoning failure to no failure recurred 2 times across 2 saved comparisons in reasoning-failures-v1.",
    occurrenceCount: 2,
    scopeCount: 2,
    firstSeenAt: "2026-03-29T12:00:00Z",
    lastSeenAt: "2026-03-30T12:00:00Z",
    datasets: ["reasoning-failures-v1"],
    models: ["run_alpha→run_beta"],
    failureTypes: ["reasoning"],
    transitionTypes: ["failure_to_no_failure"],
    recentSeverity: 0.25,
    representativeEvidence: [
      {
        kind: "comparison_case" as const,
        label: "compare_alpha_to_beta:case-002",
        runId: null,
        reportId: "compare_alpha_to_beta",
        caseId: "case-002",
        promptId: "case-002",
        section: "transitions",
        transitionType: "failure_to_no_failure",
      },
    ],
    ...overrides,
  };
}

function buildReadyArtifactState(
  comparisonIds: string[],
  source = DEFAULT_SOURCE,
): ArtifactShellState {
  return {
    status: "ready",
    overview: {
      status: "ready",
      source,
      runs: {
        count: 2,
        ids: ["run_alpha", "run_beta"],
      },
      comparisons: {
        count: comparisonIds.length,
        ids: comparisonIds,
      },
      issues: [],
      message: null,
    },
  };
}

function buildReadyRunInventoryState(
  runs: NonNullable<RunInventoryState["inventory"]>["runs"] = [
    {
      runId: "run_alpha",
      dataset: "reasoning-failures-v1",
      model: "demo",
      createdAt: "2026-03-29T09:00:00Z",
      status: "completed",
    },
    {
      runId: "run_beta",
      dataset: "reasoning-failures-v1",
      model: "demo",
      createdAt: "2026-03-30T11:30:00Z",
      status: "completed",
    },
  ],
  source = DEFAULT_SOURCE,
): RunInventoryState {
  return {
    status: "ready",
    inventory: {
      source,
      runs,
    },
    message: null,
  };
}

function buildReadyComparisonInventoryState(
  source = DEFAULT_SOURCE,
): ComparisonInventoryState {
  return {
    status: "ready",
    inventory: {
      source,
      comparisons: [
        {
          reportId: "compare_alpha_to_beta",
          baselineRunId: "run_alpha",
          candidateRunId: "run_beta",
          dataset: "reasoning-failures-v1",
          createdAt: "2026-03-30T12:00:00Z",
          status: "improved",
          compatible: true,
          signalVerdict: "improvement",
          regressionScore: 0.125,
          improvementScore: 0.25,
          netScore: -0.125,
          severity: 0.25,
          topDrivers: [
            {
              driverRank: 0,
              failureType: "hallucination",
              delta: -0.25,
              direction: "improvement",
              caseIds: ["case-002"],
            },
            {
              driverRank: 1,
              failureType: "reasoning",
              delta: 0.125,
              direction: "regression",
              caseIds: ["case-004"],
            },
          ],
        },
        {
          reportId: "compare_dataset_mismatch",
          baselineRunId: "run_alpha",
          candidateRunId: "run_beta",
          dataset: null,
          createdAt: "2026-03-30T12:30:00Z",
          status: "incompatible_dataset",
          compatible: false,
          signalVerdict: "incompatible",
          regressionScore: 0,
          improvementScore: 0,
          netScore: 0,
          severity: 0,
          topDrivers: [],
        },
      ],
    },
    message: null,
  };
}

function buildCompatibleDetail(source = DEFAULT_SOURCE): ComparisonDetail {
  return {
    source,
    comparison: {
      reportId: "compare_alpha_to_beta",
      createdAt: "2026-03-30T12:00:00Z",
      status: "improved",
      baselineRunId: "run_alpha",
      candidateRunId: "run_beta",
      dataset: "reasoning-failures-v1",
      baselineDataset: null,
      candidateDataset: null,
      compatible: true,
      reason: null,
      comparisonMode: "baseline_to_candidate",
      metricsComputedOn: "shared_cases_only",
    },
    signal: buildSignal("improvement", 0.25, [
      {
        failureType: "hallucination",
        delta: -0.25,
        caseIds: ["case-002"],
      },
      {
        failureType: "reasoning",
        delta: 0.125,
        caseIds: ["case-004"],
      },
    ]),
    metrics: {
      baseline: {
        attemptedCaseCount: 8,
        classifiedCaseCount: 8,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 8,
        failureRate: 0.5,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      candidate: {
        attemptedCaseCount: 8,
        classifiedCaseCount: 8,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 8,
        failureRate: 0.25,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      delta: {
        failureRate: -0.25,
        classificationCoverage: 0,
        executionSuccessRate: 0,
      },
    },
    coverage: {
      sharedCaseCount: 8,
      baselineOnlyCaseCount: 1,
      candidateOnlyCaseCount: 0,
      sharedCaseIds: ["case-002", "case-003"],
      baselineOnlyCaseIds: ["case-001"],
      candidateOnlyCaseIds: [],
    },
    transitions: {
      counts: {
        improvements: 1,
        regressions: 1,
        failureTypeSwaps: 0,
        errorChanges: 0,
      },
      summary: [
        {
          transitionType: "failure_to_no_failure",
          label: "failure -> no_failure",
          count: 1,
          caseIds: ["case-002"],
        },
        {
          transitionType: "no_failure_to_failure",
          label: "no_failure -> failure",
          count: 1,
          caseIds: ["case-004"],
        },
      ],
    },
    caseDeltas: [
      {
        caseId: "case-002",
        promptId: "case-002",
        prompt: "Answer using only the supplied source snippet.",
        tags: ["core", "factuality"],
        transitionType: "failure_to_no_failure",
        transitionLabel: "failure -> no_failure",
        baselineFailureType: "hallucination",
        candidateFailureType: "no_failure",
        baselineExpectationVerdict: "unexpected_failure",
        candidateExpectationVerdict: "no_failure_as_expected",
        baselineErrorStage: null,
        candidateErrorStage: null,
        baselineExplanation: "Unsupported factual framing detected.",
        candidateExplanation: "No heuristic failure signal detected.",
      },
      {
        caseId: "case-004",
        promptId: "case-004",
        prompt: "Use only the provided evidence bullets.",
        tags: ["extended"],
        transitionType: "no_failure_to_failure",
        transitionLabel: "no_failure -> failure",
        baselineFailureType: "no_failure",
        candidateFailureType: "reasoning",
        baselineExpectationVerdict: "no_failure_as_expected",
        candidateExpectationVerdict: "unexpected_failure",
        baselineErrorStage: null,
        candidateErrorStage: null,
        baselineExplanation: "No heuristic failure signal detected.",
        candidateExplanation: "Reasoning chain diverged from the rubric.",
      },
    ],
    insightReport: {
      analysisMode: "heuristic",
      sourceKind: "comparison",
      title: "Comparison insight report",
      summary: "Comparison compare_alpha_to_beta. improvement drives most of the matched comparison deltas.",
      generatedBy: "heuristic_v1",
      sampling: {
        totalMatches: 2,
        sampledMatches: 2,
        sampleLimit: 12,
        truncated: false,
        strategy: "ranked_representative_groups",
      },
      patterns: [
        {
          kind: "delta_kind",
          label: "improvement",
          summary: "improvement drives most of the matched comparison deltas (1 cases).",
          groupKey: "improvement",
          count: 1,
          share: 0.5,
          evidenceRefs: [
            {
              kind: "comparison_case",
              label: "compare_alpha_to_beta:case-002",
              runId: null,
              reportId: "compare_alpha_to_beta",
              caseId: "case-002",
              promptId: "case-002",
              section: "transitions",
              transitionType: "failure_to_no_failure",
            },
          ],
        },
      ],
      anomalies: [
        {
          kind: "outlier_delta",
          label: "case-004",
          summary: "case-004 remains a low-frequency regression outlier.",
          groupKey: "case-004",
          count: 1,
          share: 0.5,
          evidenceRefs: [
            {
              kind: "comparison_case",
              label: "compare_alpha_to_beta:case-004",
              runId: null,
              reportId: "compare_alpha_to_beta",
              caseId: "case-004",
              promptId: "case-004",
              section: "transitions",
              transitionType: "no_failure_to_failure",
            },
          ],
        },
      ],
      evidenceLinks: [
        {
          kind: "comparison_case",
          label: "compare_alpha_to_beta:case-002",
          runId: null,
          reportId: "compare_alpha_to_beta",
          caseId: "case-002",
          promptId: "case-002",
          section: "transitions",
          transitionType: "failure_to_no_failure",
        },
        {
          kind: "comparison_case",
          label: "compare_alpha_to_beta:case-004",
          runId: null,
          reportId: "compare_alpha_to_beta",
          caseId: "case-004",
          promptId: "case-004",
          section: "transitions",
          transitionType: "no_failure_to_failure",
        },
      ],
    },
    governanceRecommendation: buildGovernanceRecommendation(),
  };
}

function buildIncompatibleDetail(): ComparisonDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    comparison: {
      reportId: "compare_dataset_mismatch",
      createdAt: "2026-03-30T12:30:00Z",
      status: "incompatible_dataset",
      baselineRunId: "run_alpha",
      candidateRunId: "run_beta",
      dataset: null,
      baselineDataset: "reasoning-failures-v1",
      candidateDataset: "hallucination-failures-v1",
      compatible: false,
      reason: "dataset_mismatch",
      comparisonMode: "baseline_to_candidate",
      metricsComputedOn: null,
    },
    signal: {
      verdict: "incompatible",
      reason: "dataset_mismatch",
      regressionScore: 0,
      improvementScore: 0,
      netScore: 0,
      severity: 0,
      topDrivers: [],
    },
    metrics: {
      baseline: {
        attemptedCaseCount: 10,
        classifiedCaseCount: 10,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 10,
        failureRate: 0.4,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      candidate: {
        attemptedCaseCount: 10,
        classifiedCaseCount: 10,
        executionErrorCount: 0,
        unclassifiedCount: 0,
        successfulModelInvocationCount: 10,
        failureRate: 0.2,
        classificationCoverage: 1,
        executionSuccessRate: 1,
      },
      delta: {
        failureRate: null,
        classificationCoverage: null,
        executionSuccessRate: null,
      },
    },
    coverage: {
      sharedCaseCount: 0,
      baselineOnlyCaseCount: 1,
      candidateOnlyCaseCount: 1,
      sharedCaseIds: [],
      baselineOnlyCaseIds: ["case-001"],
      candidateOnlyCaseIds: ["case-101"],
    },
    transitions: {
      counts: {
        improvements: 0,
        regressions: 0,
        failureTypeSwaps: 0,
        errorChanges: 0,
      },
      summary: [],
    },
    caseDeltas: [],
    insightReport: null,
    governanceRecommendation: {
      ...buildGovernanceRecommendation({
        comparisonId: "compare_dataset_mismatch",
        action: "ignore",
        policyRule: "incompatible_signal",
        rationale:
          "Saved comparison is incompatible, so governance cannot create or evolve a regression family from it.",
        signal: {
          verdict: "incompatible",
          reason: "dataset_mismatch",
          regressionScore: 0,
          improvementScore: 0,
          netScore: 0,
          severity: 0,
          topDrivers: [],
        },
        matchedFamily: {
          familyId: "regression-comparison-general",
          matchKind: "suggested_new",
          exists: false,
          versionCount: 0,
          latestDatasetId: null,
          currentCaseCount: 0,
          proposedAdditionCount: 0,
          duplicateCaseCount: 0,
          duplicateRatio: 0,
          projectedCaseCount: 0,
          familyCaseCap: 200,
          capReached: false,
          duplicateRatioExceeded: false,
        },
      }),
    },
  };
}

function serializeComparisonDetail(detail: ComparisonDetail): Record<string, unknown> {
  return {
    ...detail,
    signal: {
      verdict: detail.signal.verdict,
      reason: detail.signal.reason,
      regression_score: detail.signal.regressionScore,
      improvement_score: detail.signal.improvementScore,
      net_score: detail.signal.netScore,
      severity: detail.signal.severity,
      top_drivers: detail.signal.topDrivers.map((driver) => ({
        driver_rank: driver.driverRank,
        failure_type: driver.failureType,
        delta: driver.delta,
        direction: driver.direction,
        case_ids: driver.caseIds,
      })),
    },
    insightReport:
      detail.insightReport === null
        ? null
        : {
            analysis_mode: detail.insightReport.analysisMode,
            source_kind: detail.insightReport.sourceKind,
            title: detail.insightReport.title,
            summary: detail.insightReport.summary,
            generated_by: detail.insightReport.generatedBy,
            sampling: {
              total_matches: detail.insightReport.sampling.totalMatches,
              sampled_matches: detail.insightReport.sampling.sampledMatches,
              sample_limit: detail.insightReport.sampling.sampleLimit,
              truncated: detail.insightReport.sampling.truncated,
              strategy: detail.insightReport.sampling.strategy,
            },
            patterns: detail.insightReport.patterns.map((pattern) => ({
              kind: pattern.kind,
              label: pattern.label,
              summary: pattern.summary,
              group_key: pattern.groupKey,
              count: pattern.count,
              share: pattern.share,
              evidence_refs: pattern.evidenceRefs.map((reference) => ({
                kind: reference.kind,
                label: reference.label,
                run_id: reference.runId,
                report_id: reference.reportId,
                case_id: reference.caseId,
                prompt_id: reference.promptId,
                section: reference.section,
                transition_type: reference.transitionType,
              })),
            })),
            anomalies: detail.insightReport.anomalies.map((pattern) => ({
              kind: pattern.kind,
              label: pattern.label,
              summary: pattern.summary,
              group_key: pattern.groupKey,
              count: pattern.count,
              share: pattern.share,
              evidence_refs: pattern.evidenceRefs.map((reference) => ({
                kind: reference.kind,
                label: reference.label,
                run_id: reference.runId,
                report_id: reference.reportId,
                case_id: reference.caseId,
                prompt_id: reference.promptId,
                section: reference.section,
                transition_type: reference.transitionType,
              })),
            })),
            evidence_links: detail.insightReport.evidenceLinks.map((reference) => ({
              kind: reference.kind,
              label: reference.label,
              run_id: reference.runId,
              report_id: reference.reportId,
              case_id: reference.caseId,
              prompt_id: reference.promptId,
              section: reference.section,
              transition_type: reference.transitionType,
            })),
          },
    governanceRecommendation:
      detail.governanceRecommendation === null
        ? null
        : {
            comparison_id: detail.governanceRecommendation.comparisonId,
            action: detail.governanceRecommendation.action,
            policy_rule: detail.governanceRecommendation.policyRule,
            rationale: detail.governanceRecommendation.rationale,
            policy: {
              minimum_severity: detail.governanceRecommendation.policy.minimumSeverity,
              top_n: detail.governanceRecommendation.policy.topN,
              failure_type: detail.governanceRecommendation.policy.failureType,
              family_id: detail.governanceRecommendation.policy.familyId,
              family_case_cap: detail.governanceRecommendation.policy.familyCaseCap,
              max_duplicate_ratio: detail.governanceRecommendation.policy.maxDuplicateRatio,
              recurrence_window: detail.governanceRecommendation.policy.recurrenceWindow,
              recurrence_threshold: detail.governanceRecommendation.policy.recurrenceThreshold,
              strategy: detail.governanceRecommendation.policy.strategy,
            },
            signal: {
              verdict: detail.governanceRecommendation.signal.verdict,
              reason: detail.governanceRecommendation.signal.reason,
              regression_score: detail.governanceRecommendation.signal.regressionScore,
              improvement_score: detail.governanceRecommendation.signal.improvementScore,
              net_score: detail.governanceRecommendation.signal.netScore,
              severity: detail.governanceRecommendation.signal.severity,
              top_drivers: detail.governanceRecommendation.signal.topDrivers.map((driver) => ({
                driver_rank: driver.driverRank,
                failure_type: driver.failureType,
                delta: driver.delta,
                direction: driver.direction,
                case_ids: driver.caseIds,
              })),
            },
            matched_family: {
              family_id: detail.governanceRecommendation.matchedFamily.familyId,
              match_kind: detail.governanceRecommendation.matchedFamily.matchKind,
              exists: detail.governanceRecommendation.matchedFamily.exists,
              version_count: detail.governanceRecommendation.matchedFamily.versionCount,
              latest_dataset_id: detail.governanceRecommendation.matchedFamily.latestDatasetId,
              current_case_count: detail.governanceRecommendation.matchedFamily.currentCaseCount,
              proposed_addition_count:
                detail.governanceRecommendation.matchedFamily.proposedAdditionCount,
              duplicate_case_count:
                detail.governanceRecommendation.matchedFamily.duplicateCaseCount,
              duplicate_ratio: detail.governanceRecommendation.matchedFamily.duplicateRatio,
              projected_case_count:
                detail.governanceRecommendation.matchedFamily.projectedCaseCount,
              family_case_cap: detail.governanceRecommendation.matchedFamily.familyCaseCap,
              cap_reached: detail.governanceRecommendation.matchedFamily.capReached,
              duplicate_ratio_exceeded:
                detail.governanceRecommendation.matchedFamily.duplicateRatioExceeded,
            },
            selected_case_count: detail.governanceRecommendation.selectedCaseCount,
            evidence_case_ids: detail.governanceRecommendation.evidenceCaseIds,
            preview_cases: detail.governanceRecommendation.previewCases.map((entry) => ({
              case_id: entry.caseId,
              prompt_id: entry.promptId,
              prompt: entry.prompt,
              source_case_id: entry.sourceCaseId,
              source_report_id: entry.sourceReportId,
              source_run_id: entry.sourceRunId,
              driver_failure_type: entry.driverFailureType,
              driver_rank: entry.driverRank,
              transition_type: entry.transitionType,
            })),
            history_context:
              detail.governanceRecommendation.historyContext === null
                ? null
                : {
                    scope_kind: detail.governanceRecommendation.historyContext.scopeKind,
                    scope_value: detail.governanceRecommendation.historyContext.scopeValue,
                    recent_comparison_count:
                      detail.governanceRecommendation.historyContext.recentComparisonCount,
                    recent_regression_count:
                      detail.governanceRecommendation.historyContext.recentRegressionCount,
                    comparison_trend: {
                      label: detail.governanceRecommendation.historyContext.comparisonTrend.label,
                      delta: detail.governanceRecommendation.historyContext.comparisonTrend.delta,
                      sample_count:
                        detail.governanceRecommendation.historyContext.comparisonTrend.sampleCount,
                      first_value:
                        detail.governanceRecommendation.historyContext.comparisonTrend.firstValue,
                      last_value:
                        detail.governanceRecommendation.historyContext.comparisonTrend.lastValue,
                      volatility:
                        detail.governanceRecommendation.historyContext.comparisonTrend.volatility,
                      volatility_label:
                        detail.governanceRecommendation.historyContext.comparisonTrend.volatilityLabel,
                    },
                    candidate_run_trend:
                      detail.governanceRecommendation.historyContext.candidateRunTrend === null
                        ? null
                        : {
                            label: detail.governanceRecommendation.historyContext.candidateRunTrend.label,
                            delta: detail.governanceRecommendation.historyContext.candidateRunTrend.delta,
                            sample_count:
                              detail.governanceRecommendation.historyContext.candidateRunTrend.sampleCount,
                            first_value:
                              detail.governanceRecommendation.historyContext.candidateRunTrend.firstValue,
                            last_value:
                              detail.governanceRecommendation.historyContext.candidateRunTrend.lastValue,
                            volatility:
                              detail.governanceRecommendation.historyContext.candidateRunTrend.volatility,
                            volatility_label:
                              detail.governanceRecommendation.historyContext.candidateRunTrend.volatilityLabel,
                          },
                    recurring_failures:
                      detail.governanceRecommendation.historyContext.recurringFailures.map(
                        (pattern) => ({
                          failure_type: pattern.failureType,
                          occurrences: pattern.occurrences,
                          comparison_ids: pattern.comparisonIds,
                          latest_delta: pattern.latestDelta,
                        }),
                      ),
                    recurring_clusters:
                      detail.governanceRecommendation.historyContext.recurringClusters.map(
                        (cluster) => ({
                          cluster_id: cluster.clusterId,
                          cluster_kind: cluster.clusterKind,
                          label: cluster.label,
                          summary: cluster.summary,
                          occurrence_count: cluster.occurrenceCount,
                          scope_count: cluster.scopeCount,
                          first_seen_at: cluster.firstSeenAt,
                          last_seen_at: cluster.lastSeenAt,
                          datasets: cluster.datasets,
                          models: cluster.models,
                          failure_types: cluster.failureTypes,
                          transition_types: cluster.transitionTypes,
                          recent_severity: cluster.recentSeverity,
                          representative_evidence: cluster.representativeEvidence.map(
                            (reference) => ({
                              kind: reference.kind,
                              label: reference.label,
                              run_id: reference.runId,
                              report_id: reference.reportId,
                              case_id: reference.caseId,
                              prompt_id: reference.promptId,
                              section: reference.section,
                              transition_type: reference.transitionType,
                            }),
                          ),
                        }),
                      ),
                    recent_comparisons:
                      detail.governanceRecommendation.historyContext.recentComparisons.map(
                        (row) => ({
                          report_id: row.reportId,
                          created_at: row.createdAt,
                          dataset: row.dataset,
                          baseline_run_id: row.baselineRunId,
                          candidate_run_id: row.candidateRunId,
                          baseline_model: row.baselineModel,
                          candidate_model: row.candidateModel,
                          status: row.status,
                          compatible: row.compatible,
                          signal_verdict: row.signalVerdict,
                          regression_score: row.regressionScore,
                          improvement_score: row.improvementScore,
                          net_score: row.netScore,
                          severity: row.severity,
                          top_drivers: row.topDrivers.map((driver) => ({
                            driver_rank: driver.driverRank,
                            failure_type: driver.failureType,
                            delta: driver.delta,
                            direction: driver.direction,
                            case_ids: driver.caseIds,
                          })),
                        }),
                      ),
                    family_health:
                      detail.governanceRecommendation.historyContext.familyHealth === null
                        ? null
                        : {
                            family_id: detail.governanceRecommendation.historyContext.familyHealth.familyId,
                            health_label:
                              detail.governanceRecommendation.historyContext.familyHealth.healthLabel,
                            trend: {
                              label:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.label,
                              delta:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.delta,
                              sample_count:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.sampleCount,
                              first_value:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.firstValue,
                              last_value:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.lastValue,
                              volatility:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.volatility,
                              volatility_label:
                                detail.governanceRecommendation.historyContext.familyHealth.trend.volatilityLabel,
                            },
                            version_count:
                              detail.governanceRecommendation.historyContext.familyHealth.versionCount,
                            evaluation_run_count:
                              detail.governanceRecommendation.historyContext.familyHealth.evaluationRunCount,
                            recent_fail_rate:
                              detail.governanceRecommendation.historyContext.familyHealth.recentFailRate,
                            previous_fail_rate:
                              detail.governanceRecommendation.historyContext.familyHealth.previousFailRate,
                            latest_dataset_id:
                              detail.governanceRecommendation.historyContext.familyHealth.latestDatasetId,
                            latest_version_tag:
                              detail.governanceRecommendation.historyContext.familyHealth.latestVersionTag,
                            latest_created_at:
                              detail.governanceRecommendation.historyContext.familyHealth.latestCreatedAt,
                            source_dataset_id:
                              detail.governanceRecommendation.historyContext.familyHealth.sourceDatasetId,
                            primary_failure_type:
                              detail.governanceRecommendation.historyContext.familyHealth.primaryFailureType,
                          },
                  },
            cluster_context:
              detail.governanceRecommendation.clusterContext?.map((cluster) => ({
                cluster_id: cluster.clusterId,
                cluster_kind: cluster.clusterKind,
                label: cluster.label,
                summary: cluster.summary,
                occurrence_count: cluster.occurrenceCount,
                scope_count: cluster.scopeCount,
                first_seen_at: cluster.firstSeenAt,
                last_seen_at: cluster.lastSeenAt,
                datasets: cluster.datasets,
                models: cluster.models,
                failure_types: cluster.failureTypes,
                transition_types: cluster.transitionTypes,
                recent_severity: cluster.recentSeverity,
                representative_evidence: cluster.representativeEvidence.map((reference) => ({
                  kind: reference.kind,
                  label: reference.label,
                  run_id: reference.runId,
                  report_id: reference.reportId,
                  case_id: reference.caseId,
                  prompt_id: reference.promptId,
                  section: reference.section,
                  transition_type: reference.transitionType,
                })),
              })) ?? [],
            escalation:
              detail.governanceRecommendation.escalation === null
              || detail.governanceRecommendation.escalation === undefined
                ? null
                : {
                    status: detail.governanceRecommendation.escalation.status,
                    score: detail.governanceRecommendation.escalation.score,
                    severity_band: detail.governanceRecommendation.escalation.severityBand,
                    reason: detail.governanceRecommendation.escalation.reason,
                    recent_regression_count:
                      detail.governanceRecommendation.escalation.recentRegressionCount,
                    recurring_cluster_count:
                      detail.governanceRecommendation.escalation.recurringClusterCount,
                    family_health_label:
                      detail.governanceRecommendation.escalation.familyHealthLabel,
                  },
            lifecycle_recommendation:
              detail.governanceRecommendation.lifecycleRecommendation === null
              || detail.governanceRecommendation.lifecycleRecommendation === undefined
                ? null
                : {
                    family_id: detail.governanceRecommendation.lifecycleRecommendation.familyId,
                    action: detail.governanceRecommendation.lifecycleRecommendation.action,
                    health_condition:
                      detail.governanceRecommendation.lifecycleRecommendation.healthCondition,
                    rationale: detail.governanceRecommendation.lifecycleRecommendation.rationale,
                    target_family_id:
                      detail.governanceRecommendation.lifecycleRecommendation.targetFamilyId,
                    related_family_ids:
                      detail.governanceRecommendation.lifecycleRecommendation.relatedFamilyIds,
                    source_dataset_id:
                      detail.governanceRecommendation.lifecycleRecommendation.sourceDatasetId,
                    primary_failure_type:
                      detail.governanceRecommendation.lifecycleRecommendation.primaryFailureType,
                    latest_dataset_id:
                      detail.governanceRecommendation.lifecycleRecommendation.latestDatasetId,
                    version_count:
                      detail.governanceRecommendation.lifecycleRecommendation.versionCount,
                    evaluation_run_count:
                      detail.governanceRecommendation.lifecycleRecommendation.evaluationRunCount,
                    recent_fail_rate:
                      detail.governanceRecommendation.lifecycleRecommendation.recentFailRate,
                    projected_case_count:
                      detail.governanceRecommendation.lifecycleRecommendation.projectedCaseCount,
                  },
          },
  };
}

function mockComparisonDetail(detail: ComparisonDetail) {
  const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes(`/__failure_lab__/artifacts/comparison-detail.json?reportId=${detail.comparison.reportId}`)) {
        return {
          ok: true,
          status: 200,
          json: async () => serializeComparisonDetail(detail),
        } as Response;
      }

      if (url.includes("/__failure_lab__/artifacts/dataset-versions.json")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            source: DEFAULT_SOURCE,
            family_id: "regression-reasoning-failures-v1-reasoning",
            versions: [],
            lifecycle_actions: [],
          }),
        } as Response;
      }

      if (url.includes("/__failure_lab__/artifacts/regression-pack.json")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            source: DEFAULT_SOURCE,
            dataset_id: "regression-reasoning-failures-v1-reasoning-draft",
            lifecycle: "draft",
            comparison_id: "compare_alpha_to_beta",
            suggested_family_id: "regression-reasoning-failures-v1-reasoning",
            output_path:
              "datasets/harvested/regression-reasoning-failures-v1-reasoning-draft.json",
            selected_case_count: 1,
            policy: {
              top_n: 10,
              failure_type: null,
              strategy: "top_signal_driver_cases",
              delta_kind: "regression",
            },
            signal: {
              verdict: detail.signal.verdict,
              reason: detail.signal.reason,
              regression_score: detail.signal.regressionScore,
              improvement_score: detail.signal.improvementScore,
              net_score: detail.signal.netScore,
              severity: detail.signal.severity,
              top_drivers: detail.signal.topDrivers.map((driver) => ({
                driver_rank: driver.driverRank,
                failure_type: driver.failureType,
                delta: driver.delta,
                direction: driver.direction,
                case_ids: driver.caseIds,
              })),
            },
            preview_cases: [
              {
                case_id: "regression-pack-case-001",
                prompt_id: "case-004",
                prompt: "Use only the provided evidence bullets.",
                source_case_id: "case-004",
                source_report_id: "compare_alpha_to_beta",
                source_run_id: "run_beta",
                driver_failure_type: "reasoning",
                driver_rank: 1,
                transition_type: "no_failure_to_failure",
              },
            ],
          }),
        } as Response;
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({ message: `Unexpected request: ${url}` }),
      } as Response;
    });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function mockComparisonDetailWithVersionHistory(detail: ComparisonDetail) {
  let versions: Array<{
    family_id: string;
    dataset_id: string;
    version_number: number;
    version_tag: string;
    created_at: string;
    case_count: number;
    path: string;
    parent_dataset_id: string | null;
    source_comparison_id: string;
    signal_verdict: string;
    severity: number;
  }> = [
    {
      family_id: "regression-reasoning-failures-v1-reasoning",
      dataset_id: "regression-reasoning-failures-v1-reasoning-v1",
      version_number: 1,
      version_tag: "v1",
      created_at: "2026-04-03T11:00:00Z",
      case_count: 1,
      path: "datasets/harvested/regression-reasoning-failures-v1-reasoning-v1.json",
      parent_dataset_id: null,
      source_comparison_id: "compare_alpha_to_beta",
      signal_verdict: "improvement",
      severity: 0.25,
    },
  ];

  const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes(`/__failure_lab__/artifacts/comparison-detail.json?reportId=${detail.comparison.reportId}`)) {
        return {
          ok: true,
          status: 200,
          json: async () => serializeComparisonDetail(detail),
        } as Response;
      }

      if (url.includes("/__failure_lab__/artifacts/dataset-versions.json")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            source: DEFAULT_SOURCE,
            family_id: "regression-reasoning-failures-v1-reasoning",
            versions,
            lifecycle_actions: [],
            portfolio_item: {
              family_id: "regression-reasoning-failures-v1-reasoning",
              priority_rank: 1,
              priority_band: "high",
              priority_score: 48.5,
              actionability: "actionable",
              rationale:
                "lifecycle=prune, health=stable, escalation=elevated (0.310), recent_regressions=2, recurring_clusters=1",
              lifecycle_action: "prune",
              health_condition: "overgrown",
              health_label: "stable",
              trend_label: "stable",
              version_count: versions.length,
              latest_dataset_id: versions[versions.length - 1]?.dataset_id ?? "regression-reasoning-failures-v1-reasoning-v1",
              latest_version_tag: versions[versions.length - 1]?.version_tag ?? "v1",
              latest_comparison_id: "compare_alpha_to_beta",
              source_dataset_id: "reasoning-failures-v1",
              primary_failure_type: "reasoning",
              recent_fail_rate: 0.25,
              projected_case_count: 12,
              escalation_status: "elevated",
              escalation_score: 0.31,
              recent_regression_count: 2,
              recurring_cluster_count: 1,
              target_family_id: null,
              related_family_ids: [],
              comparison_refs: [
                {
                  comparison_id: "compare_alpha_to_beta",
                  created_at: "2026-04-03T11:10:00Z",
                  dataset: "reasoning-failures-v1",
                  baseline_model: "model-alpha",
                  candidate_model: "model-beta",
                  severity: 0.25,
                  signal_verdict: "regression",
                  recurring_cluster_ids: ["cluster_reasoning_failure"],
                },
              ],
              cluster_ids: ["cluster_reasoning_failure"],
              datasets: ["reasoning-failures-v1"],
              models: ["model-alpha", "model-beta"],
              active_lifecycle_action_id: null,
              active_lifecycle_action: null,
              active_lifecycle_condition: null,
              active_lifecycle_applied_at: null,
            },
            portfolio_plans: [
              {
                plan_id: "portfolio-plan-fixture",
                created_at: "2026-04-05T14:00:00Z",
                status: "draft",
                rationale: "Saved deterministic portfolio draft covering one planning unit and one family action.",
                family_ids: ["regression-reasoning-failures-v1-reasoning"],
                datasets: ["reasoning-failures-v1"],
                models: ["model-alpha", "model-beta"],
                failure_types: ["reasoning"],
                priority_bands: ["high"],
                units: [
                  {
                    unit_id: "family:regression-reasoning-failures-v1-reasoning",
                    unit_kind: "family_review",
                    priority_band: "high",
                    priority_score: 48.5,
                    rationale: "Family remains a standalone review unit in the current portfolio queue.",
                    family_ids: ["regression-reasoning-failures-v1-reasoning"],
                    comparison_ids: ["compare_alpha_to_beta"],
                    cluster_ids: ["cluster_reasoning_failure"],
                    members: [
                      {
                        family_id: "regression-reasoning-failures-v1-reasoning",
                        priority_rank: 1,
                        priority_band: "high",
                        priority_score: 48.5,
                        actionability: "actionable",
                        lifecycle_action: "prune",
                        health_condition: "overgrown",
                        version_count: versions.length,
                        source_dataset_id: "reasoning-failures-v1",
                        primary_failure_type: "reasoning",
                        latest_dataset_id: versions[versions.length - 1]?.dataset_id ?? "regression-reasoning-failures-v1-reasoning-v1",
                        projected_case_count: 12,
                        recent_fail_rate: 0.25,
                        datasets: ["reasoning-failures-v1"],
                        models: ["model-alpha", "model-beta"],
                        target_family_id: null,
                        related_family_ids: [],
                      },
                    ],
                  },
                ],
                actions: [
                  {
                    family_id: "regression-reasoning-failures-v1-reasoning",
                    action: "prune",
                    health_condition: "overgrown",
                    rationale: "Family remains a standalone review unit in the current portfolio queue.",
                    priority_rank: 1,
                    priority_band: "high",
                    priority_score: 48.5,
                    version_count: versions.length,
                    source_dataset_id: "reasoning-failures-v1",
                    primary_failure_type: "reasoning",
                    latest_dataset_id: versions[versions.length - 1]?.dataset_id ?? "regression-reasoning-failures-v1-reasoning-v1",
                    projected_case_count: 12,
                    target_family_id: null,
                    related_family_ids: [],
                    dependency_family_ids: [],
                    comparison_ids: ["compare_alpha_to_beta"],
                    cluster_ids: ["cluster_reasoning_failure"],
                    datasets: ["reasoning-failures-v1"],
                    models: ["model-alpha", "model-beta"],
                    recent_fail_rate: 0.25,
                  },
                ],
                impact: {
                  affected_family_count: 1,
                  action_count: 1,
                  projected_case_count: 12,
                  action_counts: {
                    keep: 0,
                    prune: 1,
                    merge_candidate: 0,
                    retire: 0,
                  },
                },
              },
            ],
            history: {
              scope_kind: "family",
              scope_value: "regression-reasoning-failures-v1-reasoning",
              run_history: [],
              comparison_history: [],
              run_trend: null,
              comparison_trend: null,
              recurring_failures: [],
              dataset_versions: versions,
              dataset_health: {
                family_id: "regression-reasoning-failures-v1-reasoning",
                health_label: "stable",
                trend: {
                  label: "stable",
                  delta: 0,
                  sample_count: 2,
                  first_value: 0.25,
                  last_value: 0.25,
                  volatility: 0,
                  volatility_label: "low",
                },
                version_count: versions.length,
                evaluation_run_count: 2,
                recent_fail_rate: 0.25,
                previous_fail_rate: 0.25,
                latest_dataset_id: versions[versions.length - 1]?.dataset_id ?? null,
                latest_version_tag: versions[versions.length - 1]?.version_tag ?? null,
                latest_created_at: versions[versions.length - 1]?.created_at ?? null,
                source_dataset_id: "reasoning-failures-v1",
                primary_failure_type: "reasoning",
              },
            },
          }),
        } as Response;
      }

      if (url.includes("/__failure_lab__/artifacts/dataset-evolve.json")) {
        versions = [
          ...versions,
          {
            family_id: "regression-reasoning-failures-v1-reasoning",
            dataset_id: "regression-reasoning-failures-v1-reasoning-v2",
            version_number: 2,
            version_tag: "v2",
            created_at: "2026-04-04T09:30:00Z",
            case_count: 2,
            path: "datasets/harvested/regression-reasoning-failures-v1-reasoning-v2.json",
            parent_dataset_id: "regression-reasoning-failures-v1-reasoning-v1",
            source_comparison_id: "compare_alpha_to_beta",
            signal_verdict: "improvement",
            severity: 0.25,
          },
        ];
        return {
          ok: true,
          status: 200,
          json: async () => ({
            source: DEFAULT_SOURCE,
            dataset_id: "regression-reasoning-failures-v1-reasoning-v2",
            family_id: "regression-reasoning-failures-v1-reasoning",
            version_number: 2,
            version_tag: "v2",
            parent_dataset_id: "regression-reasoning-failures-v1-reasoning-v1",
            output_path:
              "datasets/harvested/regression-reasoning-failures-v1-reasoning-v2.json",
            previous_case_count: 1,
            added_case_count: 1,
            selected_case_count: 1,
            duplicate_case_count: 0,
            total_case_count: 2,
            comparison_id: "compare_alpha_to_beta",
            policy: {
              top_n: 10,
              failure_type: null,
              strategy: "top_signal_driver_cases",
              delta_kind: "regression",
            },
            signal: {
              verdict: detail.signal.verdict,
              reason: detail.signal.reason,
              regression_score: detail.signal.regressionScore,
              improvement_score: detail.signal.improvementScore,
              net_score: detail.signal.netScore,
              severity: detail.signal.severity,
              top_drivers: detail.signal.topDrivers.map((driver) => ({
                driver_rank: driver.driverRank,
                failure_type: driver.failureType,
                delta: driver.delta,
                direction: driver.direction,
                case_ids: driver.caseIds,
              })),
            },
            preview_cases: [
              {
                case_id: "case-004",
                prompt_id: "case-004",
                prompt: "Use only the provided evidence bullets.",
                source_case_id: "case-004",
                source_report_id: "compare_alpha_to_beta",
                source_run_id: "run_beta",
                driver_failure_type: "reasoning",
                driver_rank: 1,
                transition_type: "no_failure_to_failure",
              },
            ],
          }),
        } as Response;
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({ message: `Unexpected request: ${url}` }),
      } as Response;
    });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function buildLinkedRunDetail(runId: string, dataset: string): RunDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    run: {
      runId,
      dataset,
      model: "demo",
      createdAt: "2026-03-30T12:10:00Z",
      status: "completed",
      reportId: `${runId}_report`,
      adapterId: "demo",
      classifierId: "heuristic_v1",
      runSeed: 17,
    },
    metrics: {
      attemptedCaseCount: 4,
      classifiedCaseCount: 4,
      executionErrorCount: 0,
      unclassifiedCount: 0,
      successfulModelInvocationCount: 4,
      failureCaseCount: 1,
      failureRate: 0.25,
      classificationCoverage: 1,
      executionSuccessRate: 1,
    },
    summary: {
      failureTypes: [
        { label: "hallucination", count: 1, share: 0.25, caseIds: ["case-002"] },
      ],
      expectationVerdicts: [
        { label: "unexpected_failure", count: 1, share: 0.25, caseIds: ["case-002"] },
      ],
      tagSlices: [
        {
          tag: "core",
          attemptedCaseCount: 4,
          classifiedCaseCount: 4,
          failureCaseCount: 1,
          failureRate: 0.25,
          expectationVerdictCounts: { unexpected_failure: 1 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: ["case-002"],
      notableCaseIds: ["case-002"],
      allCaseIds: ["case-001", "case-002"],
      errorCaseIds: [],
    },
    cases: [
      {
        caseId: "case-002",
        promptId: "case-002",
        prompt: "Answer using only the supplied source snippet.",
        tags: ["core", "factuality"],
        outputText: "Invented unsupported detail.",
        expectation: {
          expectedFailure: { failureType: "no_failure", failureSubtype: null },
          observedFailure: { failureType: "hallucination", failureSubtype: null },
          verdict: "unexpected_failure",
        },
        classification: {
          failure: { failureType: "hallucination", failureSubtype: null },
          confidence: 0.91,
          explanation: "Unsupported factual framing detected.",
        },
        error: null,
      },
    ],
  };
}

function buildFallbackLinkedRunDetail(runId: string, dataset: string): RunDetail {
  return {
    source: {
      label: "Repo root artifact store",
      path: "/tmp/model-failure-lab",
      runsPath: "/tmp/model-failure-lab/runs",
      reportsPath: "/tmp/model-failure-lab/reports",
    },
    run: {
      runId,
      dataset,
      model: "demo",
      createdAt: "2026-03-30T12:10:00Z",
      status: "completed",
      reportId: `${runId}_report`,
      adapterId: "demo",
      classifierId: "heuristic_v1",
      runSeed: 17,
    },
    metrics: {
      attemptedCaseCount: 1,
      classifiedCaseCount: 1,
      executionErrorCount: 0,
      unclassifiedCount: 0,
      successfulModelInvocationCount: 1,
      failureCaseCount: 0,
      failureRate: 0,
      classificationCoverage: 1,
      executionSuccessRate: 1,
    },
    summary: {
      failureTypes: [],
      expectationVerdicts: [],
      tagSlices: [
        {
          tag: "core",
          attemptedCaseCount: 1,
          classifiedCaseCount: 1,
          failureCaseCount: 0,
          failureRate: 0,
          expectationVerdictCounts: { no_failure_as_expected: 1 },
        },
      ],
    },
    lenses: {
      mismatchCaseIds: [],
      notableCaseIds: ["case-001"],
      allCaseIds: ["case-001"],
      errorCaseIds: [],
    },
    cases: [
      {
        caseId: "case-001",
        promptId: "case-001",
        prompt: "Ground the answer in the supplied source.",
        tags: ["core"],
        outputText: "Grounded answer.",
        expectation: {
          expectedFailure: { failureType: "no_failure", failureSubtype: null },
          observedFailure: { failureType: "no_failure", failureSubtype: null },
          verdict: "no_failure_as_expected",
        },
        classification: {
          failure: { failureType: "no_failure", failureSubtype: null },
          confidence: 0.2,
          explanation: "No heuristic failure signal detected.",
        },
        error: null,
      },
    ],
  };
}

function mockComparisonAndRunDetails(
  detail: ComparisonDetail,
  linkedRuns: Map<string, RunDetail> = new Map([
    ["run_alpha", buildLinkedRunDetail("run_alpha", "reasoning-failures-v1")],
    ["run_beta", buildLinkedRunDetail("run_beta", "reasoning-failures-v1")],
  ]),
) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      if (url.includes(`/__failure_lab__/artifacts/comparison-detail.json?reportId=${detail.comparison.reportId}`)) {
        return {
          ok: true,
          status: 200,
          json: async () => serializeComparisonDetail(detail),
        } as Response;
      }

      if (url.includes("/__failure_lab__/artifacts/harvest.json")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            source: detail.source,
            dataset_id: "comparison-compare-alpha-to-beta-failure-to-no-failure",
            lifecycle: "draft",
            mode: "deltas",
            output_path:
              "datasets/harvested/comparison-compare-alpha-to-beta-failure-to-no-failure.json",
            selected_case_count: 1,
          }),
        } as Response;
      }

      for (const [runId, runDetail] of linkedRuns) {
        if (url.includes(`/__failure_lab__/artifacts/run-detail.json?runId=${runId}`)) {
          return {
            ok: true,
            status: 200,
            json: async () => runDetail,
          } as Response;
        }
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({ message: `Unexpected request: ${url}` }),
      } as Response;
    }),
  );
}

describe("comparison detail route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: nativeScrollIntoView,
    });
    window.history.replaceState({}, "", "/");
  });

  it("renders the summary-first comparison explorer and supports in-page case inspection", async () => {
    mockComparisonDetail(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    const comparisonHeading = await screen.findByRole("heading", {
      name: "Reasoning Failures V1",
    });
    expect(comparisonHeading).toBeInTheDocument();
    const comparisonHeader = comparisonHeading.closest("header");
    expect(comparisonHeader).not.toBeNull();
    expect(within(comparisonHeader as HTMLElement).queryByText("Baseline run")).not.toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).queryByText("Candidate run")).not.toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).queryByText("Report ID")).not.toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Baseline")).toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Candidate")).toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Status")).toBeInTheDocument();
    expect(within(comparisonHeader as HTMLElement).getByText("Saved at")).toBeInTheDocument();
    expect(screen.getAllByText("improvement").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("ignore").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("25.0% severity").length).toBeGreaterThan(0);
    expect(screen.getAllByText("compare_alpha_to_beta").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("navigation", { name: "Detail section jumps" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Traverse comparison evidence" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Pathway checkpoints")).not.toBeInTheDocument();
    expect(screen.queryByText("Orient first, then compare hard.")).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Directional change at a glance" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Grounded comparison explanation" }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Signal verdict is `improvement`, so the comparison does not qualify for regression-pack governance.",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Comparison compare_alpha_to_beta. improvement drives most of the matched comparison deltas.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Scope and compatibility" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shared-case analysis only")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Grouped case transitions" }),
    ).toBeInTheDocument();
    const routeProvenanceHeading = screen.getByRole("heading", {
      name: "Route provenance",
    });
    const comparisonRail = routeProvenanceHeading.closest("aside");
    expect(comparisonRail).not.toBeNull();
    expect(within(comparisonRail as HTMLElement).getByText("Report ID")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Baseline run")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Candidate run")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Compare mode")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).getByText("Metrics scope")).toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).queryByText("Shared cases")).not.toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).queryByText("Baseline only")).not.toBeInTheDocument();
    expect(within(comparisonRail as HTMLElement).queryByText("Candidate only")).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "failure -> no_failure" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Active case").length).toBeGreaterThanOrEqual(2);
    expect(
      screen.getByRole("button", { name: "Inspect transition case case-002" }),
    ).toHaveAttribute("data-active-case", "true");
    expect(document.querySelectorAll('[data-active-case="true"]')).toHaveLength(2);
    expect(
      await screen.findByText("Unsupported factual framing detected."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "reasoning +12.5%" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "reasoning +12.5%" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Inspect transition case case-004" }),
      ).toHaveAttribute("data-active-case", "true");
    });

    fireEvent.click(
      screen.getByRole("link", { name: "compare_alpha_to_beta:case-004" }),
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Inspect transition case case-004" }),
      ).toHaveAttribute("data-active-case", "true");
    });
    expect(screen.getByText("Reasoning chain diverged from the rubric.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Inspect transition case case-004" }));

    expect(
      screen.getByRole("button", { name: "Inspect transition case case-004" }),
    ).toHaveAttribute("data-active-case", "true");
    expect(screen.getByText("Reasoning chain diverged from the rubric.")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Use only the provided evidence bullets." }),
    ).toBeInTheDocument();
  });

  it("exports the selected transition slice as a draft dataset", async () => {
    const detail = buildCompatibleDetail();
    mockComparisonAndRunDetails(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(
      await screen.findByRole("button", {
        name: /export failure -> no_failure draft/i,
      }),
    );

    expect(
      await screen.findByText(
        /comparison-compare-alpha-to-beta-failure-to-no-failure written to datasets\/harvested\/comparison-compare-alpha-to-beta-failure-to-no-failure\.json\./i,
      ),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(globalThis.fetch);
    await waitFor(() => {
      const harvestCall = fetchMock.mock.calls.find(([input]) =>
        String(input).includes("/__failure_lab__/artifacts/harvest.json"),
      ) as [string | URL | Request, RequestInit?] | undefined;
      expect(harvestCall).toBeTruthy();
      const init = harvestCall?.[1];
      expect(init).toBeDefined();
      if (!init) {
        throw new Error("Expected harvest request init");
      }
      expect(init).toMatchObject({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      expect(JSON.parse(String(init.body))).toEqual({
        mode: "deltas",
        filters: {
          comparisonId: "compare_alpha_to_beta",
          reportId: "compare_alpha_to_beta",
          delta: "failure_to_no_failure",
          limit: 2,
        },
        outputStem: "comparison-compare-alpha-to-beta-failure-to-no-failure",
      });
    });
  });

  it("shows regression family history and can evolve the dataset family", async () => {
    const detail = buildCompatibleDetail();
    const fetchMock = mockComparisonDetailWithVersionHistory(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("regression-reasoning-failures-v1-reasoning-v1"),
    ).toBeInTheDocument();
    expect(screen.getByText("stable trend")).toBeInTheDocument();
    expect(screen.getByText(/Evaluated in\s+2 runs\./)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Evolve family" }));

    expect(
      await screen.findAllByText("regression-reasoning-failures-v1-reasoning-v2"),
    ).toHaveLength(2);
    expect(screen.getByText("1 new")).toBeInTheDocument();

    await waitFor(() => {
      const evolveCall = fetchMock.mock.calls.find(([input]) =>
        String(input).includes("/__failure_lab__/artifacts/dataset-evolve.json"),
      ) as [string | URL | Request, RequestInit?] | undefined;
      expect(evolveCall).toBeTruthy();
      const init = evolveCall?.[1];
      expect(init).toBeDefined();
      if (!init) {
        throw new Error("Expected dataset evolve request init");
      }
      expect(init).toMatchObject({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      expect(JSON.parse(String(init.body))).toEqual({
        familyId: "regression-reasoning-failures-v1-reasoning",
        comparisonId: "compare_alpha_to_beta",
        failureType: null,
      });
    });
  });

  it("surfaces recurring cluster context on the comparison automation panel", async () => {
    const detail = buildCompatibleDetail();
    detail.governanceRecommendation = buildGovernanceRecommendation({
      clusterContext: [buildClusterContext()],
    });
    mockComparisonDetail(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByText("Regression enforcement surface"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Recommended next move").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Family state").length).toBeGreaterThan(0);
    expect(screen.getByText("Recurring clusters")).toBeInTheDocument();
    expect(screen.getByText("reasoning · failure to no failure")).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("link", { name: "compare_alpha_to_beta:case-002" })
        .some(
          (link) =>
            link.getAttribute("href") ===
            "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002",
        ),
    ).toBe(true);
  });

  it("shows escalation and lifecycle recommendation context on the comparison route", async () => {
    const detail = buildCompatibleDetail();
    detail.governanceRecommendation = buildGovernanceRecommendation({
      action: "create",
      policyRule: "new_family_required",
      escalation: {
        status: "critical",
        score: 0.41,
        severityBand: "high",
        reason: "severity=0.270, recent_regressions=2, recurring_clusters=1",
        recentRegressionCount: 2,
        recurringClusterCount: 1,
        familyHealthLabel: "degrading",
      },
      lifecycleRecommendation: {
        familyId: "regression-reasoning-failures-v1-reasoning",
        action: "prune",
        healthCondition: "overgrown",
        rationale: "Projected family growth crosses the deterministic overgrowth threshold.",
        targetFamilyId: null,
        relatedFamilyIds: [],
        sourceDatasetId: "reasoning-failures-v1",
        primaryFailureType: "reasoning",
        latestDatasetId: "regression-reasoning-failures-v1-reasoning-v1",
        versionCount: 4,
        evaluationRunCount: 3,
        recentFailRate: 0.25,
        projectedCaseCount: 32,
      },
    });
    mockComparisonDetailWithVersionHistory(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect((await screen.findAllByText("Lifecycle recommendation")).length).toBeGreaterThan(0);
    expect(screen.getByText("Operator summary")).toBeInTheDocument();
    expect(screen.getByText("Active family state")).toBeInTheDocument();
    expect(screen.getAllByText("critical").length).toBeGreaterThan(0);
    expect(screen.getAllByText("prune").length).toBeGreaterThan(0);
    expect(
      screen.getByText("Projected family growth crosses the deterministic overgrowth threshold."),
    ).toBeInTheDocument();
  });

  it("shows portfolio priority and saved plan context on the comparison route", async () => {
    const detail = buildCompatibleDetail();
    mockComparisonDetailWithVersionHistory(detail);

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect((await screen.findAllByText("Portfolio priority")).length).toBeGreaterThan(0);
    expect(screen.getByText("Matched family")).toBeInTheDocument();
    expect(screen.getAllByText("Saved plans").length).toBeGreaterThan(0);
  });

  it("keeps incompatible comparisons openable with explicit coverage semantics", async () => {
    mockComparisonDetail(buildIncompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_dataset_mismatch"]}
        initialArtifactState={buildReadyArtifactState(["compare_dataset_mismatch"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", {
        name: "Reasoning Failures V1 Vs Hallucination Failures V1",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Incompatible comparison: Dataset Mismatch")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The comparison stays readable even though the saved runs do not align cleanly.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("case-001")).toBeInTheDocument();
    expect(screen.getByText("case-101")).toBeInTheDocument();
    expect(screen.getByText("No grouped transition changes are available.")).toBeInTheDocument();
  });

  it("links baseline and candidate identifiers directly into run detail routes", async () => {
    mockComparisonAndRunDetails(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Open baseline run_alpha" }));

    expect(await screen.findByRole("heading", { name: "Reasoning Failures V1" })).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Why it failed" })).toBeInTheDocument();
  });

  it("opens the selected comparison case directly into baseline and candidate run evidence", async () => {
    mockComparisonAndRunDetails(buildCompatibleDetail());
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    const firstRender = render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("transitions");
      expect(params.get("case")).toBe("case-002");
      expect(params.get("transition")).toBe("failure_to_no_failure");
    });

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Selected case evidence" })).toBeInTheDocument();
    expect(screen.getByText("Invented unsupported detail.")).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("evidence");
      expect(params.get("lens")).toBe("mismatches");
      expect(params.get("case")).toBe("case-002");
    });

    const baselineReturnLink = screen.getByRole("link", { name: "Back to runs" });
    const baselineReturnUrl = new URL(
      baselineReturnLink.getAttribute("href") ?? "",
      "https://example.test",
    );
    expect(baselineReturnUrl.pathname).toBe("/comparisons/compare_alpha_to_beta");
    expect(baselineReturnUrl.searchParams.get("section")).toBe("transitions");
    expect(baselineReturnUrl.searchParams.get("case")).toBe("case-002");
    expect(baselineReturnUrl.searchParams.get("transition")).toBe("failure_to_no_failure");

    firstRender.unmount();

    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in candidate run run_beta",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("run_beta").length).toBeGreaterThan(0);
    expect(screen.getByText("Invented unsupported detail.")).toBeInTheDocument();
  });

  it("disables selected-case drillthrough when the target run is already unavailable", async () => {
    mockComparisonDetail(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState([
          {
            runId: "run_beta",
            dataset: "reasoning-failures-v1",
            model: "demo",
            createdAt: "2026-03-30T11:30:00Z",
            status: "completed",
          },
        ])}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Saved baseline run run_alpha is unavailable in the active run inventory.",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("link", {
        name: "Open case case-002 in candidate run run_beta",
      }),
    ).toBeInTheDocument();
  });

  it("restores explicit comparison URL state and canonicalizes mismatched transition context", async () => {
    mockComparisonDetail(buildCompatibleDetail());
    const scrolledIds: string[] = [];
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: function mockScrollIntoView() {
        scrolledIds.push((this as HTMLElement).id);
      },
    });
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?case=case-002&transition=no_failure_to_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Reasoning chain diverged from the rubric.")).toBeInTheDocument();
    expect(
      await screen.findByText(
        "Requested case case-002 is unavailable in this transition context. Showing case-004 instead.",
      ),
    ).toBeInTheDocument();

    await waitFor(() => {
      const params = new URLSearchParams(window.location.search);
      expect(params.get("section")).toBe("transitions");
      expect(params.get("case")).toBe("case-004");
      expect(params.get("transition")).toBe("no_failure_to_failure");
      expect(scrolledIds).toContain(
        "comparison-transition-no_failure_to_failure",
      );
    });
  });

  it("preserves comparison detail as the return target when opening a linked run", async () => {
    mockComparisonAndRunDetails(buildCompatibleDetail());
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(new URLSearchParams(window.location.search).get("section")).toBe("transitions");
    });

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(await screen.findByRole("heading", { name: "Reasoning Failures V1" })).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    const returnLink = screen.getByRole("link", { name: "Back to runs" });
    const returnUrl = new URL(returnLink.getAttribute("href") ?? "", "https://example.test");
    expect(returnUrl.pathname).toBe("/comparisons/compare_alpha_to_beta");
    expect(returnUrl.searchParams.get("section")).toBe("transitions");
    expect(returnUrl.searchParams.get("case")).toBe("case-002");
    expect(returnUrl.searchParams.get("transition")).toBe("failure_to_no_failure");
  });

  it("shows focused artifact context on the selected comparison case surface", async () => {
    mockComparisonDetail(buildCompatibleDetail());

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getAllByText("compare_alpha_to_beta").length).toBeGreaterThan(0);
    expect(within(artifactContext).getAllByText("case-002").length).toBeGreaterThan(0);
    expect(within(artifactContext).getByText("/tmp/model-failure-lab")).toBeInTheDocument();
  });

  it("preserves configured artifact-source metadata on the comparison detail route", async () => {
    mockComparisonDetail(buildCompatibleDetail(CONFIGURED_SOURCE));

    render(
      <App
        useMemoryRouter
        initialEntries={["/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure"]}
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"], CONFIGURED_SOURCE)}
        initialRunInventoryState={buildReadyRunInventoryState(undefined, CONFIGURED_SOURCE)}
        initialComparisonInventoryState={buildReadyComparisonInventoryState(CONFIGURED_SOURCE)}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Configured artifact store")).toBeInTheDocument();
    expect(screen.getAllByText("/tmp/external-artifacts").length).toBeGreaterThan(0);

    const artifactContext = screen.getByRole("region", { name: "Artifact context" });
    expect(within(artifactContext).getByText("/tmp/external-artifacts")).toBeInTheDocument();
  });

  it("falls back with an explicit notice when exact baseline evidence cannot be resolved after navigation", async () => {
    mockComparisonAndRunDetails(
      buildCompatibleDetail(),
      new Map([
        ["run_alpha", buildFallbackLinkedRunDetail("run_alpha", "reasoning-failures-v1")],
        ["run_beta", buildLinkedRunDetail("run_beta", "reasoning-failures-v1")],
      ]),
    );
    window.history.replaceState(
      {},
      "",
      "/comparisons/compare_alpha_to_beta?section=transitions&case=case-002&transition=failure_to_no_failure",
    );

    render(
      <App
        initialArtifactState={buildReadyArtifactState(["compare_alpha_to_beta"])}
        initialRunInventoryState={buildReadyRunInventoryState()}
        initialComparisonInventoryState={buildReadyComparisonInventoryState()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("link", {
        name: "Open case case-002 in baseline run run_alpha",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Reasoning Failures V1" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("run_alpha").length).toBeGreaterThan(0);
    expect(
      await screen.findByText(
        "Requested case case-002 is unavailable in this evidence state. Showing case-001 instead.",
      ),
    ).toBeInTheDocument();
  });
});
