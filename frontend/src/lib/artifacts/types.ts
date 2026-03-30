export const ARTIFACT_OVERVIEW_PATH = "/__failure_lab__/artifacts/overview.json";
export const RUNS_INDEX_PATH = "/__failure_lab__/artifacts/runs.json";

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

export const DEFAULT_ARTIFACT_SOURCE: ArtifactSourceDescriptor = {
  label: "Local artifact root",
  path: "repo-root runs/ and reports/ directories",
  runsPath: "runs/",
  reportsPath: "reports/",
};
