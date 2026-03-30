import path from "node:path";
import fs from "node:fs/promises";
import type { IncomingMessage, ServerResponse } from "node:http";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const ARTIFACT_OVERVIEW_PATH = "/__failure_lab__/artifacts/overview.json";
const RUNS_INDEX_PATH = "/__failure_lab__/artifacts/runs.json";
const RUN_FILENAME = "run.json";
const RESULTS_FILENAME = "results.json";
const REPORT_FILENAME = "report.json";
const REPORT_DETAILS_FILENAME = "report_details.json";

type ArtifactCollectionSummary = {
  count: number;
  ids: string[];
};

type ArtifactCollectionOptions = {
  label: "run" | "report";
  primaryFile: string;
  secondaryFile: string;
  primaryIdField: "run_id" | "report_id";
};

type RunInventoryRow = {
  run_id: string;
  dataset: string;
  model: string;
  created_at: string;
  status: string;
};

function failureLabArtifactsPlugin(): Plugin {
  const repoRoot = path.resolve(__dirname, "..");

  async function collectArtifactIds(
    rootPath: string,
    options: ArtifactCollectionOptions,
  ): Promise<{ summary: ArtifactCollectionSummary; issues: string[] }> {
    const { label, primaryFile, secondaryFile, primaryIdField } = options;
    const issues: string[] = [];
    let entries: Array<{ isDirectory: () => boolean; name: string }>;

    try {
      entries = (await fs.readdir(rootPath, { withFileTypes: true })) as Array<{
        isDirectory: () => boolean;
        name: string;
      }>;
    } catch (error) {
      const code = error instanceof Error && "code" in error ? String(error.code) : null;
      if (code === "ENOENT") {
        return {
          summary: { count: 0, ids: [] },
          issues,
        };
      }
      throw error;
    }

    const ids: string[] = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) {
        continue;
      }

      const entryPath = path.join(rootPath, entry.name);
      const primaryPath = path.join(entryPath, primaryFile);
      const secondaryPath = path.join(entryPath, secondaryFile);

      try {
        await fs.access(primaryPath);
        await fs.access(secondaryPath);
      } catch {
        issues.push(
          `${label} ${entry.name} is missing ${primaryFile} or ${secondaryFile}`,
        );
        continue;
      }

      try {
        const payload = JSON.parse(await fs.readFile(primaryPath, "utf-8")) as Record<
          string,
          unknown
        >;
        const artifactId = payload[primaryIdField];
        if (typeof artifactId !== "string" || artifactId.trim().length === 0) {
          issues.push(`${label} ${entry.name} has an invalid ${primaryIdField}`);
          continue;
        }
        ids.push(artifactId);
      } catch (error) {
        const message = error instanceof Error ? error.message : "unknown error";
        issues.push(`${label} ${entry.name} could not be read: ${message}`);
      }
    }

    ids.sort((left, right) => left.localeCompare(right));
    return {
      summary: {
        count: ids.length,
        ids,
      },
      issues,
    };
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

  async function buildArtifactOverview() {
    const runsPath = path.join(repoRoot, "runs");
    const reportsPath = path.join(repoRoot, "reports");

    const [runInventory, reportsResult] = await Promise.all([
      collectRunInventory(runsPath),
      collectArtifactIds(reportsPath, {
        label: "report",
        primaryFile: REPORT_FILENAME,
        secondaryFile: REPORT_DETAILS_FILENAME,
        primaryIdField: "report_id",
      }),
    ]);

    const issues = [...runInventory.issues, ...reportsResult.issues];
    const status =
      issues.length > 0
        ? "incompatible"
        : runInventory.rows.length === 0 && reportsResult.summary.count === 0
          ? "empty"
          : "ready";

    return {
      status,
      source: {
        label: "Repo root artifact store",
        path: repoRoot,
        runsPath,
        reportsPath,
      },
      runs: {
        count: runInventory.rows.length,
        ids: runInventory.rows.map((row) => row.run_id),
      },
      comparisons: reportsResult.summary,
      issues,
      message:
        status === "empty"
          ? "No saved engine artifacts were found in the default local root."
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
          source: {
            label: "Repo root artifact store",
            path: repoRoot,
            runsPath: path.join(repoRoot, "runs"),
            reportsPath: path.join(repoRoot, "reports"),
          },
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
    const runsPath = path.join(repoRoot, "runs");
    const reportsPath = path.join(repoRoot, "reports");

    try {
      const runInventory = await collectRunInventory(runsPath);
      if (runInventory.issues.length > 0) {
        res.statusCode = 500;
        res.setHeader("Content-Type", "application/json");
        res.end(
          JSON.stringify({
            source: {
              label: "Repo root artifact store",
              path: repoRoot,
              runsPath,
              reportsPath,
            },
            runs: [],
            issues: runInventory.issues,
          }),
        );
        return;
      }

      res.statusCode = 200;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          source: {
            label: "Repo root artifact store",
            path: repoRoot,
            runsPath,
            reportsPath,
          },
          runs: runInventory.rows,
        }),
      );
    } catch (error) {
      res.statusCode = 500;
      res.setHeader("Content-Type", "application/json");
      res.end(
        JSON.stringify({
          source: {
            label: "Repo root artifact store",
            path: repoRoot,
            runsPath,
            reportsPath,
          },
          runs: [],
          issues: [error instanceof Error ? error.message : "run inventory failed"],
        }),
      );
    }
  }

  function registerArtifactMiddleware(
    middlewares: {
      use: (
        path: string,
        handler: (
          req: IncomingMessage,
          res: ServerResponse,
          next: (error?: unknown) => void,
        ) => void,
      ) => void;
    },
  ) {
    middlewares.use(ARTIFACT_OVERVIEW_PATH, (req, res, next) => {
      void handleArtifactOverview(req, res).catch(next);
    });
    middlewares.use(RUNS_INDEX_PATH, (req, res, next) => {
      void handleRunsIndex(req, res).catch(next);
    });
  }

  return {
    name: "failure-lab-artifacts",
    configureServer(server: {
      middlewares: {
        use: (
          path: string,
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
          path: string,
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
