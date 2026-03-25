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
import type { FailureDomainKey, FailureDomainItemModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";
import { FailureSeededDetail } from "@/components/failure/FailureSeededDetail";

type FailureDomainPanelProps = {
  domain: FailureDomainKey;
  item: FailureDomainItemModel;
  isSelected: boolean;
  onSelectMethod: (methodName: string) => void;
  onInspectMethod: (methodName: string) => void;
  actions: Array<{ label: string; path: string }>;
};

function renderMetric(item: FailureDomainItemModel, domain: FailureDomainKey) {
  if (domain === "calibration") {
    const formatter =
      item.comparisonMode === "baseline_metric" ? formatMetric : formatSignedMetric;

    return {
      label: `ECE ${formatter(item.eceMean)} / Brier ${formatter(item.brierMean)}`,
      className: cn(
        getMetricTextTone(item.eceMean, true, item.comparisonMode),
        getMetricTextTone(item.brierMean, true, item.comparisonMode),
      ),
    };
  }

  const formatter = item.comparisonMode === "baseline_metric" ? formatMetric : formatSignedMetric;
  return {
    label: formatter(item.mean),
    className: getMetricTextTone(item.mean, false, item.comparisonMode),
  };
}

export function FailureDomainPanel({
  domain,
  item,
  isSelected,
  onSelectMethod,
  onInspectMethod,
  actions,
}: FailureDomainPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const metric = renderMetric(item, domain);

  return (
    <Card
      className={cn(
        "bg-background/60",
        isSelected ? "border-primary/35 shadow-panel" : "",
        item.isExploratory ? "border-dashed" : "",
      )}
    >
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={item.isExploratory ? "exploratory" : "default"}>{item.verdict}</Badge>
          {item.isExploratory ? <Badge tone="exploratory">Exploratory</Badge> : null}
          <Badge tone="muted">{formatComparisonMode(item.comparisonMode)}</Badge>
        </div>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <CardDescription>Failure domain breakdown</CardDescription>
            <CardTitle className="text-[1.75rem]">{item.displayName}</CardTitle>
            <p className="text-sm leading-6 text-muted-foreground">{item.storyNote}</p>
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
        <div className="rounded-[22px] border border-border/70 bg-card/75 px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Aggregate summary
          </p>
          <p className={cn("mt-2 text-2xl font-semibold", metric.className)}>{metric.label}</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Seeds tracked: {item.seedCount}
            {domain !== "calibration" ? ` | std ${formatMetric(item.std)}` : ""}
          </p>
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
          {actions.map((action) => (
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

        {expanded ? <FailureSeededDetail rows={item.seedBreakdown} domain={domain} /> : null}
      </CardContent>
    </Card>
  );
}
