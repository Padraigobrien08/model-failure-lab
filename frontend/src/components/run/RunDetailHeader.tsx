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

function formatOptionalValue(value: string | number | null): string {
  if (value === null || value === "") {
    return "n/a";
  }

  return String(value);
}

export function RunDetailHeader({
  runId,
  dataset,
  model,
  status,
  createdAt,
  inventoryHref,
  reportId,
  adapterId,
  classifierId,
  runSeed,
}: RunDetailHeaderProps) {
  const datasetLabel = formatLabel(dataset);
  const modelLabel = formatLabel(model);
  const statusLabel = formatLabel(status);

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
          <Badge tone={statusTone(status)}>{statusLabel}</Badge>
          <Badge tone="muted">{modelLabel}</Badge>
        </div>
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Stage 1 · Run identity
          </p>
          <h1 className="text-3xl font-semibold leading-tight tracking-[-0.04em] text-foreground sm:text-4xl">
            {datasetLabel}
          </h1>
          <p className="max-w-4xl text-base leading-7 text-muted-foreground">
            {modelLabel} run, saved {formatTimestamp(createdAt)}. Lock the run identity first, then
            move into failure shape, diagnosis, notable cases, and selected evidence.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Run ID
            </p>
            <p className="mt-2 break-all font-mono text-xs text-foreground">{runId}</p>
          </div>
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Report ID
            </p>
            <p className="mt-2 break-all font-mono text-xs text-foreground">{reportId}</p>
          </div>
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Adapter
            </p>
            <p className="mt-2 text-sm text-foreground">{formatOptionalValue(adapterId)}</p>
          </div>
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Classifier / Seed
            </p>
            <p className="mt-2 text-sm text-foreground">
              {formatOptionalValue(classifierId)} / {formatOptionalValue(runSeed)}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
