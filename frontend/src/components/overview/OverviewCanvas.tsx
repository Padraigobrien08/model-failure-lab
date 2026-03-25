import { ArrowRight, Crosshair, ShieldAlert, Waves } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { formatLabel } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import type { OverviewSnapshot } from "@/lib/manifest/types";

type OverviewCanvasProps = {
  snapshot: OverviewSnapshot;
};

export function OverviewCanvas({ snapshot }: OverviewCanvasProps) {
  const highlightCards = [
    {
      title: "Stable calibration lane",
      icon: Waves,
      body:
        "Temperature scaling remains the cleanest reliability improvement. The React surface treats it as the reference calibration story, not as a robustness win.",
      value: formatLabel(snapshot.mitigationLabels.temperature_scaling),
    },
    {
      title: "Mixed robustness lane",
      icon: ShieldAlert,
      body:
        "Reweighting still carries the best current robustness signal, but the saved evidence does not support a clean, stable mitigation claim.",
      value: formatLabel(snapshot.mitigationLabels.reweighting),
    },
    {
      title: "Reopen conditions",
      icon: Crosshair,
      body:
        snapshot.reopenConditions[0] ??
        "Future expansion stays closed until a robustness lane produces stable seeded gains.",
      value: `${snapshot.reopenConditions.length} tracked`,
    },
  ];

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.92fr]">
      <section className="rounded-[20px] border border-border/70 bg-background/55 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Verdict Trace</Badge>
          <Badge tone="muted">Manifest-backed</Badge>
        </div>

        <div className="mt-4 grid gap-3">
          {snapshot.summaryBullets.map((bullet, index) => (
            <div
              key={bullet}
              className="grid gap-3 rounded-[16px] border border-border/70 bg-card/45 px-4 py-4 sm:grid-cols-[40px_minmax(0,1fr)]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/20 bg-primary/10 text-sm font-semibold text-primary">
                {index + 1}
              </div>
              <p className="text-sm leading-6 text-foreground">{bullet}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded-[16px] border border-border/70 bg-card/45 px-4 py-4 text-sm leading-6 text-muted-foreground">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
            Next inspection path
          </p>
          <p className="mt-2">
            Start with the ranking story in Comparisons, then move into Failure Explorer when you
            need to separate robustness tradeoffs from calibration behavior.
          </p>
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/comparisons" className={cn(buttonVariants({ variant: "default" }))}>
            Inspect Failure Traces
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
          <Link to="/evidence" className={cn(buttonVariants({ variant: "outline" }))}>
            Review Evidence Paths
          </Link>
        </div>
      </section>

      <div className="grid gap-3">
        {highlightCards.map((card) => {
          const Icon = card.icon;
          return (
            <section
              key={card.title}
              className="rounded-[18px] border border-border/70 bg-background/55 px-4 py-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    {card.title}
                  </p>
                  <p className="text-[1.55rem] font-semibold tracking-[-0.04em] text-foreground">
                    {card.value}
                  </p>
                </div>
                <div className="rounded-full border border-primary/20 bg-primary/10 p-3 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{card.body}</p>
            </section>
          );
        })}

        <section className="rounded-[18px] border border-border/70 bg-background/55 px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Scope reminder
          </p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Official evidence stays default. Exploratory methods stay behind an explicit scope
            change so the final verdict remains readable.
          </p>
        </section>
      </div>
    </div>
  );
}
