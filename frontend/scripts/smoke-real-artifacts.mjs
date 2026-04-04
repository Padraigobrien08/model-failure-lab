import { execFile } from "node:child_process";
import { createServer as createHttpServer } from "node:http";
import { mkdtemp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
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
const ARTIFACT_QUERY_PATH = "/__failure_lab__/artifacts/query.json";
const ANTHROPIC_SYSTEM_PROMPT = "Be concise.";
const ANTHROPIC_MAX_TOKENS = 256;
const CLI_LABEL = "failure-lab";
const OLLAMA_SYSTEM_PROMPT = "Be concise.";
const OLLAMA_TEMPERATURE = 0;
const QUERY_LATENCY_BUDGET_MS = 2_000;

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

  if (!["demo", "existing", "ollama-stub", "anthropic-stub"].includes(options.mode)) {
    throw new Error(`Unsupported mode: ${options.mode}`);
  }
  return options;
}

function printHelp() {
  process.stdout.write(
    [
      "Usage: node frontend/scripts/smoke-real-artifacts.mjs [--mode demo|existing|ollama-stub|anthropic-stub] [--artifact-root PATH]",
      "",
      "Modes:",
      "  demo         Generate demo artifacts with the repo-local python module and inspect them.",
      "  existing     Inspect an existing artifact root without generating new artifacts. Defaults to the repo root.",
      "  ollama-stub  Generate artifacts through the ollama:<model> CLI path against a localhost stub.",
      "  anthropic-stub  Generate artifacts through the anthropic:<model> CLI path against a localhost stub and shim SDK.",
    ].join("\n") + "\n",
  );
}

