import type { ArtifactIndex } from "@/lib/manifest/types";

export const ARTIFACT_INDEX_SCHEMA_VERSION = "artifact_index_v1";
export const DEFAULT_MANIFEST_PATH = "/artifacts/contracts/artifact_index/v1/index.json";

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function sanitizeJsonText(payload: string) {
  return payload.replace(/\b(?:NaN|-?Infinity)\b/g, "null");
}

export function artifactPathToPublicUrl(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  return path.startsWith("/") ? path : `/${path}`;
}

export function parseArtifactJson<T>(payload: string, path: string): T {
  try {
    return JSON.parse(sanitizeJsonText(payload)) as T;
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to parse JSON artifact at ${path}: ${reason}`);
  }
}

export function validateArtifactIndex(payload: unknown): ArtifactIndex {
  if (!isObject(payload)) {
    throw new Error("Artifact index payload must be an object.");
  }

  if (payload.schema_version !== ARTIFACT_INDEX_SCHEMA_VERSION) {
    throw new Error(
      `Unsupported artifact index schema: expected ${ARTIFACT_INDEX_SCHEMA_VERSION}, got ${String(
        payload.schema_version,
      )}`,
    );
  }

  if (!isObject(payload.entities) || !isObject(payload.views)) {
    throw new Error("Artifact index payload is missing entities or views.");
  }

  return payload as ArtifactIndex;
}

export async function loadArtifactJson<T = unknown>(
  path: string,
  fetchImpl: typeof fetch = fetch,
): Promise<T> {
  const requestPath = artifactPathToPublicUrl(path);
  const response = await fetchImpl(requestPath);
  if (!response.ok) {
    throw new Error(`Failed to load artifact JSON from ${requestPath}: ${response.status}`);
  }

  const payload = await response.text();
  return parseArtifactJson<T>(payload, requestPath);
}

export async function loadArtifactIndex(
  path: string = DEFAULT_MANIFEST_PATH,
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactIndex> {
  const payload = await loadArtifactJson(path, fetchImpl);
  return validateArtifactIndex(payload);
}
