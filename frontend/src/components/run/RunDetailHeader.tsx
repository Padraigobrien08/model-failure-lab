import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";

type RunDetailHeaderProps = {
  runId: string;
  dataset: string;
  model: string;
  status: string;
  createdAt: string;
  inventoryHref: string;
  reportId: string;
  adapterId: string | null;
  classifierId: string | null;
  runSeed: number | null;
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
  runId: _runId,
  dataset,
  model,
  status,
  createdAt,
  inventoryHref,
  reportId: _reportId,
  adapterId: _adapterId,
  classifierId: _classifierId,
  runSeed: _runSeed,
}: RunDetailHeaderProps) {
  const datasetLabel = formatLabel(dataset);
  const modelLabel = formatLabel(model);
  const statusLabel = formatLabel(status);
  const savedAtLabel = formatTimestamp(createdAt);

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
        <span className="text-sm text-foreground">{datasetLabel}</span>
      </nav>

      <div className="min-w-0 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Run detail</Badge>
        </div>
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Stage 1 · Run identity
          </p>
          <h1 className="text-3xl font-semibold leading-tight tracking-[-0.04em] text-foreground sm:text-4xl">
            {datasetLabel}
          </h1>
          <p className="max-w-4xl text-base leading-7 text-muted-foreground">
            Lock the route identity first, then move into failure shape, diagnosis, notable cases,
            and selected evidence without re-reading a dense provenance block.
          </p>
        </div>
        <div className="rounded-[22px] border border-border/60 bg-card/55 px-4 py-4">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Status
              </p>
              <Badge tone={statusTone(status)}>{statusLabel}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Model
              </p>
              <p className="text-sm font-semibold text-foreground">{modelLabel}</p>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Saved at
              </p>
              <p className="text-sm font-semibold text-foreground">{savedAtLabel}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
