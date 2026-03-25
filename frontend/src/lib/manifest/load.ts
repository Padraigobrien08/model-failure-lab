import type { ArtifactIndex } from "@/lib/manifest/types";

export const ARTIFACT_INDEX_SCHEMA_VERSION = "artifact_index_v1";
export const DEFAULT_MANIFEST_PATH = "/artifacts/contracts/artifact_index/v1/index.json";

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
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

export async function loadArtifactIndex(
  path: string = DEFAULT_MANIFEST_PATH,
  fetchImpl: typeof fetch = fetch,
): Promise<ArtifactIndex> {
  const response = await fetchImpl(path);
  if (!response.ok) {
    throw new Error(`Failed to load artifact index from ${path}: ${response.status}`);
  }

  const payload = (await response.json()) as unknown;
  return validateArtifactIndex(payload);
}
