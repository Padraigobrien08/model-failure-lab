import { Badge } from "@/components/ui/badge";
import { formatCount, formatLabel } from "@/lib/formatters";
import type { OverviewSnapshot } from "@/lib/manifest/types";

type StatusStripProps = {
  snapshot: OverviewSnapshot;
};

export function StatusStrip({ snapshot }: StatusStripProps) {
  const cards = [
    {
      label: "Final robustness",
      value: formatLabel(snapshot.finalRobustnessVerdict),
      tone: "accent" as const,
      detail: "Saved from the official closeout package.",
    },
    {
      label: "Expansion gate",
      value: formatLabel(snapshot.datasetExpansionRecommendation),
      tone: "default" as const,
      detail: "Current dataset-expansion decision and reopen rule.",
    },
    {
      label: "Visible reports",
      value: formatCount(snapshot.inventoryCounts.reports),
      tone: "muted" as const,
      detail: "Default-visible report surfaces in the current manifest.",
    },
  ];

  return (
    <section className="grid gap-3 lg:grid-cols-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-[18px] border border-border/70 bg-background/55 px-4 py-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {card.label}
              </p>
              <p className="mt-2 text-[1.55rem] font-semibold tracking-[-0.04em] text-foreground">
                {card.value}
              </p>
            </div>
            <Badge tone={card.tone}>{card.label}</Badge>
          </div>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">{card.detail}</p>
        </div>
      ))}
    </section>
  );
}
