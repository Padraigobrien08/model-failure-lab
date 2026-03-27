import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel, formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { LaneRouteLaneId, LaneRouteRunRow } from "@/lib/laneRoute";
import type { LaneRouteMethodId } from "@/lib/laneRoute";
import { buildRunRoutePath } from "@/lib/runRoute";
import { cn } from "@/lib/utils";

type MethodRunsSubtableProps = {
  laneId: LaneRouteLaneId;
  methodId: LaneRouteMethodId;
  methodLabel: string;
  runs: LaneRouteRunRow[];
  scope: TraceScope;
  selectedEntityId: string;
  onSelectRun: (entityId: string) => void;
};

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
  methodId,
  methodLabel,
  runs,
  scope,
  selectedEntityId,
  onSelectRun,
}: MethodRunsSubtableProps) {
  const officialRuns = runs.filter((run) => run.scope === "official");
  const exploratoryRuns = runs.filter((run) => run.scope === "exploratory");

  function renderRows(sectionRuns: LaneRouteRunRow[]) {
    return sectionRuns.map((run) => {
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
              to={buildRunRoutePath(run.runId, scope, { laneId, methodId })}
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
    });
  }

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
          {renderRows(officialRuns)}
          {exploratoryRuns.length > 0 ? (
            <tr className="border-t border-border/50">
              <td className="bg-muted/20 px-3 py-2" colSpan={5}>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="exploratory">Exploratory runs</Badge>
                  <p className="text-[11px] text-muted-foreground">
                    Shown because scope includes exploratory evidence.
                  </p>
                </div>
              </td>
            </tr>
          ) : null}
          {renderRows(exploratoryRuns)}
        </tbody>
      </table>
    </div>
  );
}
