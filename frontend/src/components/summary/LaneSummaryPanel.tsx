import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel, formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { SummaryRouteLanePanel, SummaryRouteMethodStatus } from "@/lib/summaryRoute";
import { cn } from "@/lib/utils";

type LaneSummaryPanelProps = {
  lane: SummaryRouteLanePanel;
  scope: TraceScope;
};

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
  const previewRows = lane.methodPreviewRows
    .filter((row) => scope === "all" || row.scope === "official")
    .slice(0, 3);

  return (
    <section className="grid gap-4 rounded-[20px] border border-border/70 bg-card/45 p-4 sm:p-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.9fr)]">
      <div className="space-y-4">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="muted">Lane</Badge>
            <Badge {...getStatusBadgeProps(lane.status)}>{formatLabel(lane.status)}</Badge>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">{lane.label}</h2>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">{lane.summary}</p>
          </div>
        </div>

        <dl className="grid gap-3 sm:grid-cols-2">
          {lane.metrics.map((metric) => {
            const deltaTone = getMetricTextTone(metric.deltaVsBaseline, Boolean(metric.lowerIsBetter));

            return (
              <div
                key={`${lane.laneId}-${metric.label}`}
                className="rounded-[16px] border border-border/70 bg-background/55 px-4 py-3"
              >
                <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {metric.label}
                </dt>
                <dd className="mt-2 space-y-1">
                  <p className="text-lg font-semibold text-foreground">{formatMetric(metric.value)}</p>
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

      <div className="rounded-[18px] border border-border/70 bg-background/55 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Method preview
          </p>
          <p className="text-xs text-muted-foreground">Baseline first</p>
        </div>

        <div className="mt-3 space-y-3">
          {previewRows.map((row) => {
            const statusBadgeProps = getStatusBadgeProps(row.status);

            return (
              <div key={`${lane.laneId}-${row.methodId}`} className="rounded-[14px] border border-border/70 px-3 py-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="default">{row.label}</Badge>
                    <Badge {...statusBadgeProps}>{formatLabel(row.status)}</Badge>
                    {row.scope === "exploratory" ? <Badge tone="exploratory">Exploratory</Badge> : null}
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">{row.summary}</p>
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
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
