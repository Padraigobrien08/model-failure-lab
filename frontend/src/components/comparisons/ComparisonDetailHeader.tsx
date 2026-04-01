import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { ComparisonDetail } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonDetailHeaderProps = {
  comparison: ComparisonDetail["comparison"];
  inventoryHref: string;
  baselineRunState?: unknown;
  candidateRunState?: unknown;
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

function statusTone(
  compatible: boolean,
  status: string,
): "accent" | "default" | "muted" {
  if (!compatible) {
    return "default";
  }
  if (status.startsWith("improved")) {
    return "accent";
  }
  if (status.startsWith("regressed")) {
    return "default";
  }
  return "muted";
}

function datasetBadgeText(comparison: ComparisonDetail["comparison"]): string {
  if (comparison.dataset) {
    return comparison.dataset;
  }
  if (comparison.baselineDataset && comparison.candidateDataset) {
    return `${comparison.baselineDataset} vs ${comparison.candidateDataset}`;
  }
  return "Multiple datasets";
}

export function ComparisonDetailHeader({
  comparison,
  inventoryHref,
  baselineRunState,
  candidateRunState,
}: ComparisonDetailHeaderProps) {
  const datasetLabel = formatLabel(datasetBadgeText(comparison));

  return (
    <header className="space-y-4 border-b border-border/60 pb-5">
      <nav
        aria-label="Comparison breadcrumb"
        className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
      >
        <Link className="font-semibold text-foreground no-underline" to={inventoryHref}>
          Comparisons
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-sm text-foreground">{datasetLabel}</span>
      </nav>

      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Comparison detail</Badge>
          <Link
            className="rounded-full text-inherit no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            to={`/runs/${encodeURIComponent(comparison.baselineRunId)}`}
            state={baselineRunState}
          >
            <Badge tone="muted">Baseline</Badge>
          </Link>
          <Link
            className="rounded-full text-inherit no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            to={`/runs/${encodeURIComponent(comparison.candidateRunId)}`}
            state={candidateRunState}
          >
            <Badge tone="muted">Candidate</Badge>
          </Link>
          <Badge tone="muted">{datasetLabel}</Badge>
          <Badge tone={statusTone(comparison.compatible, comparison.status)}>
            {formatLabel(comparison.status)}
          </Badge>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Orient first
          </p>
          <h1 className="text-3xl font-semibold leading-tight tracking-[-0.04em] text-foreground sm:text-4xl">
            {datasetLabel}
          </h1>
          <p className="max-w-4xl text-base leading-7 text-muted-foreground">
            Frame the comparison first: baseline versus candidate, shared-case scope, and the delta
            that explains what changed overall.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Baseline run
            </p>
            <p className="mt-2 break-all font-mono text-xs text-foreground">
              {comparison.baselineRunId}
            </p>
          </div>
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Candidate run
            </p>
            <p className="mt-2 break-all font-mono text-xs text-foreground">
              {comparison.candidateRunId}
            </p>
          </div>
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Report ID
            </p>
            <p className="mt-2 break-all font-mono text-xs text-foreground">
              {comparison.reportId}
            </p>
          </div>
          <div className="rounded-[18px] border border-border/60 bg-card/55 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Saved at
            </p>
            <p className="mt-2 text-sm text-foreground">{formatTimestamp(comparison.createdAt)}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
