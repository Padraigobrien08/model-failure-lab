import {
  ARTIFACT_OVERVIEW_PATH,
  DEFAULT_ARTIFACT_SOURCE,
  type ArtifactCollectionSummary,
  type ArtifactOverview,
  type ArtifactOverviewStatus,
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

export function validateArtifactOverview(payload: unknown): ArtifactOverview {
  if (payload === null || typeof payload !== "object") {
    throw new Error("artifact overview payload must be an object");
  }

  const data = payload as Record<string, unknown>;
  const status = requireString(data.status, "status");
  if (status !== "ready" && status !== "empty" && status !== "incompatible") {
    throw new Error("status must be ready, empty, or incompatible");
  }

  const sourcePayload = data.source;
  if (sourcePayload === null || typeof sourcePayload !== "object") {
    throw new Error("source must be an object");
  }
  const sourceData = sourcePayload as Record<string, unknown>;

  const issuesValue = data.issues;
  const issues =
    issuesValue === undefined ? [] : requireStringArray(issuesValue, "issues");
  const messageValue = data.message;

  return {
    status: status as ArtifactOverviewStatus,
    source: {
      label: requireString(sourceData.label, "source.label"),
      path: requireString(sourceData.path, "source.path"),
      runsPath: requireString(sourceData.runsPath, "source.runsPath"),
      reportsPath: requireString(sourceData.reportsPath, "source.reportsPath"),
    },
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
