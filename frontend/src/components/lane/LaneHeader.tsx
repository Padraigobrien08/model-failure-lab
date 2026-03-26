import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";
import type { LaneRouteStatus } from "@/lib/laneRoute";

type LaneHeaderProps = {
  laneLabel: string;
  status: LaneRouteStatus;
  summary: string;
  scope: TraceScope;
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

export function LaneHeader({ laneLabel, status, summary, scope }: LaneHeaderProps) {
  return (
    <header className="space-y-3 border-b border-border/70 pb-4">
      <nav aria-label="Lane breadcrumb" className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link className="underline underline-offset-4" to={`/?scope=${scope}`}>
          Summary
        </Link>
        <span aria-hidden="true">/</span>
        <span>{laneLabel}</span>
      </nav>

      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          What is happening in this lane?
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">{laneLabel}</h1>
          <Badge {...getStatusBadgeProps(status)}>{formatLabel(status)}</Badge>
        </div>
        <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{summary}</p>
      </div>
    </header>
  );
}
