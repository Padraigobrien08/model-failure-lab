import { execFile } from "node:child_process";
import { createServer as createHttpServer } from "node:http";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { Readable, Writable } from "node:stream";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { createServer as createViteServer } from "vite";

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

function parseArgs(argv) {
  const options = {
    artifactRoot: null,
    mode: "demo",
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--mode") {
      options.mode = argv[index + 1] ?? "";
      index += 1;
      continue;
    }
    if (arg === "--artifact-root") {
      options.artifactRoot = argv[index + 1] ?? "";
      index += 1;
      continue;
    }
    if (arg === "--help") {
      printHelp();
      process.exit(0);
    }
    throw new Error(`Unknown argument: ${arg}`);
  }

  if (!["demo", "existing", "ollama-stub"].includes(options.mode)) {
    throw new Error(`Unsupported mode: ${options.mode}`);
  }
  if (options.mode === "existing" && !options.artifactRoot) {
    throw new Error("--artifact-root is required when --mode existing");
  }

  return options;
}

function printHelp() {
  process.stdout.write(
    [
      "Usage: node frontend/scripts/smoke-real-artifacts.mjs [--mode demo|existing|ollama-stub] [--artifact-root PATH]",
      "",
      "Modes:",
      "  demo         Generate demo artifacts with the repo-local python module and inspect them.",
      "  existing     Inspect an existing artifact root without generating new artifacts.",
      "  ollama-stub  Generate artifacts through the ollama:<model> CLI path against a localhost stub.",
    ].join("\n") + "\n",
  );
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

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

class OllamaStubServer {
  constructor() {
    this.requests = [];
    this.server = createHttpServer(async (request, response) => {
      if (request.method !== "POST" || request.url !== "/api/generate") {
        response.statusCode = 404;
        response.end();
        return;
      }

      try {
        const rawBody = await new Promise((resolve, reject) => {
          let body = "";
          request.setEncoding("utf8");
          request.on("data", (chunk) => {
            body += chunk;
          });
          request.on("end", () => resolve(body));
          request.on("error", reject);
        });

        const payload = JSON.parse(rawBody);
        this.requests.push(payload);

        const responsePayload = {
          done: true,
          eval_count: 5,
          model: String(payload.model),
          prompt_eval_count: 7,
          response: `model:${payload.model}::${payload.prompt}`,
        };
        response.statusCode = 200;
        response.setHeader("Content-Type", "application/json");
        response.end(JSON.stringify(responsePayload));
      } catch (error) {
        response.statusCode = 500;
        response.end(error instanceof Error ? error.message : String(error));
      }
    });
  }

  get baseUrl() {
    const address = this.server.address();
    if (!address || typeof address === "string") {
      throw new Error("Ollama stub server is not listening yet");
    }
    return `http://127.0.0.1:${address.port}`;
  }

  async start() {
    await new Promise((resolve, reject) => {
      this.server.once("error", reject);
      this.server.listen(0, "127.0.0.1", () => {
        this.server.off("error", reject);
        resolve(undefined);
      });
    });
  }

  async close() {
    await new Promise((resolve, reject) => {
      this.server.close((error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve(undefined);
      });
    });
  }
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

async function prepareDemoArtifacts(artifactRoot) {
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

  return {
    comparisonReportId,
    extraLines: [],
    runId: firstRunId,
  };
}

async function prepareOllamaArtifacts(artifactRoot) {
  const stub = new OllamaStubServer();
  await stub.start();

  try {
    const baselineOutput = await runCli([
      "run",
      "--dataset",
      "reasoning-failures-v1",
      "--model",
      "ollama:baseline-model",
      "--ollama-host",
      stub.baseUrl,
      "--system-prompt",
      "Be concise.",
      "--model-option",
      "temperature=0",
      "--root",
      artifactRoot,
    ]);
    const baselineRunId = parseLabel(baselineOutput, "Run ID");
    await runCli(["report", "--run", baselineRunId, "--root", artifactRoot]);

    const candidateOutput = await runCli([
      "run",
      "--dataset",
      "reasoning-failures-v1",
      "--model",
      "ollama:candidate-model",
      "--ollama-host",
      stub.baseUrl,
      "--system-prompt",
      "Be concise.",
      "--model-option",
      "temperature=0",
      "--root",
      artifactRoot,
    ]);
    const candidateRunId = parseLabel(candidateOutput, "Run ID");
    await runCli(["report", "--run", candidateRunId, "--root", artifactRoot]);

    const compareOutput = await runCli([
      "compare",
      baselineRunId,
      candidateRunId,
      "--root",
      artifactRoot,
    ]);
    const comparisonReportId = parseLabel(compareOutput, "Report ID");

    if (stub.requests.length === 0) {
      throw new Error("Ollama stub smoke did not receive any requests");
    }
    if (!stub.requests.every((payload) => payload.system === "Be concise.")) {
      throw new Error("Ollama stub smoke did not preserve the system prompt");
    }
    if (!stub.requests.every((payload) => payload.stream === false)) {
      throw new Error("Ollama stub smoke did not force non-streaming requests");
    }
    if (!stub.requests.every((payload) => payload.options?.temperature === 0)) {
      throw new Error("Ollama stub smoke did not preserve model options");
    }

    return {
      comparisonReportId,
      extraLines: [`Ollama requests: ${stub.requests.length}`],
      runId: baselineRunId,
    };
  } finally {
    await stub.close();
  }
}

async function resolveExistingArtifacts(artifactRoot) {
  const runIds = await listDirectoryIds(path.join(artifactRoot, "runs"));
  if (runIds.length === 0) {
    throw new Error("No saved runs were found in the provided artifact root");
  }

  const reportIds = await listDirectoryIds(path.join(artifactRoot, "reports"));
  let comparisonReportId = null;
  let comparisonPayload = null;

  for (const reportId of reportIds) {
    const payload = await readJson(
      path.join(artifactRoot, "reports", reportId, "report.json"),
    );
    const reportKind = payload?.metadata?.report_kind;
    if (reportKind === "comparison" || typeof payload?.comparison === "object") {
      comparisonReportId = reportId;
      comparisonPayload = payload;
      break;
    }
  }

  if (!comparisonReportId) {
    throw new Error("No comparison report was found in the provided artifact root");
  }

  const preferredRunId = comparisonPayload?.comparison?.baseline_run_id;
  const runId =
    typeof preferredRunId === "string" && runIds.includes(preferredRunId)
      ? preferredRunId
      : runIds[0];

  return {
    comparisonReportId,
    extraLines: [],
    runId,
  };
}

async function inspectArtifactRoot({ artifactRoot, comparisonReportId, mode, runId, extraLines }) {
  const normalizedArtifactRoot = path.resolve(artifactRoot);
  const previousArtifactRoot = process.env.FAILURE_LAB_ARTIFACT_ROOT;
  let server;

  try {
    process.env.FAILURE_LAB_ARTIFACT_ROOT = normalizedArtifactRoot;
    server = await createViteServer({
      configFile: path.join(frontendRoot, "vite.config.ts"),
      logLevel: "silent",
      root: frontendRoot,
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
      `/__failure_lab__/artifacts/run-detail.json?runId=${encodeURIComponent(runId)}`,
    );
    const comparisonDetail = await fetchJsonFromMiddleware(
      server,
      `/__failure_lab__/artifacts/comparison-detail.json?reportId=${encodeURIComponent(
        comparisonReportId,
      )}`,
    );

    const runIds = await listDirectoryIds(path.join(normalizedArtifactRoot, "runs"));
    const reportIds = await listDirectoryIds(path.join(normalizedArtifactRoot, "reports"));

    if (overview.status !== "ready") {
      throw new Error(`Expected ready overview, received ${overview.status}`);
    }
    if (overview.source.path !== normalizedArtifactRoot) {
      throw new Error("Overview source path did not use the configured artifact root");
    }
    if (runsInventory.source.path !== normalizedArtifactRoot) {
      throw new Error("Runs inventory source path did not use the configured artifact root");
    }
    if (comparisonsInventory.source.path !== normalizedArtifactRoot) {
      throw new Error(
        "Comparisons inventory source path did not use the configured artifact root",
      );
    }
    if (runDetail.source.path !== normalizedArtifactRoot) {
      throw new Error("Run detail source path did not use the configured artifact root");
    }
    if (comparisonDetail.source.path !== normalizedArtifactRoot) {
      throw new Error(
        "Comparison detail source path did not use the configured artifact root",
      );
    }
    if (!runIds.includes(runId) || !runsInventory.runs.some((row) => row.run_id === runId)) {
      throw new Error(`Runs inventory did not include ${runId}`);
    }
    if (
      !reportIds.includes(comparisonReportId) ||
      !comparisonsInventory.comparisons.some((row) => row.report_id === comparisonReportId)
    ) {
      throw new Error(`Comparisons inventory did not include ${comparisonReportId}`);
    }
    if (runDetail.run.runId !== runId) {
      throw new Error("Run detail payload did not match the selected run");
    }
    if (comparisonDetail.comparison.reportId !== comparisonReportId) {
      throw new Error("Comparison detail payload did not match the selected report");
    }

    process.stdout.write(
      [
        "Failure Lab UI Smoke",
        `Mode: ${mode}`,
        `CLI: ${CLI_LABEL} (via python3 -m model_failure_lab)`,
        `Artifact root: ${normalizedArtifactRoot}`,
        `Run: ${runId}`,
        `Comparison: ${comparisonReportId}`,
        ...extraLines,
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
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const ownsArtifactRoot = !options.artifactRoot;
  const artifactRoot = path.resolve(
    options.artifactRoot ?? (await mkdtemp(path.join(tmpdir(), "failure-lab-ui-smoke-"))),
  );

  try {
    let selection;
    if (options.mode === "existing") {
      selection = await resolveExistingArtifacts(artifactRoot);
    } else if (options.mode === "ollama-stub") {
      selection = await prepareOllamaArtifacts(artifactRoot);
    } else {
      selection = await prepareDemoArtifacts(artifactRoot);
    }

    await inspectArtifactRoot({
      artifactRoot,
      mode: options.mode,
      ...selection,
    });
  } finally {
    if (ownsArtifactRoot) {
      await rm(artifactRoot, { force: true, recursive: true });
    }
  }
}

main().catch((error) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
