import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel, formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { LaneRouteLaneId, LaneRouteMethodRow, LaneRouteTableColumn } from "@/lib/laneRoute";
import { cn } from "@/lib/utils";

type MethodComparisonTableProps = {
  laneId: LaneRouteLaneId;
  columns: LaneRouteTableColumn[];
  rows: LaneRouteMethodRow[];
  scope: TraceScope;
};

function withScope(path: string, scope: TraceScope) {
  return `${path}?scope=${scope}`;
}

function getStatusBadgeProps(status: LaneRouteMethodRow["status"]) {
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

function renderMetricCell(row: LaneRouteMethodRow, key: LaneRouteTableColumn["key"]) {
  if (key === "status") {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <Badge {...getStatusBadgeProps(row.status)}>{formatLabel(row.status)}</Badge>
        {row.scope === "exploratory" ? <Badge tone="exploratory">Exploratory</Badge> : null}
      </div>
    );
  }

  if (key === "worst_group") {
    return <span className="font-mono text-sm">{formatMetric(row.metrics.worstGroup)}</span>;
  }

  if (key === "ood") {
    return <span className="font-mono text-sm">{formatMetric(row.metrics.ood)}</span>;
  }

  if (key === "id") {
    return <span className="font-mono text-sm">{formatMetric(row.metrics.id)}</span>;
  }

  if (key === "ece") {
    return <span className="font-mono text-sm">{formatMetric(row.metrics.ece)}</span>;
  }

  if (key === "brier") {
    return <span className="font-mono text-sm">{formatMetric(row.metrics.brier)}</span>;
  }

  return (
    <span
      className={cn(
        "font-mono text-sm",
        getMetricTextTone(row.deltaVsBaseline, Boolean(row.lowerIsBetter)),
      )}
    >
      {formatSignedMetric(row.deltaVsBaseline)}
    </span>
  );
}

export function MethodComparisonTable({
  laneId,
  columns,
  rows,
  scope,
}: MethodComparisonTableProps) {
  return (
    <div className="overflow-x-auto rounded-[16px] border border-border/70">
      <table className="min-w-full border-collapse text-sm">
        <thead className="bg-muted/40">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  "border-b border-border/70 px-4 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground",
                  column.align === "right" ? "text-right" : "text-left",
                )}
                scope="col"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.entityId} className="border-b border-border/60 last:border-b-0">
              {columns.map((column, index) => (
                <td
                  key={`${row.entityId}-${column.key}`}
                  className={cn(
                    "px-4 py-3 align-top text-foreground",
                    column.align === "right" ? "text-right" : "text-left",
                  )}
                >
                  {index === 0 ? (
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          className="font-semibold underline decoration-border underline-offset-4 hover:text-primary"
                          to={withScope(`/lane/${laneId}/${row.methodId}`, scope)}
                        >
                          {row.label}
                        </Link>
                        {row.methodId === "baseline" ? <Badge tone="muted">Baseline</Badge> : null}
                      </div>
                      <p className="max-w-sm text-xs leading-5 text-muted-foreground">{row.summary}</p>
                    </div>
                  ) : (
                    renderMetricCell(row, column.key)
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
