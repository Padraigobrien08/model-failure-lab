import { ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { RunInventoryItem } from "@/lib/artifacts/types";

type RunInventoryTableProps = {
  rows: RunInventoryItem[];
  onOpenRun: (runId: string) => void;
};

function formatTimestamp(value: string): string {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return value;
  }
  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    timeZone: "UTC",
    year: "numeric",
  }).format(new Date(parsed));
}

function statusTone(status: string): "accent" | "muted" | "default" {
  if (status === "completed") {
    return "accent";
  }
  if (status.includes("error")) {
    return "default";
  }
  return "muted";
}

export function RunInventoryTable({ rows, onOpenRun }: RunInventoryTableProps) {
  return (
    <div className="overflow-hidden rounded-[28px] border border-border/70 bg-card/80 shadow-[0_18px_45px_-28px_rgba(15,23,42,0.28)]">
      <table aria-label="Runs inventory" className="min-w-full border-collapse">
        <thead>
          <tr className="border-b border-border/60 text-left">
            <th className="px-5 py-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Run id
            </th>
            <th className="px-5 py-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Dataset
            </th>
            <th className="px-5 py-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Model
            </th>
            <th className="px-5 py-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Saved at
            </th>
            <th className="px-5 py-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Status
            </th>
            <th className="px-5 py-4 text-right text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Open
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.runId} className="border-b border-border/50 last:border-b-0">
              <td colSpan={6} className="p-0">
                <div
                  aria-label={`Open run ${row.runId}`}
                  className="grid cursor-pointer gap-3 px-5 py-4 transition-colors hover:bg-background/60 focus:outline-none focus:ring-2 focus:ring-primary/35 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_minmax(0,0.8fr)_minmax(0,0.8fr)_minmax(0,0.8fr)_auto] md:items-center"
                  onClick={() => onOpenRun(row.runId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onOpenRun(row.runId);
                    }
                  }}
                  role="link"
                  tabIndex={0}
                >
                  <div className="min-w-0 text-sm font-semibold text-foreground">
                    <div className="truncate">{row.runId}</div>
                  </div>
                  <div className="text-sm text-muted-foreground">{row.dataset}</div>
                  <div className="text-sm text-muted-foreground">{row.model}</div>
                  <div className="text-sm text-muted-foreground">
                    {formatTimestamp(row.createdAt)}
                  </div>
                  <div>
                    <Badge tone={statusTone(row.status)}>
                      {row.status.split("_").join(" ")}
                    </Badge>
                  </div>
                  <div className="flex justify-end">
                    <button
                      aria-label={`Open ${row.runId}`}
                      className="inline-flex h-10 items-center gap-2 rounded-full border border-border/70 bg-background/80 px-4 text-sm font-semibold text-foreground transition-colors hover:bg-background"
                      onClick={(event) => {
                        event.stopPropagation();
                        onOpenRun(row.runId);
                      }}
                      type="button"
                    >
                      Open
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
