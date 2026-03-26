import { Fragment } from "react";
import { Link, matchPath, useLocation, useParams } from "react-router-dom";

import { NAVIGATION_ITEMS } from "@/app/router";
import { useTraceScope } from "@/app/scope";
import { Button } from "@/components/ui/button";
import {
  buildLaneRouteModel,
  type LaneRouteLaneId,
  type LaneRouteMethodId,
} from "@/lib/laneRoute";
import { buildSummaryRouteModel } from "@/lib/summaryRoute";
import { cn } from "@/lib/utils";

function getActiveRouteLabel(pathname: string) {
  const activeRoute =
    NAVIGATION_ITEMS.find((item) => matchPath({ path: item.path, end: true }, pathname)) ??
    NAVIGATION_ITEMS[0];

  return activeRoute.label;
}

function buildScopedPath(path: string, scope: "official" | "all") {
  return `${path}?scope=${scope}`;
}

function inferMethodIdFromRunId(runId: string | undefined): LaneRouteMethodId | null {
  if (!runId) {
    return null;
  }

  const candidates: LaneRouteMethodId[] = [
    "temperature_scaling",
    "reweighting",
    "group_dro",
    "baseline",
  ];

  return candidates.find((candidate) => runId.includes(candidate)) ?? null;
}

function inferLaneIdFromMethodId(methodId: LaneRouteMethodId | null): LaneRouteLaneId {
  if (methodId === "temperature_scaling") {
    return "calibration";
  }

  return "robustness";
}

function pickPreferredMethodId(
  laneId: LaneRouteLaneId,
  scope: "official" | "all",
  preferredMethodId?: string,
) {
  const laneModel = buildLaneRouteModel(laneId, scope);
  const explicitMethod =
    preferredMethodId &&
    laneModel.rows.find((row) => row.methodId === preferredMethodId);

  if (explicitMethod) {
    return explicitMethod.methodId;
  }

  return (
    laneModel.rows.find((row) => row.methodId !== "baseline")?.methodId ??
    laneModel.rows[0]?.methodId ??
    "baseline"
  );
}

function pickPreferredRunId(
  laneId: LaneRouteLaneId,
  methodId: LaneRouteMethodId,
  scope: "official" | "all",
  explicitRunId?: string,
) {
  if (explicitRunId) {
    return explicitRunId;
  }

  const laneModel = buildLaneRouteModel(laneId, scope);
  const methodRow = laneModel.rows.find((row) => row.methodId === methodId) ?? laneModel.rows[0];
  const preferredRun =
    methodRow?.runs.find((run) => run.scope === "official") ?? methodRow?.runs[0];

  return preferredRun?.runId ?? "distilbert_reweighting_seed_13";
}

function resolveTraceTargets(
  params: Readonly<Record<string, string | undefined>>,
  scope: "official" | "all",
) {
  const summaryModel = buildSummaryRouteModel(scope);
  const inferredMethodId = inferMethodIdFromRunId(params.runId);
  const laneId = (params.laneId as LaneRouteLaneId | undefined) ??
    inferLaneIdFromMethodId(inferredMethodId) ??
    summaryModel.laneOrder[0];
  const methodId = pickPreferredMethodId(laneId, scope, params.methodId ?? inferredMethodId ?? undefined);
  const runId = pickPreferredRunId(laneId, methodId, scope, params.runId);
  const entityId = params.entityId ?? `run_${runId}`;

  return { laneId, methodId, runId, entityId };
}

function getTraceHref(
  label: string,
  params: Readonly<Record<string, string | undefined>>,
  scope: "official" | "all",
) {
  const targets = resolveTraceTargets(params, scope);

  switch (label) {
    case "Verdict":
      return buildScopedPath("/", scope);
    case "Lane":
      return buildScopedPath(`/lane/${targets.laneId}`, scope);
    case "Method":
      return buildScopedPath(`/lane/${targets.laneId}/${targets.methodId}`, scope);
    case "Run":
      return buildScopedPath(`/run/${targets.runId}`, scope);
    case "Artifact":
      return buildScopedPath(`/debug/raw/${targets.entityId}`, scope);
    default:
      return null;
  }
}

export function TraceHeader() {
  const location = useLocation();
  const params = useParams();
  const { scope, setScope } = useTraceScope();
  const activeRouteLabel = getActiveRouteLabel(location.pathname);
  const homeHref = `/?scope=${scope}`;

  return (
    <header className="border-b border-border/70 bg-background/95">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Model Failure Lab
            </p>
            <Link className="text-lg font-semibold tracking-[-0.03em] text-foreground" to={homeHref}>
              Failure Debugger
            </Link>
          </div>
          <div
            aria-label="Trace chain"
            className="flex flex-wrap items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground"
          >
            {NAVIGATION_ITEMS.map((item, index) => (
              <Fragment key={item.path}>
                {index > 0 ? (
                  <span aria-hidden="true" className="text-muted-foreground/70">
                    →
                  </span>
                ) : null}
                {(() => {
                  const href = getTraceHref(item.label, params, scope);
                  const isActive = item.label === activeRouteLabel;
                  const isAvailable = href !== null;
                  const pillClassName = cn(
                    "rounded-full border border-border/70 px-2.5 py-1 transition-colors",
                    isActive && "border-foreground text-foreground",
                    isAvailable && !isActive && "hover:border-foreground/60 hover:text-foreground",
                    !isAvailable && "opacity-50",
                  );

                  if (isActive || href === null || !isAvailable) {
                    return (
                      <span
                        aria-current={isActive ? "page" : undefined}
                        aria-disabled={!isAvailable}
                        className={pillClassName}
                      >
                        {item.label}
                      </span>
                    );
                  }

                  return (
                    <Link className={pillClassName} to={href}>
                      {item.label}
                    </Link>
                  );
                })()}
              </Fragment>
            ))}
          </div>
        </div>

        <div
          aria-label="Trace scope"
          className="flex items-center gap-2 rounded-full border border-border/70 bg-card/70 p-1"
        >
          <Button
            size="sm"
            variant={scope === "official" ? "default" : "ghost"}
            aria-pressed={scope === "official"}
            onClick={() => setScope("official")}
          >
            Official
          </Button>
          <Button
            size="sm"
            variant={scope === "all" ? "default" : "ghost"}
            aria-pressed={scope === "all"}
            onClick={() => setScope("all")}
          >
            All
          </Button>
        </div>
      </div>
    </header>
  );
}
