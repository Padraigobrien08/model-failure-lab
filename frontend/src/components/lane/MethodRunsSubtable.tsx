import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel, formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { LaneRouteLaneId, LaneRouteRunRow } from "@/lib/laneRoute";
import { cn } from "@/lib/utils";

type MethodRunsSubtableProps = {
  laneId: LaneRouteLaneId;
  methodLabel: string;
  runs: LaneRouteRunRow[];
  scope: TraceScope;
  selectedEntityId: string;
  onSelectRun: (entityId: string) => void;
};

function withScope(path: string, scope: TraceScope) {
  return `${path}?scope=${scope}`;
}

function getStatusBadgeProps(status: LaneRouteRunRow["status"]) {
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

export function MethodRunsSubtable({
  laneId,
  methodLabel,
  runs,
  scope,
  selectedEntityId,
  onSelectRun,
}: MethodRunsSubtableProps) {
  return (
    <div className="px-4 py-3">
      <table aria-label={`${methodLabel} runs`} className="min-w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className="px-3 py-2 text-left font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Run ID
            </th>
            <th className="px-3 py-2 text-left font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Seed
            </th>
            <th className="px-3 py-2 text-left font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Status
            </th>
            <th className="px-3 py-2 text-right font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              {laneId === "robustness" ? "Worst-group" : "ECE"}
            </th>
            <th className="px-3 py-2 text-right font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Delta
            </th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const isSelected = selectedEntityId === run.entityId;

            return (
              <tr
                key={run.entityId}
                aria-selected={isSelected}
                className={cn(
                  "border-t border-border/50 cursor-pointer transition-colors",
                  isSelected ? "bg-background/90" : "hover:bg-background/60",
                )}
                data-testid={`run-row-${run.runId}`}
                onClick={() => onSelectRun(run.entityId)}
              >
                <td className="px-3 py-2 text-left">
                  <Link
                    className="font-mono text-[11px] underline decoration-border underline-offset-4 hover:text-primary"
                    onClick={(event) => {
                      event.stopPropagation();
                    }}
                    to={withScope(`/run/${run.runId}`, scope)}
                  >
                    {run.runId}
                  </Link>
                </td>
                <td className="px-3 py-2 text-left font-mono text-[11px] text-foreground">{run.seed}</td>
                <td className="px-3 py-2 text-left">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge {...getStatusBadgeProps(run.status)}>{formatLabel(run.status)}</Badge>
                    {run.scope === "exploratory" ? <Badge tone="exploratory">Exploratory</Badge> : null}
                  </div>
                </td>
                <td className="px-3 py-2 text-right font-mono text-[11px] text-foreground">
                  {formatMetric(run.keyMetricValue)}
                </td>
                <td
                  className={cn(
                    "px-3 py-2 text-right font-mono text-[11px]",
                    getMetricTextTone(run.deltaVsBaseline, laneId === "calibration"),
                  )}
                >
                  {formatSignedMetric(run.deltaVsBaseline)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
