/**
 * The bridge, driven over real HTTP against a real workspace.
 *
 * Until this file existed, `frontend/server/artifactBridge.ts` (then `vite.config.ts`) was
 * the largest file in the frontend and the only one no test could import. The CSRF check,
 * the artifact-id validation, the flag mapping into `scripts/query_bridge.py`, and the two
 * payloads composed here in TypeScript rather than by the engine were all unexercised --
 * which is how a `404` branch shipped that could never be taken.
 *
 * These tests mount the plugin's own middleware on a `node:http` server and make real
 * requests, so routing, method checks, status codes and payload shape are all covered by
 * the same path a browser takes. The Python-backed endpoints need an interpreter and a
 * built index, so they are skipped when `scripts/query_bridge.py` cannot run. Every guard --
 * id validation, CSRF, method checks, missing-artifact handling -- runs unconditionally,
 * because those are the paths a hostile caller reaches without any workspace at all.
 *
 * @vitest-environment node
 */

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import type { IncomingMessage, ServerResponse } from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";

import { failureLabArtifactsPlugin } from "../artifactBridge";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "../../..");
const DEMO_RUNS = path.join(REPO_ROOT, "examples", "regression_demo", "runs");
const COMPARISON_ID = "compare_8ba8496a_to_dda18a0e_66320e7c";

type Middleware = (
  req: IncomingMessage,
  res: ServerResponse,
  next: (error?: unknown) => void,
) => void;

async function mountBridge(
  artifactRoot: string,
): Promise<{ server: http.Server; origin: string }> {
  const handlers: Middleware[] = [];
  const plugin = failureLabArtifactsPlugin({ repoRoot: REPO_ROOT, artifactRoot });
  // The plugin registers the same middleware on both the dev and the preview server; the
  // shim below is the smallest thing that satisfies the shape it expects.
  const configureServer = plugin.configureServer as unknown as (s: {
    middlewares: { use: (h: Middleware) => void };
  }) => void;
  configureServer({ middlewares: { use: (h: Middleware) => handlers.push(h) } });

  const created = http.createServer((req, res) => {
    let index = 0;
    const next = () => {
      const handler = handlers[index++];
      if (!handler) {
        res.statusCode = 404;
        res.end("{}");
        return;
      }
      handler(req, res, next);
    };
    next();
  });
  await new Promise<void>((resolve) => created.listen(0, "127.0.0.1", resolve));
  const address = created.address();
  if (typeof address === "string" || address === null) {
    throw new Error("bridge test server did not bind a port");
  }
  return { server: created, origin: `http://127.0.0.1:${address.port}` };
}

/**
 * Build the fixture workspace at module scope, not in `beforeAll`.
 *
 * `it.runIf(...)` is evaluated during collection, which happens before any hook runs -- so
 * a flag set in `beforeAll` is always still `false` when the skip decision is made, and
 * every Python-backed test silently skipped. Top-level await makes the flag true by the
 * time the suite is collected.
 */
const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "failure-lab-bridge-"));
fs.mkdirSync(path.join(workspace, "runs"), { recursive: true });
for (const name of ["baseline", "candidate"]) {
  fs.cpSync(path.join(DEMO_RUNS, name), path.join(workspace, "runs", name), {
    recursive: true,
  });
}

/** True once the engine has produced reports, a comparison and an index in the workspace. */
const pythonReady = (() => {
  try {
    const env = { ...process.env, PYTHONPATH: path.join(REPO_ROOT, "src") };
    const run = (args: string[]) =>
      execFileSync("python3", ["-m", "model_failure_lab", ...args, "--root", workspace], {
        cwd: REPO_ROOT,
        env,
        stdio: "pipe",
      });
    // Bare run ids: inside a workspace the engine resolves them under `runs/`.
    run(["compare", "baseline", "candidate"]);
    run(["report", "--run", "baseline"]);
    run(["report", "--run", "candidate"]);
    run(["index", "rebuild"]);
    return true;
  } catch {
    return false;
  }
})();

// Top-level await: the port must exist before any test body runs.
const { server, origin } = await mountBridge(workspace);

