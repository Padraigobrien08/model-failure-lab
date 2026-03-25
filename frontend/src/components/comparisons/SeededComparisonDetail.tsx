import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatMetric, formatSignedMetric } from "@/lib/formatters";
import type { SeedBreakdownRow } from "@/lib/manifest/types";

type SeededComparisonDetailProps = {
  rows: SeedBreakdownRow[];
};

function renderDelta(row: SeedBreakdownRow, key: string) {
  return key in row.deltas ? formatSignedMetric(row.deltas[key]) : formatMetric(row.metrics[key]);
}

export function SeededComparisonDetail({ rows }: SeededComparisonDetailProps) {
  if (rows.length === 0) {
    return (
      <Card className="bg-background/55">
        <CardContent className="px-4 py-4 text-sm leading-6 text-muted-foreground">
          Scout-only evidence is summarized in the saved report package. There is no seeded cohort
          expansion for this lane.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div
          key={row.seed}
          className="rounded-[22px] border border-border/70 bg-background/55 px-4 py-4"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="muted">Seed {row.seed}</Badge>
            {row.verdict ? <Badge tone="default">{row.verdict}</Badge> : null}
            {row.runId ? (
              <span className="font-mono text-xs text-muted-foreground">{row.runId}</span>
            ) : null}
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Worst Group
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {renderDelta(row, "worst_group_f1")}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                OOD
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {renderDelta(row, "ood_macro_f1")}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                ID
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {renderDelta(row, "id_macro_f1")}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                ECE
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {renderDelta(row, "ece")}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Brier
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {renderDelta(row, "brier_score")}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
