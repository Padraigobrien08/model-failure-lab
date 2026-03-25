import { Badge } from "@/components/ui/badge";
import { formatMetric, formatSignedMetric } from "@/lib/formatters";
import type { FailureDomainKey, SeedBreakdownRow } from "@/lib/manifest/types";

type FailureSeededDetailProps = {
  rows: SeedBreakdownRow[];
  domain: FailureDomainKey;
};

function renderDomainValue(row: SeedBreakdownRow, domain: FailureDomainKey) {
  if (domain === "calibration") {
    const ece = "ece" in row.deltas ? row.deltas.ece : row.metrics.ece;
    const brier = "brier_score" in row.deltas ? row.deltas.brier_score : row.metrics.brier_score;
    const formatter =
      "ece" in row.deltas || "brier_score" in row.deltas ? formatSignedMetric : formatMetric;
    return `ECE ${formatter(ece)} / Brier ${formatter(brier)}`;
  }

  const metricKey =
    domain === "worst_group"
      ? "worst_group_f1"
      : domain === "ood"
        ? "ood_macro_f1"
        : "id_macro_f1";
  const hasDelta = metricKey in row.deltas;
  const value = hasDelta ? row.deltas[metricKey] : row.metrics[metricKey];
  return hasDelta ? formatSignedMetric(value) : formatMetric(value);
}

export function FailureSeededDetail({ rows, domain }: FailureSeededDetailProps) {
  if (rows.length === 0) {
    return (
      <p className="text-sm leading-6 text-muted-foreground">
        Scout-only evidence remains summarized in the saved report package.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div
          key={`${domain}-${row.seed}`}
          className="rounded-[18px] border border-border/70 bg-background/55 px-4 py-3"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="muted">Seed {row.seed}</Badge>
            {row.verdict ? <Badge tone="default">{row.verdict}</Badge> : null}
          </div>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
            <p className="font-mono text-xs text-muted-foreground">{row.runId ?? row.evalId}</p>
            <p className="text-sm font-semibold text-foreground">{renderDomainValue(row, domain)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
