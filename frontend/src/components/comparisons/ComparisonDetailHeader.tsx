import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { ComparisonDetail } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonDetailHeaderProps = {
  comparison: ComparisonDetail["comparison"];
  signal: ComparisonDetail["signal"];
  governanceRecommendation: ComparisonDetail["governanceRecommendation"];
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

function signalTone(verdict: string): "accent" | "default" | "muted" {
  if (verdict === "improvement") {
    return "accent";
  }
  if (verdict === "regression") {
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
  signal,
  governanceRecommendation,
  inventoryHref,
  baselineRunState: _baselineRunState,
  candidateRunState: _candidateRunState,
}: ComparisonDetailHeaderProps) {
  const datasetLabel = formatLabel(datasetBadgeText(comparison));
  const savedAtLabel = formatTimestamp(comparison.createdAt);
  const statusLabel = formatLabel(comparison.status);

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
          <Badge tone={signalTone(signal.verdict)}>{formatLabel(signal.verdict)}</Badge>
          <Badge tone="muted">{(signal.severity * 100).toFixed(1)}% severity</Badge>
          {governanceRecommendation ? (
            <Badge tone={governanceRecommendation.action === "ignore" ? "default" : "accent"}>
              {formatLabel(governanceRecommendation.action)}
            </Badge>
          ) : null}
          {governanceRecommendation?.escalation ? (
            <Badge
              tone={
                governanceRecommendation.escalation.status === "critical"
                  ? "default"
                  : "accent"
              }
            >
              {formatLabel(governanceRecommendation.escalation.status)}
            </Badge>
          ) : null}
          {governanceRecommendation?.lifecycleRecommendation ? (
            <Badge tone="muted">
              {formatLabel(governanceRecommendation.lifecycleRecommendation.action)}
            </Badge>
          ) : null}
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Orient first
          </p>
          <h1 className="text-3xl font-semibold leading-tight tracking-[-0.04em] text-foreground sm:text-4xl">
            {datasetLabel}
          </h1>
          <p className="max-w-4xl text-base leading-7 text-muted-foreground">
            Frame the comparison first, then move into shared-case scope and grouped transition
            evidence without repeating the full provenance block in the header.
          </p>
          {governanceRecommendation ? (
            <p className="max-w-4xl text-sm leading-6 text-muted-foreground">
              Recommendation: {governanceRecommendation.rationale}
            </p>
          ) : null}
          {governanceRecommendation?.lifecycleRecommendation ? (
            <p className="max-w-4xl text-sm leading-6 text-muted-foreground">
              Lifecycle: {governanceRecommendation.lifecycleRecommendation.rationale}
            </p>
          ) : null}
        </div>

        <div className="rounded-[22px] border border-border/60 bg-card/55 px-4 py-4">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Baseline
              </p>
              <p className="break-all text-sm font-semibold text-foreground">
                {comparison.baselineRunId}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Candidate
              </p>
              <p className="break-all text-sm font-semibold text-foreground">
                {comparison.candidateRunId}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Status
              </p>
              <Badge tone={statusTone(comparison.compatible, comparison.status)}>
                {statusLabel}
              </Badge>
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
