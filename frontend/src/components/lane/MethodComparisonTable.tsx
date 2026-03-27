import { Fragment } from "react";
import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatLabel, formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import { MethodRunsSubtable } from "@/components/lane/MethodRunsSubtable";
import type {
  LaneRouteLaneId,
  LaneRouteMethodId,
  LaneRouteMethodRow,
  LaneRouteSelection,
  LaneRouteTableColumn,
} from "@/lib/laneRoute";
import { cn } from "@/lib/utils";

type MethodComparisonTableProps = {
  laneId: LaneRouteLaneId;
  columns: LaneRouteTableColumn[];
  officialRows: LaneRouteMethodRow[];
  exploratoryRows: LaneRouteMethodRow[];
  scope: TraceScope;
  selected: LaneRouteSelection;
  expandedMethodIds: LaneRouteMethodId[];
  onSelectMethod: (entityId: string) => void;
  onSelectRun: (entityId: string) => void;
  onToggleRuns: (methodId: LaneRouteMethodId) => void;
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
  officialRows,
  exploratoryRows,
  scope,
  selected,
  expandedMethodIds,
  onSelectMethod,
  onSelectRun,
  onToggleRuns,
}: MethodComparisonTableProps) {
  function renderRows(rows: LaneRouteMethodRow[]) {
    return rows.map((row) => {
      const isExpanded = expandedMethodIds.includes(row.methodId);
      const isSelected =
        selected.entityType === "method" && selected.entityId === row.entityId;

      return (
        <Fragment key={row.entityId}>
          <tr
            aria-selected={isSelected}
            className={cn(
              "border-b border-border/60 last:border-b-0 cursor-pointer transition-colors",
              isSelected ? "bg-muted/35" : "hover:bg-muted/15",
            )}
            data-testid={`method-row-${row.methodId}`}
            onClick={() => onSelectMethod(row.entityId)}
          >
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
                      <Button
                        aria-label={`${isExpanded ? "Hide" : "Show"} runs for ${row.label}`}
                        aria-expanded={isExpanded}
                        className="h-7 rounded-md px-2 text-[10px]"
                        onClick={(event) => {
                          event.stopPropagation();
                          onToggleRuns(row.methodId);
                        }}
                        size="sm"
                        variant="outline"
                      >
                        {isExpanded ? "Hide runs" : "Show runs"}
                      </Button>
                      <Link
                        className="font-semibold underline decoration-border underline-offset-4 hover:text-primary"
                        onClick={(event) => {
                          event.stopPropagation();
                        }}
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
          {isExpanded ? (
            <tr className="border-b border-border/60">
              <td className="bg-muted/10 px-0 py-0" colSpan={columns.length}>
                <MethodRunsSubtable
                  laneId={laneId}
                  methodId={row.methodId}
                  methodLabel={row.label}
                  runs={row.runs}
                  scope={scope}
                  selectedEntityId={selected.entityId}
                  onSelectRun={onSelectRun}
                />
              </td>
            </tr>
          ) : null}
        </Fragment>
      );
    });
  }

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
          {renderRows(officialRows)}
          {exploratoryRows.length > 0 ? (
            <tr>
              <td className="bg-muted/20 px-4 py-3" colSpan={columns.length}>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="exploratory">Exploratory methods</Badge>
                  <p className="text-xs text-muted-foreground">
                    Shown because scope includes exploratory evidence.
                  </p>
                </div>
              </td>
            </tr>
          ) : null}
          {renderRows(exploratoryRows)}
        </tbody>
      </table>
    </div>
  );
}