async function runCli(args, { pythonPathEntries = [] } = {}) {
  const command = ["-m", "model_failure_lab", ...args];
  const pythonPath = [pyPath, ...pythonPathEntries];
  if (process.env.PYTHONPATH) {
    pythonPath.push(process.env.PYTHONPATH);
  }
  const { stdout, stderr } = await execFileAsync("python3", command, {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONPATH: pythonPath.join(path.delimiter),
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

class AnthropicStubServer {
  constructor() {
    this.requests = [];
    this.server = createHttpServer(async (request, response) => {
      if (request.method !== "POST" || request.url !== "/v1/messages") {
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
          content: [
            {
              text: `model:${payload.model}::${payload.messages[0].content}`,
              type: "text",
            },
          ],
          id: "msg_123",
          model: String(payload.model),
          role: "assistant",
          stop_reason: "end_turn",
          type: "message",
          usage: {
            input_tokens: 9,
            output_tokens: 5,
          },
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
      throw new Error("Anthropic stub server is not listening yet");
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

async function createAnthropicSdkShim(rootDir) {
  const packageDir = path.join(rootDir, "anthropic");
  await mkdir(packageDir, { recursive: true });
  await writeFile(
    path.join(packageDir, "__init__.py"),
    [
      "import json",
      "from urllib import request",
      "",
      "",
      "class Anthropic:",
      "    def __init__(self, *, api_key=None, base_url=None, **kwargs):",
      "        del api_key, kwargs",
      "        self._base_url = (base_url or 'https://api.anthropic.com').rstrip('/')",
      "        self.messages = _MessagesAPI(self._base_url)",
      "",
      "",
      "class _MessagesAPI:",
      "    def __init__(self, base_url):",
      "        self._base_url = base_url",
      "",
      "    def create(self, **kwargs):",
      "        body = json.dumps(kwargs).encode('utf-8')",
      "        http_request = request.Request(",
      "            f\"{self._base_url}/v1/messages\",",
      "            data=body,",
      "            headers={'Content-Type': 'application/json'},",
      "            method='POST',",
      "        )",
      "        with request.urlopen(http_request) as response:",
      "            return json.loads(response.read().decode('utf-8'))",
      "",
    ].join("\n"),
    "utf8",
  );
}

async function fetchJsonFromMiddleware(server, pathname) {
  const { json } = await fetchTimedJsonFromMiddleware(server, pathname);
  return json;
}

async function fetchTimedJsonFromMiddleware(server, pathname) {
  const startedAt = performance.now();
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
        const parsed = JSON.parse(body);
        resolve({
          durationMs: performance.now() - startedAt,
          json: parsed,
        });
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
      OLLAMA_SYSTEM_PROMPT,
      "--model-option",
      `temperature=${OLLAMA_TEMPERATURE}`,
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
      OLLAMA_SYSTEM_PROMPT,
      "--model-option",
      `temperature=${OLLAMA_TEMPERATURE}`,
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
    if (!stub.requests.every((payload) => payload.system === OLLAMA_SYSTEM_PROMPT)) {
      throw new Error("Ollama stub smoke did not preserve the system prompt");
    }
    if (!stub.requests.every((payload) => payload.stream === false)) {
      throw new Error("Ollama stub smoke did not force non-streaming requests");
    }
    if (!stub.requests.every((payload) => payload.options?.temperature === OLLAMA_TEMPERATURE)) {
      throw new Error("Ollama stub smoke did not preserve model options");
    }

    const baselineRun = await readJson(path.join(artifactRoot, "runs", baselineRunId, "run.json"));
    const candidateRun = await readJson(path.join(artifactRoot, "runs", candidateRunId, "run.json"));
    const comparisonReport = await readJson(
      path.join(artifactRoot, "reports", comparisonReportId, "report.json"),
    );
    if (baselineRun?.metadata?.adapter_id !== "ollama") {
      throw new Error("Baseline run was not written through the ollama adapter");
    }
    if (candidateRun?.metadata?.adapter_id !== "ollama") {
      throw new Error("Candidate run was not written through the ollama adapter");
    }
    if (comparisonReport?.comparison?.compatible !== true) {
      throw new Error("Ollama stub smoke did not produce a compatible comparison report");
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

async function prepareAnthropicArtifacts(artifactRoot) {
  const stub = new AnthropicStubServer();
  const shimRoot = await mkdtemp(path.join(tmpdir(), "failure-lab-anthropic-shim-"));
  await createAnthropicSdkShim(shimRoot);
  await stub.start();

  try {
    const baselineOutput = await runCli(
      [
        "run",
        "--dataset",
        "reasoning-failures-v1",
        "--model",
        "anthropic:baseline-model",
        "--anthropic-base-url",
        stub.baseUrl,
        "--system-prompt",
        ANTHROPIC_SYSTEM_PROMPT,
        "--model-option",
        `max_tokens=${ANTHROPIC_MAX_TOKENS}`,
        "--root",
        artifactRoot,
      ],
      { pythonPathEntries: [shimRoot] },
    );
    const baselineRunId = parseLabel(baselineOutput, "Run ID");
    await runCli(["report", "--run", baselineRunId, "--root", artifactRoot], {
      pythonPathEntries: [shimRoot],
    });

    const candidateOutput = await runCli(
      [
        "run",
        "--dataset",
        "reasoning-failures-v1",
        "--model",
        "anthropic:candidate-model",
        "--anthropic-base-url",
        stub.baseUrl,
        "--system-prompt",
        ANTHROPIC_SYSTEM_PROMPT,
        "--model-option",
        `max_tokens=${ANTHROPIC_MAX_TOKENS}`,
        "--root",
        artifactRoot,
      ],
      { pythonPathEntries: [shimRoot] },
    );
    const candidateRunId = parseLabel(candidateOutput, "Run ID");
    await runCli(["report", "--run", candidateRunId, "--root", artifactRoot], {
      pythonPathEntries: [shimRoot],
    });

    const compareOutput = await runCli(
      [
        "compare",
        baselineRunId,
        candidateRunId,
        "--root",
        artifactRoot,
      ],
      { pythonPathEntries: [shimRoot] },
    );
    const comparisonReportId = parseLabel(compareOutput, "Report ID");

    if (stub.requests.length === 0) {
      throw new Error("Anthropic stub smoke did not receive any requests");
    }
    if (!stub.requests.every((payload) => payload.system === ANTHROPIC_SYSTEM_PROMPT)) {
      throw new Error("Anthropic stub smoke did not preserve the system prompt");
    }
    if (!stub.requests.every((payload) => payload.max_tokens === ANTHROPIC_MAX_TOKENS)) {
      throw new Error("Anthropic stub smoke did not preserve model options");
    }

    const baselineRun = await readJson(path.join(artifactRoot, "runs", baselineRunId, "run.json"));
    const candidateRun = await readJson(path.join(artifactRoot, "runs", candidateRunId, "run.json"));
    const comparisonReport = await readJson(
      path.join(artifactRoot, "reports", comparisonReportId, "report.json"),
    );
    if (baselineRun?.metadata?.adapter_id !== "anthropic") {
      throw new Error("Baseline run was not written through the anthropic adapter");
    }
    if (candidateRun?.metadata?.adapter_id !== "anthropic") {
      throw new Error("Candidate run was not written through the anthropic adapter");
    }
    if (comparisonReport?.comparison?.compatible !== true) {
      throw new Error("Anthropic stub smoke did not produce a compatible comparison report");
    }

    return {
      comparisonReportId,
      extraLines: [`Anthropic requests: ${stub.requests.length}`],
      runId: baselineRunId,
    };
  } finally {
    await stub.close();
    await rm(shimRoot, { force: true, recursive: true });
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
    const analysisCases = await fetchTimedJsonFromMiddleware(
      server,
      `${ARTIFACT_QUERY_PATH}?mode=cases&limit=10`,
    );
    const analysisDeltas = await fetchTimedJsonFromMiddleware(
      server,
      `${ARTIFACT_QUERY_PATH}?mode=deltas&limit=10`,
    );
    const analysisAggregates = await fetchTimedJsonFromMiddleware(
      server,
      `${ARTIFACT_QUERY_PATH}?mode=aggregates&aggregateBy=failure_type&limit=10`,
    );
    const analysisSignals = await fetchTimedJsonFromMiddleware(
      server,
      `${ARTIFACT_QUERY_PATH}?mode=signals&signalDirection=all&limit=10`,
    );
    const analysisClusters = await fetchTimedJsonFromMiddleware(
      server,
      `${ARTIFACT_QUERY_PATH}?mode=clusters&limit=10`,
    );
    const savedSignalRow = analysisSignals.json.rows.find(
      (row) => row && typeof row.report_id === "string" && row.report_id === comparisonReportId,
    );
    const matchedFamilyId =
      comparisonDetail.governanceRecommendation?.matched_family_id ??
      savedSignalRow?.governance_recommendation?.matched_family_id ??
      null;
    const datasetVersions =
      typeof matchedFamilyId === "string" && matchedFamilyId.length > 0
        ? await fetchJsonFromMiddleware(
            server,
            `/__failure_lab__/artifacts/dataset-versions.json?familyId=${encodeURIComponent(
              matchedFamilyId,
            )}&limit=10`,
          )
        : null;

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
    if (!comparisonDetail.signal || typeof comparisonDetail.signal.verdict !== "string") {
      throw new Error("Comparison detail did not expose the persisted signal block");
    }
    if (
      !comparisonDetail.governanceRecommendation ||
      typeof comparisonDetail.governanceRecommendation.action !== "string"
    ) {
      throw new Error("Comparison detail did not expose the persisted governance recommendation");
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
    if (analysisCases.json.source.path !== normalizedArtifactRoot) {
      throw new Error("Analysis case query source path did not use the configured artifact root");
    }
    if (analysisDeltas.json.source.path !== normalizedArtifactRoot) {
      throw new Error("Analysis delta query source path did not use the configured artifact root");
    }
    if (analysisAggregates.json.source.path !== normalizedArtifactRoot) {
      throw new Error(
        "Analysis aggregate query source path did not use the configured artifact root",
      );
    }
    if (analysisSignals.json.source.path !== normalizedArtifactRoot) {
      throw new Error("Analysis signal query source path did not use the configured artifact root");
    }
    if (analysisClusters.json.source.path !== normalizedArtifactRoot) {
      throw new Error("Analysis cluster query source path did not use the configured artifact root");
    }
    if (!Array.isArray(analysisCases.json.rows)) {
      throw new Error("Analysis case query did not return rows");
    }
    if (!Array.isArray(analysisDeltas.json.rows)) {
      throw new Error("Analysis delta query did not return rows");
    }
    if (!Array.isArray(analysisAggregates.json.rows)) {
      throw new Error("Analysis aggregate query did not return rows");
    }
    if (!Array.isArray(analysisSignals.json.rows)) {
      throw new Error("Analysis signal query did not return rows");
    }
    if (!Array.isArray(analysisClusters.json.rows)) {
      throw new Error("Analysis cluster query did not return rows");
    }
    if (
      !analysisClusters.json.rows.some(
        (row) =>
          row &&
          typeof row.cluster_id === "string" &&
          typeof row.cluster_kind === "string" &&
          Array.isArray(row.representative_evidence),
      )
    ) {
      throw new Error("Analysis cluster query did not expose recurring cluster summaries");
    }
    if (
      !analysisSignals.json.rows.some(
        (row) =>
          row &&
          typeof row.report_id === "string" &&
          row.report_id === comparisonReportId &&
          row.governance_recommendation &&
          typeof row.governance_recommendation.action === "string",
      )
    ) {
      throw new Error(
        "Analysis signal query did not expose a governance recommendation for the saved comparison",
      );
    }
    if (
      !comparisonDetail.governanceRecommendation.history_context ||
      typeof comparisonDetail.governanceRecommendation.history_context.scope_kind !== "string" ||
      typeof comparisonDetail.governanceRecommendation.history_context.scope_value !== "string"
    ) {
      throw new Error(
        "Comparison detail did not expose the persisted governance history context",
      );
    }
    if (
      !savedSignalRow ||
      !savedSignalRow.governance_recommendation ||
      !savedSignalRow.governance_recommendation.history_context ||
      typeof savedSignalRow.governance_recommendation.history_context.scope_kind !== "string" ||
      typeof savedSignalRow.governance_recommendation.history_context.scope_value !== "string"
    ) {
      throw new Error(
        "Analysis signal query did not expose the governance history context for the saved comparison",
      );
    }
    if (matchedFamilyId !== null) {
      if (!datasetVersions) {
        throw new Error("Dataset versions payload was not fetched for the matched family");
      }
      if (datasetVersions.family_id !== matchedFamilyId) {
        throw new Error("Dataset versions payload did not match the selected family");
      }
      if (
        !datasetVersions.history ||
        !datasetVersions.history.dataset_health ||
        !datasetVersions.history.dataset_health.trend ||
        typeof datasetVersions.history.dataset_health.trend.label !== "string"
      ) {
        throw new Error("Dataset versions payload did not expose family health history");
      }
    }
    for (const [label, durationMs] of [
      ["cases", analysisCases.durationMs],
      ["deltas", analysisDeltas.durationMs],
      ["aggregates", analysisAggregates.durationMs],
      ["signals", analysisSignals.durationMs],
      ["clusters", analysisClusters.durationMs],
    ]) {
      if (durationMs > QUERY_LATENCY_BUDGET_MS) {
        throw new Error(
          `Analysis ${label} query exceeded ${QUERY_LATENCY_BUDGET_MS}ms (${durationMs.toFixed(1)}ms)`,
        );
      }
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
        `Query latency (cases): ${analysisCases.durationMs.toFixed(1)}ms`,
        `Query latency (deltas): ${analysisDeltas.durationMs.toFixed(1)}ms`,
        `Query latency (aggregates): ${analysisAggregates.durationMs.toFixed(1)}ms`,
        `Query latency (signals): ${analysisSignals.durationMs.toFixed(1)}ms`,
        `Query latency (clusters): ${analysisClusters.durationMs.toFixed(1)}ms`,
        "Verified endpoints:",
        "- overview",
        "- runs inventory",
        "- run detail",
        "- comparisons inventory",
        "- comparison detail",
        "- analysis query (cases)",
        "- analysis query (deltas)",
        "- analysis query (aggregates)",
        "- analysis query (signals)",
        "- analysis query (clusters)",
        "- governance recommendation payloads",
        "- governance history context payloads",
        ...(matchedFamilyId === null ? [] : ["- dataset family health history"]),
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
  const ownsArtifactRoot = !options.artifactRoot && options.mode !== "existing";
  const artifactRoot = options.artifactRoot
    ? path.resolve(options.artifactRoot)
    : options.mode === "existing"
      ? repoRoot
      : path.resolve(await mkdtemp(path.join(tmpdir(), "failure-lab-ui-smoke-")));

  try {
    let selection;
    if (options.mode === "existing") {
      selection = await resolveExistingArtifacts(artifactRoot);
    } else if (options.mode === "ollama-stub") {
      selection = await prepareOllamaArtifacts(artifactRoot);
    } else if (options.mode === "anthropic-stub") {
      selection = await prepareAnthropicArtifacts(artifactRoot);
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
