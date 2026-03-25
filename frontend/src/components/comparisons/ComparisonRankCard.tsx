import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  formatComparisonMode,
  formatMetric,
  formatSignedMetric,
  getMetricTextTone,
} from "@/lib/formatters";
import type { ComparisonCardMetric, ComparisonCardModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";
import { SeededComparisonDetail } from "@/components/comparisons/SeededComparisonDetail";

type ComparisonRankCardProps = {
  item: ComparisonCardModel;
  rank: number;
  isSelected: boolean;
  onSelectMethod: (methodName: string) => void;
  onInspectMethod: (methodName: string) => void;
};

function renderMetric(metric: ComparisonCardMetric) {
  if (metric.comparisonMode === "baseline_metric") {
    return formatMetric(metric.value);
  }

  return formatSignedMetric(metric.value);
}

export function ComparisonRankCard({
  item,
  rank,
  isSelected,
  onSelectMethod,
  onInspectMethod,
}: ComparisonRankCardProps) {
  const [expanded, setExpanded] = useState(false);
  const verdictTone = item.isExploratory
    ? "exploratory"
    : item.verdict === "stable"
      ? "accent"
      : "default";

  return (
    <Card
      className={cn(
        "rounded-[18px] bg-background/55 transition-shadow",
        isSelected ? "border-primary/40 shadow-rail" : "border-border/70",
        item.isExploratory ? "border-dashed" : "",
      )}
    >
      <CardHeader className="gap-4 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="muted">#{rank}</Badge>
          <Badge tone={verdictTone}>{item.verdict}</Badge>
          {item.isExploratory ? <Badge tone="exploratory">Exploratory</Badge> : null}
          <Badge tone="default">{formatComparisonMode(item.comparisonMode)}</Badge>
        </div>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <CardDescription>Ranked method summary</CardDescription>
            <CardTitle className="text-[1.85rem]">{item.displayName}</CardTitle>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">{item.storyNote}</p>
          </div>
          <Button
            variant={isSelected ? "default" : "outline"}
            size="sm"
            aria-pressed={isSelected}
            onClick={() => onSelectMethod(item.methodName)}
          >
            {isSelected ? "Focused lane" : "Focus lane"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {Object.values(item.metrics).map((metric) => (
            <div
              key={metric.label}
              className="rounded-[16px] border border-border/70 bg-card/45 px-4 py-4"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {metric.label}
              </p>
              <p
                className={cn(
                  "mt-2 text-2xl font-semibold",
                  getMetricTextTone(
                    metric.value,
                    metric.invertPolarity,
                    metric.comparisonMode,
                  ),
                )}
              >
                {renderMetric(metric)}
              </p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                std {formatMetric(metric.std)}
              </p>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <span>{item.seedCount} seeds tracked</span>
          {item.seededInterpretation ? (
            <span>Seeded interpretation: {item.seededInterpretation}</span>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            aria-label={`Inspect ${item.displayName} evidence`}
            onClick={() => onInspectMethod(item.methodName)}
            disabled={!item.representativeRunId}
          >
            Inspect evidence
          </Button>
          {item.actions.map((action) => (
            <a
              key={`${item.methodName}-${action.label}`}
              href={action.path}
              target="_blank"
              rel="noreferrer"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              {action.label}
            </a>
          ))}
          <Button variant="ghost" size="sm" onClick={() => setExpanded((value) => !value)}>
            {expanded ? "Hide per-seed breakdown" : "Show per-seed breakdown"}
          </Button>
        </div>

        {expanded ? <SeededComparisonDetail rows={item.seedBreakdown} /> : null}
      </CardContent>
    </Card>
  );
}
