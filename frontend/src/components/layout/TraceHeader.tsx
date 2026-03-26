import { Fragment } from "react";
import { Link, matchPath, useLocation, useParams } from "react-router-dom";

import { NAVIGATION_ITEMS } from "@/app/router";
import { useTraceScope } from "@/app/scope";
import { Button } from "@/components/ui/button";
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

function getTraceHref(
  label: string,
  params: Readonly<Record<string, string | undefined>>,
  scope: "official" | "all",
) {
  switch (label) {
    case "Verdict":
      return buildScopedPath("/", scope);
    case "Lane":
      return params.laneId ? buildScopedPath(`/lane/${params.laneId}`, scope) : null;
    case "Method":
      return params.laneId && params.methodId
        ? buildScopedPath(`/lane/${params.laneId}/${params.methodId}`, scope)
        : null;
    case "Run":
      return params.runId ? buildScopedPath(`/run/${params.runId}`, scope) : null;
    case "Artifact":
      return params.entityId
        ? buildScopedPath(`/debug/raw/${params.entityId}`, scope)
        : null;
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
  const activeRouteIndex = NAVIGATION_ITEMS.findIndex((item) => item.label === activeRouteLabel);

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
                  const isAvailable = href !== null && index <= activeRouteIndex;
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
