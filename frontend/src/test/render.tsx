import { render } from "@testing-library/react";
import { vi } from "vitest";

import { App } from "@/app/App";
import type { DatasetFamiliesState, GateState } from "@/app/router";
import type {
  ArtifactShellState,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";
import {
  buildDatasetFamiliesState,
  buildGateState,
  buildReadyArtifactState,
  buildReadyComparisonInventoryState,
  buildReadyRunInventoryState,
} from "@/test/factories";

type StateOverrides = {
  initialArtifactState?: ArtifactShellState;
  initialRunInventoryState?: RunInventoryState;
  initialComparisonInventoryState?: ComparisonInventoryState;
  initialDatasetFamiliesState?: DatasetFamiliesState;
  initialGateState?: GateState;
};

/**
 * Render the App on a MemoryRouter with all five initial states supplied so
 * the shell-level loaders never hit the network — only page-level fetches
 * (comparison detail, run detail, query, dataset versions, …) reach the stub.
 */
export function renderApp(
  initialEntries: string[] = ["/"],
  overrides: StateOverrides = {},
) {
  return render(
    <App
      useMemoryRouter
      initialEntries={initialEntries}
      initialArtifactState={overrides.initialArtifactState ?? buildReadyArtifactState()}
      initialRunInventoryState={
        overrides.initialRunInventoryState ?? buildReadyRunInventoryState()
      }
      initialComparisonInventoryState={
        overrides.initialComparisonInventoryState ?? buildReadyComparisonInventoryState()
      }
      initialDatasetFamiliesState={
        overrides.initialDatasetFamiliesState ?? buildDatasetFamiliesState()
      }
      initialGateState={overrides.initialGateState ?? buildGateState("blocked")}
    />,
  );
}

export type FetchRoute = {
  /** URL substring to match (e.g. "comparison-detail.json"). */
  match: string;
  /** Wire payload or a function of the request; return { status, body } for errors. */
  respond:
    | Record<string, unknown>
    | ((url: string, init?: RequestInit) => unknown | { __status: number; body: unknown });
};

export type RecordedFetch = { url: string; init?: RequestInit };

/**
 * Stub global fetch, routing requests by URL substring. Unmatched URLs reject
 * loudly. Returns the list of recorded calls for request assertions.
 * Pair with `vi.unstubAllGlobals()` in afterEach.
 */
export function stubFetch(routes: FetchRoute[]): RecordedFetch[] {
  const calls: RecordedFetch[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      const route = routes.find((candidate) => url.includes(candidate.match));
      if (!route) {
        throw new Error(`unstubbed fetch: ${url}`);
      }
      const outcome =
        typeof route.respond === "function" ? route.respond(url, init) : route.respond;
      if (
        outcome !== null &&
        typeof outcome === "object" &&
        "__status" in (outcome as Record<string, unknown>)
      ) {
        const { __status, body } = outcome as { __status: number; body: unknown };
        return {
          ok: __status >= 200 && __status < 300,
          status: __status,
          json: async () => body,
        } as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => outcome,
      } as Response;
    }),
  );
  return calls;
}
