export const ARTIFACT_OVERVIEW_PATH = "/__failure_lab__/artifacts/overview.json";
export const RUNS_INDEX_PATH = "/__failure_lab__/artifacts/runs.json";
export const COMPARISONS_INDEX_PATH = "/__failure_lab__/artifacts/comparisons.json";
export const COMPARISON_DETAIL_PATH = "/__failure_lab__/artifacts/comparison-detail.json";
export const RUN_DETAIL_PATH = "/__failure_lab__/artifacts/run-detail.json";

export type ArtifactOverviewStatus = "ready" | "empty" | "incompatible";

export type ArtifactSourceDescriptor = {
  label: string;
  path: string;
  runsPath: string;
  reportsPath: string;
};

export type ArtifactCollectionSummary = {
  count: number;
  ids: string[];
};

export type ArtifactOverview = {
  status: ArtifactOverviewStatus;
  source: ArtifactSourceDescriptor;
  runs: ArtifactCollectionSummary;
  comparisons: ArtifactCollectionSummary;
  issues: string[];
  message: string | null;
};

export type ArtifactShellState =
  | {
      status: "loading";
      overview: null;
    }
  | {
      status: ArtifactOverviewStatus;
      overview: ArtifactOverview;
    };

export type RunInventoryItem = {
  runId: string;
  dataset: string;
  model: string;
  createdAt: string;
  status: string;
};

export type RunInventory = {
  source: ArtifactSourceDescriptor;
  runs: RunInventoryItem[];
};

export type RunInventoryState =
  | {
      status: "idle" | "loading";
      inventory: null;
      message: null;
    }
  | {
      status: "ready";
      inventory: RunInventory;
      message: null;
    }
  | {
      status: "incompatible";
      inventory: null;
      message: string;
    };

export type ComparisonInventoryItem = {
  reportId: string;
  baselineRunId: string;
  candidateRunId: string;
  dataset: string | null;
  createdAt: string;
  status: string;
  compatible: boolean;
};

export type ComparisonInventory = {
  source: ArtifactSourceDescriptor;
  comparisons: ComparisonInventoryItem[];
};

export type ComparisonInventoryState =
  | {
      status: "idle" | "loading";
      inventory: null;
      message: null;
    }
  | {
      status: "ready";
      inventory: ComparisonInventory;
      message: null;
    }
  | {
      status: "incompatible";
      inventory: null;
      message: string;
    };

export type ComparisonMetricsSnapshot = {
  attemptedCaseCount: number;
  classifiedCaseCount: number;
  executionErrorCount: number;
  unclassifiedCount: number;
  successfulModelInvocationCount: number;
  failureRate: number | null;
  classificationCoverage: number | null;
  executionSuccessRate: number | null;
};

export type ComparisonDeltaMetrics = {
  failureRate: number | null;
  classificationCoverage: number | null;
  executionSuccessRate: number | null;
};

export type ComparisonTransitionSummaryRow = {
  transitionType: string;
  label: string;
  count: number;
  caseIds: string[];
};

export type ComparisonCaseDeltaRecord = {
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

export type ComparisonDetail = {
  source: ArtifactSourceDescriptor;
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
    baseline: ComparisonMetricsSnapshot;
    candidate: ComparisonMetricsSnapshot;
    delta: ComparisonDeltaMetrics;
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
    summary: ComparisonTransitionSummaryRow[];
  };
  caseDeltas: ComparisonCaseDeltaRecord[];
};

export type ComparisonDetailState =
  | {
      status: "idle" | "loading";
      detail: null;
      message: null;
    }
  | {
      status: "ready";
      detail: ComparisonDetail;
      message: null;
    }
  | {
      status: "incompatible";
      detail: null;
      message: string;
    };

export type FailureLabelRecord = {
  failureType: string;
  failureSubtype: string | null;
};

export type RunDetailSummaryRow = {
  label: string;
  count: number;
  share: number | null;
  caseIds: string[];
};

export type RunTagSlice = {
  tag: string;
  attemptedCaseCount: number;
  classifiedCaseCount: number;
  failureCaseCount: number;
  failureRate: number | null;
  expectationVerdictCounts: Record<string, number>;
};

export type RunCaseRecord = {
  caseId: string;
  promptId: string;
  prompt: string;
  tags: string[];
  outputText: string | null;
  expectation: {
    expectedFailure: FailureLabelRecord | null;
    observedFailure: FailureLabelRecord | null;
    verdict: string | null;
  };
  classification: {
    failure: FailureLabelRecord;
    confidence: number | null;
    explanation: string | null;
  } | null;
  error: {
    stage: string;
    type: string;
    message: string;
  } | null;
};

export type RunCaseLensKey = "mismatches" | "notable" | "all" | "errors";

export type RunDetail = {
  source: ArtifactSourceDescriptor;
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
    failureTypes: RunDetailSummaryRow[];
    expectationVerdicts: RunDetailSummaryRow[];
    tagSlices: RunTagSlice[];
  };
  lenses: {
    mismatchCaseIds: string[];
    notableCaseIds: string[];
    allCaseIds: string[];
    errorCaseIds: string[];
  };
  cases: RunCaseRecord[];
};

export type RunDetailState =
  | {
      status: "idle" | "loading";
      detail: null;
      message: null;
    }
  | {
      status: "ready";
      detail: RunDetail;
      message: null;
    }
  | {
      status: "incompatible";
      detail: null;
      message: string;
    };

export const DEFAULT_ARTIFACT_SOURCE: ArtifactSourceDescriptor = {
  label: "Local artifact root",
  path: "repo-root runs/ and reports/ directories",
  runsPath: "runs/",
  reportsPath: "reports/",
};
