import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel, formatMetric } from "@/lib/formatters";
import type { MethodRouteLaneId, MethodRouteRunRow } from "@/lib/methodRoute";
import { buildRunRoutePath } from "@/lib/runRoute";
import { cn } from "@/lib/utils";

type RunTableProps = {
  laneId: MethodRouteLaneId;
  methodId: string;
  methodLabel: string;
  runs: MethodRouteRunRow[];
  scope: TraceScope;
  selectedEntityId: string;
  onSelectRun: (entityId: string) => void;
};

function getStatusBadgeProps(status: MethodRouteRunRow["status"]) {
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

export function RunTable({
  laneId,
  methodId,
  methodLabel,
  runs,
  scope,
  selectedEntityId,
  onSelectRun,
}: RunTableProps) {
  const primaryMetricLabel = laneId === "robustness" ? "Worst-group" : "ECE";

  return (
    <section className="space-y-3">
      <div className="space-y-1">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Seed-first runs
        </h2>
        <p className="text-sm text-muted-foreground">
          Ordered by seed so the route stays consistent before the run inspector lands in the next wave.
        </p>
      </div>

      <div className="overflow-hidden rounded-[16px] border border-border/70">
        <table aria-label={`${methodLabel} runs`} className="min-w-full border-collapse text-sm">
          <thead>
            <tr className="bg-muted/20">
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Run ID
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Seed
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Status
              </th>
              <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {primaryMetricLabel}
              </th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => {
              const primaryMetric =
                run.metrics.find((metric) => metric.label === primaryMetricLabel) ?? run.metrics[0];
              const isSelected = run.entityId === selectedEntityId;

              return (
                <tr
                  key={run.entityId}
                  aria-selected={isSelected}
                  className={cn(
                    "border-t border-border/60 transition-colors",
                    isSelected ? "bg-primary/5" : "hover:bg-muted/20",
                  )}
                  data-testid={`method-run-row-${run.runId}`}
                  onClick={() => onSelectRun(run.entityId)}
                >
                  <td className="px-4 py-3">
                    <Link
                      className="font-mono text-xs underline decoration-border underline-offset-4 hover:text-primary"
                      onClick={(event) => {
                        event.stopPropagation();
                      }}
                      to={buildRunRoutePath(run.runId, scope, { laneId, methodId })}
                    >
                      {run.runId}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-foreground">{run.seed}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge {...getStatusBadgeProps(run.status)}>{formatLabel(run.status)}</Badge>
                      {run.scope === "exploratory" ? <Badge tone="exploratory">Exploratory</Badge> : null}
                      {isSelected ? <Badge tone="muted">Selected</Badge> : null}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-foreground">
                    {primaryMetric ? formatMetric(primaryMetric.value) : "n/a"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