async function call(
  urlPath: string,
  init: RequestInit & { headers?: Record<string, string> } = {},
): Promise<{ status: number; body: unknown }> {
  const response = await fetch(`${origin}${urlPath}`, init);
  const text = await response.text();
  let body: unknown = text;
  try {
    body = JSON.parse(text);
  } catch {
    /* a non-JSON body is itself the assertion in some cases */
  }
  return { status: response.status, body };
}

/**
 * A request with an arbitrary `Host` header.
 *
 * `fetch` treats `Host` as a forbidden header name and silently drops it, so the DNS-
 * rebinding case cannot be expressed with it -- the request would arrive addressed to the
 * real host and pass. `node:http` sets exactly what it is given.
 */
function rawCall(
  urlPath: string,
  { host, method = "GET", body }: { host: string; method?: string; body?: string },
): Promise<{ status: number; body: unknown }> {
  const { port } = server.address() as { port: number };
  return new Promise((resolve, reject) => {
    const request = http.request(
      {
        host: "127.0.0.1",
        port,
        path: urlPath,
        method,
        headers: {
          Host: host,
          ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        },
      },
      (response) => {
        let text = "";
        response.on("data", (chunk) => (text += chunk));
        response.on("end", () => {
          let parsed: unknown = text;
          try {
            parsed = JSON.parse(text);
          } catch {
            /* the raw text is the assertion */
          }
          resolve({ status: response.statusCode ?? 0, body: parsed });
        });
      },
    );
    request.on("error", reject);
    if (body !== undefined) {
      request.write(body);
    }
    request.end();
  });
}

afterAll(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
  fs.rmSync(workspace, { recursive: true, force: true });
});

// ---------------------------------------------------------------------------------------
// Path traversal and argument injection
// ---------------------------------------------------------------------------------------

describe("artifact id validation", () => {
  const hostile = [
    "../../../../etc",
    "..",
    "a/b",
    "a\\b",
    "/etc/passwd",
  ];

  it("rejects a percent-encoded traversal, which the server decodes before it sees it", async () => {
    // Sent raw rather than re-encoded, so the query parser hands the handler "../../etc".
    const { status } = await call(
      "/__failure_lab__/artifacts/run-detail.json?runId=%2e%2e%2f%2e%2e%2fetc",
    );
    expect(status).toBe(400);
  });

  it.each(hostile)("rejects run id %j with 400, not 500", async (runId) => {
    const { status, body } = await call(
      `/__failure_lab__/artifacts/run-detail.json?runId=${encodeURIComponent(runId)}`,
    );
    // 400, because a crafted id is the caller's mistake. Answering 500 told the caller the
    // server had broken, and made a rejected traversal indistinguishable from a crash.
    expect(status).toBe(400);
    expect(body).toMatchObject({ message: expect.stringContaining("invalid path segment") });
  });

  it("never leaks the absolute workspace path in an error body", async () => {
    const { body } = await call(
      "/__failure_lab__/artifacts/run-detail.json?runId=" + encodeURIComponent("../../etc"),
    );
    expect(JSON.stringify(body)).not.toContain(workspace);
    expect(JSON.stringify(body)).not.toContain(REPO_ROOT);
  });

  it("requires the id parameter at all", async () => {
    expect((await call("/__failure_lab__/artifacts/run-detail.json")).status).toBe(400);
    expect((await call("/__failure_lab__/artifacts/comparison-detail.json")).status).toBe(400);
  });
});

// ---------------------------------------------------------------------------------------
// Missing vs broken: the branch that could not be reached
// ---------------------------------------------------------------------------------------

describe("missing artifacts", () => {
  it("answers 404 for a run that does not exist", async () => {
    // `bridgeErrorMessage` always returns its fallback string, so the old check --
    // `message.includes("ENOENT")` on that return value -- was dead code and every miss
    // answered 500.
    const { status, body } = await call(
      "/__failure_lab__/artifacts/run-detail.json?runId=does-not-exist",
    );
    expect(status).toBe(404);
    expect(body).toMatchObject({ message: "run detail failed" });
  });

  it("answers 404 for a comparison that does not exist", async () => {
    const { status } = await call(
      "/__failure_lab__/artifacts/comparison-detail.json?reportId=nope",
    );
    expect(status).toBe(404);
  });
});

