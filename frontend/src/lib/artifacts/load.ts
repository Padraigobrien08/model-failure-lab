import {
  ARTIFACT_OVERVIEW_PATH,
  DEFAULT_ARTIFACT_SOURCE,
  RUNS_INDEX_PATH,
  type ArtifactCollectionSummary,
  type ArtifactOverview,
  type ArtifactOverviewStatus,
  type ArtifactSourceDescriptor,
  type RunInventory,
  type RunInventoryItem,
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

function requireSource(value: unknown, field: string): ArtifactSourceDescriptor {
  if (value === null || typeof value !== "object") {
    throw new Error(`${field} must be an object`);
  }

  const source = value as Record<string, unknown>;
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
