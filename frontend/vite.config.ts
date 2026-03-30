import path from "node:path";
import fs from "node:fs/promises";
import type { IncomingMessage, ServerResponse } from "node:http";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const ARTIFACT_OVERVIEW_PATH = "/__failure_lab__/artifacts/overview.json";
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

  async function buildArtifactOverview() {
    const runsPath = path.join(repoRoot, "runs");
    const reportsPath = path.join(repoRoot, "reports");

    const [runsResult, reportsResult] = await Promise.all([
      collectArtifactIds(runsPath, {
        label: "run",
        primaryFile: RUN_FILENAME,
        secondaryFile: RESULTS_FILENAME,
        primaryIdField: "run_id",
      }),
      collectArtifactIds(reportsPath, {
        label: "report",
        primaryFile: REPORT_FILENAME,
        secondaryFile: REPORT_DETAILS_FILENAME,
        primaryIdField: "report_id",
      }),
    ]);

    const issues = [...runsResult.issues, ...reportsResult.issues];
    const status =
      issues.length > 0
        ? "incompatible"
        : runsResult.summary.count === 0 && reportsResult.summary.count === 0
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
      runs: runsResult.summary,
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
