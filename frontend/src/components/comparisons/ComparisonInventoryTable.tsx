import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ComparisonInventoryItem } from "@/lib/artifacts/types";

type ComparisonInventoryTableProps = {
  rows: ComparisonInventoryItem[];
  onOpenComparison: (reportId: string) => void;
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

function datasetLabel(dataset: string | null): string {
  return dataset ?? "Multiple datasets";
}

export function ComparisonInventoryTable({
  rows,
  onOpenComparison,
}: ComparisonInventoryTableProps) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-border/70 bg-card/75 shadow-panel">
      <div className="overflow-x-auto">
        <table
          aria-label="Comparisons inventory"
          className="min-w-full border-collapse text-sm"
        >
          <thead className="bg-background/55">
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
                Status
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Open
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.reportId}
                tabIndex={0}
                role="link"
                aria-label={`Open comparison ${row.reportId}`}
                className="cursor-pointer border-b border-border/55 transition-colors last:border-b-0 hover:bg-background/50 focus-visible:bg-background/50 focus-visible:outline-none"
                onClick={() => onOpenComparison(row.reportId)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onOpenComparison(row.reportId);
                  }
                }}
              >
                <td className="px-4 py-3 font-mono text-xs text-foreground">{row.reportId}</td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">
                  {row.baselineRunId}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-foreground">
                  {row.candidateRunId}
                </td>
                <td className="px-4 py-3 text-foreground">{datasetLabel(row.dataset)}</td>
                <td className="px-4 py-3 text-muted-foreground">
                  <time dateTime={row.createdAt}>{formatTimestamp(row.createdAt)}</time>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={statusTone(row.compatible, row.status)}>{row.status}</Badge>
                </td>
                <td className="px-4 py-3">
                  <Button
                    variant="ghost"
                    size="sm"
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
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
