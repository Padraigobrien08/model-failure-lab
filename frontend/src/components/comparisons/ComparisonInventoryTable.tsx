import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ComparisonInventoryItem } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonInventoryTableProps = {
  rows: ComparisonInventoryItem[];
  onOpenComparison: (reportId: string) => void;
};

function MobileLabel({ children }: { children: string }) {
  return (
    <span className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground md:hidden">
      {children}
    </span>
  );
}

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

function datasetLabel(dataset: string | null): string {
  return dataset ?? "Multiple datasets";
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

function recommendationTone(action: string): "accent" | "default" | "muted" {
  return action === "ignore" ? "default" : "accent";
}

function escalationTone(status: string): "accent" | "default" | "muted" {
  if (status === "critical") {
    return "default";
  }
  if (status === "elevated") {
    return "accent";
  }
  return "muted";
}

function priorityTone(priorityBand: string): "accent" | "default" | "muted" {
  if (priorityBand === "urgent") {
    return "default";
  }
  if (priorityBand === "high") {
    return "accent";
  }
  return "muted";
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function ComparisonInventoryTable({
  rows,
  onOpenComparison,
}: ComparisonInventoryTableProps) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-border/70 bg-card/75 shadow-panel">
      <div className="md:overflow-x-auto">
        <table
          aria-label="Comparisons inventory"
          className="block min-w-full border-collapse text-sm md:table"
        >
          <thead className="hidden bg-background/55 md:table-header-group">
            <tr className="border-b border-border/70 text-left">
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Report id
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Baseline
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Candidate
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Dataset
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Saved at
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Operator triage
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Open
              </th>
            </tr>
          </thead>
          <tbody className="block md:table-row-group">
            {rows.map((row) => {
              const recommendation = row.governanceRecommendation ?? null;
              const lifecycleRecommendation = recommendation?.lifecycleRecommendation ?? null;
              const escalation = recommendation?.escalation ?? null;
              const portfolioItem = row.portfolioItem ?? null;
              const matchedFamilyId = recommendation?.matchedFamily.familyId ?? null;
              const actionability = portfolioItem?.actionability ?? null;

              return (
                <tr
                key={row.reportId}
                tabIndex={0}
                role="link"
                aria-label={`Open comparison ${row.reportId}`}
                className="mb-3 block cursor-pointer rounded-[20px] border border-border/55 bg-background/25 p-4 transition-colors last:mb-0 hover:bg-background/50 focus-visible:bg-background/50 focus-visible:outline-none md:mb-0 md:table-row md:rounded-none md:border-x-0 md:border-b md:border-t-0 md:bg-transparent md:p-0"
                onClick={() => onOpenComparison(row.reportId)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onOpenComparison(row.reportId);
                  }
                }}
              >
                <td className="block px-0 py-2 font-mono text-xs text-foreground md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Report id</MobileLabel>
                  {row.reportId}
                </td>
                <td className="block px-0 py-2 font-mono text-xs text-foreground md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Baseline</MobileLabel>
                  {row.baselineRunId}
                </td>
                <td className="block px-0 py-2 font-mono text-xs text-foreground md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Candidate</MobileLabel>
                  {row.candidateRunId}
                </td>
                <td className="block px-0 py-2 text-foreground md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Dataset</MobileLabel>
                  {datasetLabel(row.dataset)}
                </td>
                <td className="block px-0 py-2 text-muted-foreground md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Saved at</MobileLabel>
                  <time dateTime={row.createdAt}>{formatTimestamp(row.createdAt)}</time>
                </td>
                <td className="block px-0 py-2 md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Triage</MobileLabel>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={signalTone(row.signalVerdict)}>{row.signalVerdict}</Badge>
                    <Badge tone="muted">{formatPercent(row.severity)} severity</Badge>
                    <Badge tone={statusTone(row.compatible, row.status)}>{row.status}</Badge>
                    {recommendation ? (
                      <Badge tone={recommendationTone(recommendation.action)}>
                        {formatLabel(recommendation.action)}
                      </Badge>
                    ) : null}
                    {escalation ? (
                      <Badge tone={escalationTone(escalation.status)}>
                        {formatLabel(escalation.status)}
                      </Badge>
                    ) : null}
                    {lifecycleRecommendation ? (
                      <Badge tone="muted">
                        {formatLabel(lifecycleRecommendation.action)}
                      </Badge>
                    ) : null}
                    {portfolioItem ? (
                      <Badge tone={priorityTone(portfolioItem.priorityBand)}>
                        Rank {portfolioItem.priorityRank} {formatLabel(portfolioItem.priorityBand)}
                      </Badge>
                    ) : null}
                  </div>
                  <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                    {matchedFamilyId ? (
                      <p className="break-all">
                        Family: {matchedFamilyId}
                        {actionability ? ` · ${formatLabel(actionability)}` : ""}
                      </p>
                    ) : null}
                    {portfolioItem ? (
                      <p>
                        Priority {portfolioItem.priorityScore.toFixed(3)} ·{" "}
                        {portfolioItem.recentRegressionCount} recent regressions ·{" "}
                        {portfolioItem.recurringClusterCount} recurring clusters
                      </p>
                    ) : null}
                    {row.topDrivers[0] ? (
                      <p>
                        Driver: {row.topDrivers[0].failureType}{" "}
                        {row.topDrivers[0].delta > 0 ? "+" : ""}
                        {(row.topDrivers[0].delta * 100).toFixed(1)}%
                      </p>
                    ) : null}
                  </div>
                </td>
                <td className="block px-0 pt-3 md:table-cell md:px-4 md:py-3">
                  <MobileLabel>Open</MobileLabel>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full md:w-auto"
                    aria-label={`Open ${row.reportId}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenComparison(row.reportId);
                    }}
                  >
                    Open
                  </Button>
                </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
