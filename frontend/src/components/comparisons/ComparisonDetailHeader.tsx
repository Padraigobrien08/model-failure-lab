import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { ComparisonDetail } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonDetailHeaderProps = {
  comparison: ComparisonDetail["comparison"];
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
}: ComparisonDetailHeaderProps) {
  return (
    <header className="space-y-5 border-b border-border/60 pb-6">
      <nav
        aria-label="Comparison breadcrumb"
        className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
      >
        <Link className="font-semibold text-foreground no-underline" to={inventoryHref}>
          Comparisons
        </Link>
        <span aria-hidden="true">/</span>
        <span className="font-mono text-xs text-foreground">{comparison.reportId}</span>
      </nav>

      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Comparison detail</Badge>
          <Link
            className="rounded-full text-inherit no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            to={`/runs/${encodeURIComponent(comparison.baselineRunId)}`}
          >
            <Badge tone="muted">{comparison.baselineRunId}</Badge>
          </Link>
          <Link
            className="rounded-full text-inherit no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            to={`/runs/${encodeURIComponent(comparison.candidateRunId)}`}
          >
            <Badge tone="muted">{comparison.candidateRunId}</Badge>
          </Link>
          <Badge tone="muted">{datasetBadgeText(comparison)}</Badge>
          <Badge tone={statusTone(comparison.compatible, comparison.status)}>
            {formatLabel(comparison.status)}
          </Badge>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Orient first
          </p>
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground sm:text-4xl">
            {comparison.reportId}
          </h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Frame the comparison before reading the transitions: baseline versus candidate, saved
            dataset scope, compatibility, and the delta that explains what changed overall.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] md:items-center">
          <div className="rounded-[20px] border border-border/60 bg-background/70 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Baseline
            </p>
            <p className="mt-2 text-sm font-semibold text-foreground">{comparison.baselineRunId}</p>
          </div>
          <div className="flex items-center justify-center">
            <span className="rounded-full border border-border/60 bg-card/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              vs
            </span>
          </div>
          <div className="rounded-[20px] border border-border/60 bg-background/70 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Candidate
            </p>
            <p className="mt-2 text-sm font-semibold text-foreground">
              {comparison.candidateRunId}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            "Directional delta",
            "Coverage scope",
            "Grouped transitions",
            "Selected evidence",
          ].map((step, index) => (
            <span
              key={step}
              className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground"
            >
              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/12 text-[10px] text-primary">
                {index + 1}
              </span>
              {step}
            </span>
          ))}
        </div>

        <p className="text-sm text-muted-foreground">
          Saved at{" "}
          <span className="font-medium text-foreground">
            {formatTimestamp(comparison.createdAt)}
          </span>
        </p>
      </div>
    </header>
  );
}
