import type { KeyboardEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel, formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { SummaryRouteLanePanel, SummaryRouteMethodStatus } from "@/lib/summaryRoute";
import { cn } from "@/lib/utils";

type LaneSummaryPanelProps = {
  lane: SummaryRouteLanePanel;
  scope: TraceScope;
};

function withScope(path: string, scope: TraceScope) {
  return `${path}?scope=${scope}`;
}

function getStatusBadgeProps(status: SummaryRouteMethodStatus | SummaryRouteLanePanel["status"]) {
  if (status === "stable") {
    return { tone: "accent" as const };
  }

  if (status === "failure") {
    return {
      tone: "default" as const,
      className: "border border-destructive/25 bg-destructive/10 text-destructive",
    };
  }

  return { tone: "default" as const };
}

export function LaneSummaryPanel({ lane, scope }: LaneSummaryPanelProps) {
  const navigate = useNavigate();

  function openLane() {
    navigate(withScope(`/lane/${lane.laneId}`, scope));
  }

  function handlePanelKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    openLane();
  }

  return (
    <section
      aria-label={`${lane.label} lane`}
      className="grid cursor-pointer gap-4 rounded-lg border border-border/60 bg-transparent p-3 transition-colors hover:border-foreground/30 sm:p-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.9fr)]"
      data-testid={`${lane.laneId}-lane-panel`}
      onClick={openLane}
      onKeyDown={handlePanelKeyDown}
      role="link"
      tabIndex={0}
    >
      <div className="space-y-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="muted">Lane</Badge>
            <Badge {...getStatusBadgeProps(lane.status)}>{formatLabel(lane.status)}</Badge>
          </div>
          <div className="space-y-1.5">
            <h2 className="text-xl font-semibold tracking-[-0.04em] text-foreground sm:text-2xl">
              {lane.label}
            </h2>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">{lane.summary}</p>
          </div>
        </div>

        <dl className="grid gap-3 sm:grid-cols-2">
          {lane.metrics.map((metric) => {
            const deltaTone = getMetricTextTone(metric.deltaVsBaseline, Boolean(metric.lowerIsBetter));

            return (
              <div
                key={`${lane.laneId}-${metric.label}`}
                className="border-t border-border/60 px-0 pt-3 first:border-t-0 first:pt-0"
              >
                <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {metric.label}
                </dt>
                <dd className="mt-1.5 space-y-0.5">
                  <p className="text-base font-semibold text-foreground sm:text-lg">
                    {formatMetric(metric.value)}
                  </p>
                  <p className={cn("text-sm", deltaTone)}>
                    {metric.deltaVsBaseline === undefined || metric.deltaVsBaseline === null
                      ? "No baseline delta"
                      : `${formatSignedMetric(metric.deltaVsBaseline)} vs baseline`}
                  </p>
                </dd>
              </div>
            );
          })}
        </dl>
      </div>

      <div className="space-y-3 lg:border-l lg:border-border/60 lg:pl-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Method preview
          </p>
          <p className="text-xs text-muted-foreground">Baseline first</p>
        </div>

        <div className="space-y-3">
          {lane.officialMethodPreviewRows.map((row) => {
            const statusBadgeProps = getStatusBadgeProps(row.status);

            return (
              <div
                key={`${lane.laneId}-${row.methodId}`}
                className="border-t border-border/60 pt-3 first:border-t-0 first:pt-0"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      className="text-sm font-semibold text-foreground underline decoration-border underline-offset-4 hover:text-primary"
                      onClick={(event) => {
                        event.stopPropagation();
                      }}
                      to={withScope(`/lane/${lane.laneId}/${row.methodId}`, scope)}
                    >
                      {row.label}
                    </Link>
                    <Badge {...statusBadgeProps}>{formatLabel(row.status)}</Badge>
                    {row.scope === "exploratory" ? <Badge tone="exploratory">Exploratory</Badge> : null}
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">{row.summary}</p>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold text-foreground">{row.headlineMetric.label}</span>
                  <span className="text-foreground">{formatMetric(row.headlineMetric.value)}</span>
                  <span
                    className={cn(
                      "text-muted-foreground",
                      getMetricTextTone(
                        row.headlineMetric.deltaVsBaseline,
                        Boolean(row.headlineMetric.lowerIsBetter),
                      ),
                    )}
                  >
                    {row.headlineMetric.deltaVsBaseline === undefined ||
                    row.headlineMetric.deltaVsBaseline === null
                      ? "baseline reference"
                      : `${formatSignedMetric(row.headlineMetric.deltaVsBaseline)} vs baseline`}
                  </span>
                </div>
              </div>
            );
          })}
          {lane.exploratoryMethodPreviewRows.length > 0 ? (
            <div className="border-t border-dashed border-border/70 pt-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="exploratory">Exploratory methods</Badge>
                <p className="text-xs text-muted-foreground">
                  Shown because scope includes exploratory evidence.
                </p>
              </div>
            </div>
          ) : null}
          {lane.exploratoryMethodPreviewRows.map((row) => {
            const statusBadgeProps = getStatusBadgeProps(row.status);

            return (
              <div
                key={`${lane.laneId}-${row.methodId}`}
                className="border-t border-dashed border-border/60 pt-3"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      className="text-sm font-semibold text-foreground underline decoration-border underline-offset-4 hover:text-primary"
                      onClick={(event) => {
                        event.stopPropagation();
                      }}
                      to={withScope(`/lane/${lane.laneId}/${row.methodId}`, scope)}
                    >
                      {row.label}
                    </Link>
                    <Badge {...statusBadgeProps}>{formatLabel(row.status)}</Badge>
                    <Badge tone="exploratory">Exploratory</Badge>
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">{row.summary}</p>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold text-foreground">{row.headlineMetric.label}</span>
                  <span className="text-foreground">{formatMetric(row.headlineMetric.value)}</span>
                  <span
                    className={cn(
                      "text-muted-foreground",
                      getMetricTextTone(
                        row.headlineMetric.deltaVsBaseline,
                        Boolean(row.headlineMetric.lowerIsBetter),
                      ),
                    )}
                  >
                    {row.headlineMetric.deltaVsBaseline === undefined ||
                    row.headlineMetric.deltaVsBaseline === null
                      ? "baseline reference"
                      : `${formatSignedMetric(row.headlineMetric.deltaVsBaseline)} vs baseline`}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
