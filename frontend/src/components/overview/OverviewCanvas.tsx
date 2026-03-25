import { ArrowRight, Crosshair, ShieldAlert, Waves } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
      <Card className="bg-background/65">
        <CardHeader className="space-y-4">
          <Badge tone="accent">Overview Launchpad</Badge>
          <div className="space-y-4">
            <CardTitle className="max-w-3xl text-[2.25rem] leading-[1.05] tracking-[-0.05em]">
              Trace the failure story from final verdicts down into the evidence routes without
              leaving the manifest-backed contract.
            </CardTitle>
            <CardDescription className="max-w-2xl text-base leading-7">
              This React shell turns the final benchmark closeout into a debugging workbench. The
              official story remains stable calibration, still-mixed robustness, and deferred
              expansion under explicit reopen conditions.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2">
            {snapshot.summaryBullets.map((bullet) => (
              <div
                key={bullet}
                className="rounded-[22px] border border-border/80 bg-card/70 p-4 text-sm leading-6 text-foreground"
              >
                {bullet}
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <Link to="/comparisons" className={cn(buttonVariants({ variant: "default" }))}>
              Inspect Failure Traces
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link to="/evidence" className={cn(buttonVariants({ variant: "outline" }))}>
              Review Evidence Paths
            </Link>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {highlightCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.title} className="bg-background/55">
              <CardHeader className="flex flex-row items-start justify-between pb-3">
                <div className="space-y-2">
                  <CardDescription>{card.title}</CardDescription>
                  <CardTitle className="text-2xl">{card.value}</CardTitle>
                </div>
                <div className="rounded-full border border-primary/20 bg-primary/10 p-3 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
              </CardHeader>
              <CardContent className="pt-0 text-sm leading-6 text-muted-foreground">
                {card.body}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
