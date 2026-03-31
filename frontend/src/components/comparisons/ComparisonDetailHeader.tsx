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
    <header className="space-y-4 border-b border-border/60 pb-5">
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

      <div className="space-y-3">
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

        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
            {comparison.reportId}
          </h1>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Start with the directional delta between baseline and candidate, then inspect grouped
            transition cases that explain the change.
          </p>
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
