import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";
import type { LaneRouteStatus } from "@/lib/laneRoute";

type RunHeaderProps = {
  laneLabel: string;
  methodLabel: string;
  runId: string;
  seed: number;
  status: LaneRouteStatus;
  breadcrumbs: {
    summaryPath: string;
    lanePath: string;
    methodPath: string;
  };
};

function getStatusBadgeProps(status: LaneRouteStatus) {
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

export function RunHeader({
  laneLabel,
  methodLabel,
  runId,
  seed,
  status,
  breadcrumbs,
}: RunHeaderProps) {
  return (
    <header className="space-y-3 border-b border-border/70 pb-4">
      <nav aria-label="Run breadcrumb" className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link className="underline underline-offset-4" to={breadcrumbs.summaryPath}>
          Summary
        </Link>
        <span aria-hidden="true">/</span>
        <Link className="underline underline-offset-4" to={breadcrumbs.lanePath}>
          {laneLabel}
        </Link>
        <span aria-hidden="true">/</span>
        <Link className="underline underline-offset-4" to={breadcrumbs.methodPath}>
          {methodLabel}
        </Link>
        <span aria-hidden="true">/</span>
        <span>{runId}</span>
      </nav>

      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          What happened in this run?
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">{runId}</h1>
          <Badge tone="muted">{laneLabel}</Badge>
          <Badge tone="muted">{methodLabel}</Badge>
          <Badge tone="muted">Seed {seed}</Badge>
          <Badge {...getStatusBadgeProps(status)}>{formatLabel(status)}</Badge>
        </div>
      </div>
    </header>
  );
}