// ---------------------------------------------------------------------------------------
// Host check: DNS rebinding is what turns the CSRF check into a formality
// ---------------------------------------------------------------------------------------

describe("host allowlist", () => {
  it("refuses a request addressed to a host this server does not serve", async () => {
    // A rebinding page resolves its own hostname to 127.0.0.1, reaches the bridge, and is
    // then *genuinely* same-origin -- so the CSRF check passes by construction. The host
    // is the only thing that still distinguishes it.
    const { status, body } = await rawCall("/__failure_lab__/artifacts/overview.json", {
      host: "attacker.example",
    });
    expect(status).toBe(403);
    expect(body).toMatchObject({ message: expect.stringContaining("not allowed") });
  });

  it("refuses a disallowed host on the write endpoints too", async () => {
    for (const writePath of WRITE_PATHS) {
      const { status } = await rawCall(writePath, {
        host: "attacker.example",
        method: "POST",
        body: "{}",
      });
      expect(status, writePath).toBe(403);
    }
  });

  it.each(["localhost:5174", "127.0.0.1:5174", "app.localhost:5174", "[::1]:5174"])(
    "serves %s",
    async (host) => {
      const { status } = await rawCall("/__failure_lab__/artifacts/overview.json", { host });
      expect(status).not.toBe(403);
    },
  );

  it("leaves non-bridge paths to the rest of the server", async () => {
    // The check is scoped to `/__failure_lab__/`; Vite owns everything else.
    const { status } = await rawCall("/index.html", { host: "attacker.example" });
    expect(status).toBe(404); // our shim's terminal handler, i.e. it was passed through
  });
});

// ---------------------------------------------------------------------------------------
// CSRF: the only thing standing between a visited web page and a local write
// ---------------------------------------------------------------------------------------

const WRITE_PATHS = [
  "/__failure_lab__/artifacts/harvest.json",
  "/__failure_lab__/artifacts/regression-pack.json",
  "/__failure_lab__/artifacts/dataset-evolve.json",
];

describe("write endpoints", () => {
  it.each(WRITE_PATHS)("%s rejects GET", async (writePath) => {
    const { status, body } = await call(writePath);
    expect(status).toBe(405);
    expect(body).toMatchObject({ message: expect.stringContaining("POST") });
  });

  it.each(WRITE_PATHS)("%s rejects a cross-site POST", async (writePath) => {
    const { status, body } = await call(writePath, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://evil.example",
        "Sec-Fetch-Site": "cross-site",
      },
      body: "{}",
    });
    expect(status).toBe(403);
    expect(body).toMatchObject({ message: "cross-origin writes are not allowed" });
  });

  it.each(WRITE_PATHS)("%s rejects a same-site-but-not-same-origin POST", async (writePath) => {
    // `same-site` covers a sibling subdomain, which is a different origin.
    const { status } = await call(writePath, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Sec-Fetch-Site": "same-site" },
      body: "{}",
    });
    expect(status).toBe(403);
  });

  it.each(WRITE_PATHS)("%s rejects an Origin whose host is not ours", async (writePath) => {
    const { status } = await call(writePath, {
      method: "POST",
      headers: { "Content-Type": "application/json", Origin: "http://localhost:9999" },
      body: "{}",
    });
    expect(status).toBe(403);
  });

  it.each(WRITE_PATHS)("%s admits a genuine same-origin POST past the CSRF check", async (writePath) => {
    const { status } = await call(writePath, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: origin,
        "Sec-Fetch-Site": "same-origin",
      },
      body: "{}",
    });
    // Past the guard: the request is now rejected on its *contents* (400/500), never 403.
    expect(status).not.toBe(403);
  });

  it("rejects a body that is not a JSON object", async () => {
    for (const body of ["", "[]", "null", "not json"]) {
      const { status } = await call(WRITE_PATHS[0], {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      expect(status, `body ${JSON.stringify(body)}`).toBe(400);
    }
  });
});

// ---------------------------------------------------------------------------------------
// The two payloads composed here in TypeScript rather than by the engine
// ---------------------------------------------------------------------------------------

