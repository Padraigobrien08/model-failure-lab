import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    },
    {
      label: "Expansion gate",
      value: formatLabel(snapshot.datasetExpansionRecommendation),
      tone: "default" as const,
    },
    {
      label: "Official reports",
      value: formatCount(snapshot.inventoryCounts.reports),
      tone: "muted" as const,
    },
  ];

  return (
    <section className="grid gap-4 lg:grid-cols-3">
      {cards.map((card) => (
        <Card key={card.label} className="bg-background/65">
          <CardHeader className="flex flex-row items-start justify-between pb-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {card.label}
              </p>
              <CardTitle className="mt-3 text-2xl">{card.value}</CardTitle>
            </div>
            <Badge tone={card.tone}>{card.label}</Badge>
          </CardHeader>
          <CardContent className="pt-0 text-sm leading-6 text-muted-foreground">
            {card.label === "Official reports"
              ? "Default-visible report surfaces available in the current manifest."
              : "Derived directly from the saved closeout and official evidence package."}
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
