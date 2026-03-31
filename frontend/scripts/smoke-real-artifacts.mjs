import { execFile } from "node:child_process";
import { mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { Readable, Writable } from "node:stream";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { createServer } from "vite";

const execFileAsync = promisify(execFile);
const repoRoot = path.resolve(fileURLToPath(new URL("..", import.meta.url)), "..");
const frontendRoot = path.join(repoRoot, "frontend");
const pyPath = path.join(repoRoot, "src");
const CLI_LABEL = "failure-lab";

function parseLabel(output, label) {
  const pattern = new RegExp(`^${label}:\\s+(.+)$`, "m");
  const match = output.match(pattern);
  if (!match) {
    throw new Error(`Could not parse ${label} from CLI output:\n${output}`);
  }
  return match[1].trim();
}

async function runCli(args) {
  const command = ["-m", "model_failure_lab", ...args];
  const { stdout, stderr } = await execFileAsync("python3", command, {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONPATH: pyPath,
    },
  });

  if (stderr.trim().length > 0) {
    process.stderr.write(stderr);
  }

  return stdout;
}

async function listDirectoryIds(dirPath) {
  const entries = await readdir(dirPath, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort((left, right) => right.localeCompare(left));
}

async function fetchJsonFromMiddleware(server, pathname) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let settled = false;
    const headers = new Map();

    const req = new Readable({
      read() {
        this.push(null);
      },
    });
    req.url = pathname;
    req.originalUrl = pathname;
    req.method = "GET";
    req.headers = {
      accept: "application/json",
      host: "failure-lab.local",
    };

    const res = new Writable({
      write(chunk, _encoding, callback) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
        callback();
      },
    });
    res.statusCode = 200;
    res.setHeader = (name, value) => {
      headers.set(String(name).toLowerCase(), value);
      return res;
    };
    res.getHeader = (name) => headers.get(String(name).toLowerCase());
    res.writeHead = (statusCode, maybeHeaders) => {
      res.statusCode = statusCode;
      if (maybeHeaders && typeof maybeHeaders === "object") {
        for (const [name, value] of Object.entries(maybeHeaders)) {
          headers.set(String(name).toLowerCase(), value);
        }
      }
      return res;
    };

    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      const body = Buffer.concat(chunks).toString("utf8");
      if (res.statusCode >= 400) {
        reject(new Error(`Request failed for ${pathname}: ${res.statusCode} ${body}`));
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch (error) {
        reject(
          error instanceof Error
            ? error
            : new Error(`Failed to parse JSON body for ${pathname}`),
        );
      }
    };

    res.end = (chunk) => {
      if (chunk) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      }
      finish();
      return res;
    };

    server.middlewares.handle(req, res, (error) => {
      if (error) {
        reject(error);
        return;
      }
      finish();
    });
  });
}

async function main() {
  const artifactRoot = await mkdtemp(path.join(tmpdir(), "failure-lab-ui-smoke-"));
  const previousArtifactRoot = process.env.FAILURE_LAB_ARTIFACT_ROOT;
  let server;

  try {
    const firstRunOutput = await runCli([
      "run",
      "--dataset",
      "reasoning-failures-v1",
      "--model",
      "demo",
      "--root",
      artifactRoot,
    ]);
    const firstRunId = parseLabel(firstRunOutput, "Run ID");

    await runCli(["report", "--run", firstRunId, "--root", artifactRoot]);

    const secondRunOutput = await runCli([
      "run",
      "--dataset",
      "reasoning-failures-v1",
      "--model",
      "demo:alternate",
      "--root",
      artifactRoot,
    ]);
    const secondRunId = parseLabel(secondRunOutput, "Run ID");

    await runCli(["report", "--run", secondRunId, "--root", artifactRoot]);

    const compareOutput = await runCli([
      "compare",
      firstRunId,
      secondRunId,
      "--root",
      artifactRoot,
    ]);
    const comparisonReportId = parseLabel(compareOutput, "Report ID");

    process.env.FAILURE_LAB_ARTIFACT_ROOT = artifactRoot;
    server = await createServer({
      configFile: path.join(frontendRoot, "vite.config.ts"),
      root: frontendRoot,
      logLevel: "silent",
      server: {
        middlewareMode: true,
      },
    });
    const overview = await fetchJsonFromMiddleware(
      server,
      "/__failure_lab__/artifacts/overview.json",
    );
    const runsInventory = await fetchJsonFromMiddleware(
      server,
      "/__failure_lab__/artifacts/runs.json",
    );
    const comparisonsInventory = await fetchJsonFromMiddleware(
      server,
      "/__failure_lab__/artifacts/comparisons.json",
    );
    const runDetail = await fetchJsonFromMiddleware(
      server,
      `/__failure_lab__/artifacts/run-detail.json?runId=${encodeURIComponent(firstRunId)}`,
    );
    const comparisonDetail = await fetchJsonFromMiddleware(
      server,
      `/__failure_lab__/artifacts/comparison-detail.json?reportId=${encodeURIComponent(
        comparisonReportId,
      )}`,
    );

    const runIds = await listDirectoryIds(path.join(artifactRoot, "runs"));
    const reportIds = await listDirectoryIds(path.join(artifactRoot, "reports"));

    if (overview.status !== "ready") {
      throw new Error(`Expected ready overview, received ${overview.status}`);
    }
    if (overview.source.path !== artifactRoot) {
      throw new Error("Overview source path did not use the configured artifact root");
    }
    if (runIds.length < 2 || runsInventory.runs.length < 2) {
      throw new Error("Expected at least two saved runs in the smoke artifact root");
    }
    if (!runsInventory.runs.some((row) => row.run_id === firstRunId)) {
      throw new Error(`Runs inventory did not include ${firstRunId}`);
    }
    if (!reportIds.includes(comparisonReportId)) {
      throw new Error(`Saved comparison report ${comparisonReportId} was not written`);
    }
    if (
      !comparisonsInventory.comparisons.some(
        (row) => row.report_id === comparisonReportId,
      )
    ) {
      throw new Error(`Comparisons inventory did not include ${comparisonReportId}`);
    }
    if (runDetail.run.runId !== firstRunId) {
      throw new Error("Run detail payload did not match the selected run");
    }
    if (comparisonDetail.comparison.reportId !== comparisonReportId) {
      throw new Error("Comparison detail payload did not match the selected report");
    }

    process.stdout.write(
      [
        "Failure Lab UI Smoke",
        `CLI: ${CLI_LABEL} (via python3 -m model_failure_lab)`,
        `Artifact root: ${artifactRoot}`,
        `Runs: ${runIds.join(", ")}`,
        `Comparison: ${comparisonReportId}`,
        "Verified endpoints:",
        "- overview",
        "- runs inventory",
        "- run detail",
        "- comparisons inventory",
        "- comparison detail",
      ].join("\n") + "\n",
    );
  } finally {
    await server?.close();
    if (previousArtifactRoot === undefined) {
      delete process.env.FAILURE_LAB_ARTIFACT_ROOT;
    } else {
      process.env.FAILURE_LAB_ARTIFACT_ROOT = previousArtifactRoot;
    }
    await rm(artifactRoot, { recursive: true, force: true });
  }
}

main().catch((error) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
