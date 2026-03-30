export const ARTIFACT_OVERVIEW_PATH = "/__failure_lab__/artifacts/overview.json";

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

export const DEFAULT_ARTIFACT_SOURCE: ArtifactSourceDescriptor = {
  label: "Local artifact root",
  path: "repo-root runs/ and reports/ directories",
  runsPath: "runs/",
  reportsPath: "reports/",
};
