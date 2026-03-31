import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";

type RunDetailHeaderProps = {
  runId: string;
  dataset: string;
  model: string;
  status: string;
  createdAt: string;
  inventoryHref: string;
};

function formatTimestamp(createdAt: string): string {
  const value = new Date(createdAt);
  if (Number.isNaN(value.getTime())) {
    return createdAt;
  }

  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(value);
}

function statusTone(status: string): "accent" | "default" | "muted" {
  if (status === "completed") {
    return "accent";
  }
  if (status === "completed_with_errors") {
    return "default";
  }
  return "muted";
}

export function RunDetailHeader({
  runId,
  dataset,
  model,
  status,
  createdAt,
  inventoryHref,
}: RunDetailHeaderProps) {
  return (
    <header className="space-y-4 border-b border-border/60 pb-5">
      <nav
        aria-label="Run breadcrumb"
        className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
      >
        <Link className="font-semibold text-foreground no-underline" to={inventoryHref}>
          Runs
        </Link>
        <span aria-hidden="true">/</span>
        <span className="font-mono text-xs text-foreground">{runId}</span>
      </nav>

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Run detail</Badge>
          <Badge tone="muted">{dataset}</Badge>
          <Badge tone="muted">{model}</Badge>
          <Badge tone={statusTone(status)}>{status}</Badge>
        </div>
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">{runId}</h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Read the run-level shape first, then drop into the cases carrying the strongest mismatch
            or failure signal.
          </p>
        </div>
        <p className="text-sm text-muted-foreground">
          Saved at <span className="font-medium text-foreground">{formatTimestamp(createdAt)}</span>
        </p>
      </div>
    </header>
  );
}
