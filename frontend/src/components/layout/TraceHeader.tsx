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
import { buildRunRoutePath } from "@/lib/runRoute";
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
  if (
    preferredMethodId === "baseline" ||
    preferredMethodId === "reweighting" ||
    preferredMethodId === "temperature_scaling" ||
    preferredMethodId === "group_dro"
  ) {
    return preferredMethodId;
  }

  const laneModel = buildLaneRouteModel(laneId, scope);
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
  const methodRow = laneModel.rows.find((row) => row.methodId === methodId);
  const preferredRun =
    methodRow?.runs.find((run) => run.scope === "official") ?? methodRow?.runs[0];

  if (preferredRun) {
    return preferredRun.runId;
  }

  return `distilbert_${methodId}_seed_13`;
}

function resolveTraceTargets(
  params: Readonly<Record<string, string | undefined>>,
  scope: "official" | "all",
  searchParams: URLSearchParams,
) {
  const summaryModel = buildSummaryRouteModel(scope);
  const inferredMethodId = inferMethodIdFromRunId(params.runId);
  const laneId = (params.laneId as LaneRouteLaneId | undefined) ??
    ((searchParams.get("lane") as LaneRouteLaneId | null) ?? undefined) ??
    inferLaneIdFromMethodId(inferredMethodId) ??
    summaryModel.laneOrder[0];
  const methodId = pickPreferredMethodId(
    laneId,
    scope,
    params.methodId ?? searchParams.get("method") ?? inferredMethodId ?? undefined,
  );
  const runId = pickPreferredRunId(laneId, methodId, scope, params.runId);
  const entityId = params.entityId ?? `run_${runId}`;

  return { laneId, methodId, runId, entityId };
}

function getTraceHref(
  label: string,
  params: Readonly<Record<string, string | undefined>>,
  scope: "official" | "all",
  searchParams: URLSearchParams,
) {
  const targets = resolveTraceTargets(params, scope, searchParams);

  switch (label) {
    case "Verdict":
      return buildScopedPath("/", scope);
    case "Lane":
      return buildScopedPath(`/lane/${targets.laneId}`, scope);
    case "Method":
      return buildScopedPath(`/lane/${targets.laneId}/${targets.methodId}`, scope);
    case "Run":
      return buildRunRoutePath(targets.runId, scope, {
        laneId: targets.laneId,
        methodId: targets.methodId,
      });
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
  const searchParams = new URLSearchParams(location.search);

  return (
    <header className="border-b border-border/60 bg-background/95">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="space-y-1.5">
          <div className="space-y-0.5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Model Failure Lab
            </p>
            <Link className="text-base font-semibold tracking-[-0.03em] text-foreground sm:text-lg" to={homeHref}>
              Failure Debugger
            </Link>
          </div>
          <div
            aria-label="Trace chain"
            className="flex flex-wrap items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground"
          >
            {NAVIGATION_ITEMS.map((item, index) => (
              <Fragment key={item.path}>
                {index > 0 ? (
                  <span aria-hidden="true" className="text-muted-foreground/70">
                    →
                  </span>
                ) : null}
                {(() => {
                  const href = getTraceHref(item.label, params, scope, searchParams);
                  const isActive = item.label === activeRouteLabel;
                  const isAvailable = href !== null;
                  const pillClassName = cn(
                    "rounded-md border border-border/60 px-2 py-1 transition-colors",
                    isActive && "border-foreground/70 bg-muted/20 text-foreground",
                    isAvailable && !isActive && "hover:border-foreground/50 hover:text-foreground",
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
          className="flex items-center gap-1 rounded-md border border-border/60 bg-muted/10 p-1"
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