describe("TypeScript-composed detail payloads", () => {
  it.runIf(pythonReady)("run-detail reports the run's real metrics and cases", async () => {
    const { status, body } = await call(
      "/__failure_lab__/artifacts/run-detail.json?runId=baseline",
    );
    expect(status).toBe(200);
    const payload = body as {
      run: { runId: string; dataset: string; status: string };
      metrics: { attemptedCaseCount: number; failureRate: number | null };
      cases: unknown[];
      lenses: { allCaseIds: string[] };
    };
    expect(payload.run.runId).toBe("baseline");
    expect(payload.run.dataset).toBe("support-regression-demo-v1");
    expect(payload.metrics.attemptedCaseCount).toBe(8);
    // The demo baseline is the clean run: nothing fails.
    expect(payload.metrics.failureRate).toBe(0);
    expect(payload.cases).toHaveLength(8);
    expect(payload.lenses.allCaseIds).toHaveLength(8);
  });

  it.runIf(pythonReady)("run-detail reports the candidate's four regressions", async () => {
    const { body } = await call("/__failure_lab__/artifacts/run-detail.json?runId=candidate");
    const payload = body as { metrics: { failureRate: number | null } };
    expect(payload.metrics.failureRate).toBe(0.5);
  });

  it.runIf(pythonReady)("comparison-detail agrees with the engine's own verdict", async () => {
    const { status, body } = await call(
      `/__failure_lab__/artifacts/comparison-detail.json?reportId=${COMPARISON_ID}`,
    );
    expect(status).toBe(200);
    const payload = body as {
      comparison: { compatible: boolean; reportId: string };
      signal: { verdict: string; regressionScore: number };
      coverage: { sharedCaseCount: number };
      caseDeltas: { transitionType: string }[];
    };
    expect(payload.comparison.reportId).toBe(COMPARISON_ID);
    expect(payload.comparison.compatible).toBe(true);
    expect(payload.signal.verdict).toBe("regression");
    expect(payload.signal.regressionScore).toBeCloseTo(0.5, 6);
    expect(payload.coverage.sharedCaseCount).toBe(8);
    expect(
      payload.caseDeltas.filter((d) => d.transitionType === "no_failure_to_failure"),
    ).toHaveLength(4);
  });
});

// ---------------------------------------------------------------------------------------
// Routing and flag mapping
// ---------------------------------------------------------------------------------------

describe("routing", () => {
  it("passes unknown paths to the next middleware rather than swallowing them", async () => {
    const { status } = await call("/__failure_lab__/artifacts/not-an-endpoint.json");
    expect(status).toBe(404);
  });

  it.runIf(pythonReady)("serves every read endpoint the console loads on navigation", async () => {
    for (const endpoint of [
      "overview.json",
      "runs.json",
      "comparisons.json",
      "dataset-families.json",
      "dataset-drafts.json",
      "gate.json",
      "baselines.json",
    ]) {
      const { status } = await call(`/__failure_lab__/artifacts/${endpoint}`);
      expect(status, endpoint).toBe(200);
    }
  });

  it.runIf(pythonReady)("maps query filters onto the bridge's own flags", async () => {
    const { status, body } = await call(
      "/__failure_lab__/artifacts/query.json?mode=cases&failureType=hallucination&limit=3",
    );
    expect(status).toBe(200);
    const payload = body as { mode: string; filters: Record<string, unknown> };
    // The filters echoed back are the bridge's proof it forwarded what the UI asked for --
    // a renamed flag shows up here rather than as a silently unfiltered result set.
    expect(payload.mode).toBe("cases");
    expect(payload.filters.failureType).toBe("hallucination");
    expect(payload.filters.limit).toBe(3);
  });

  it.runIf(pythonReady)("cannot be talked into a different bridge argument", async () => {
    // Values reach `execFile` as array elements, so they cannot become separate flags. A
    // flag-shaped value is refused by argparse rather than honoured.
    const { status } = await call(
      "/__failure_lab__/artifacts/query.json?mode=cases&runId=--limit%3D99999",
    );
    expect(status).toBe(500);
  });
});
