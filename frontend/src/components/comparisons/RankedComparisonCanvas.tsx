import { Link } from "react-router-dom";

import { ComparisonRankCard } from "@/components/comparisons/ComparisonRankCard";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatComparisonMode, formatMetric, formatSignedMetric } from "@/lib/formatters";
import type { ComparisonCardModel, FailureDomainKey, FailureDomainModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type RankedComparisonCanvasProps = {
  items: ComparisonCardModel[];
  domains: FailureDomainModel[];
  selectedMethod: string | null;
  selectedDomain: FailureDomainKey | null;
  onSelectMethod: (methodName: string) => void;
  onSelectDomain: (domain: FailureDomainKey) => void;
  onInspectMethod: (methodName: string) => void;
};

function renderDomainMetric(
  comparisonMode: string,
  mean: number | null | undefined,
  eceMean?: number | null,
  brierMean?: number | null,
) {
  if (comparisonMode === "baseline_metric") {
    if (eceMean !== undefined || brierMean !== undefined) {
      return `ECE ${formatMetric(eceMean)} / Brier ${formatMetric(brierMean)}`;
    }

    return formatMetric(mean);
  }

  if (eceMean !== undefined || brierMean !== undefined) {
    return `ECE ${formatSignedMetric(eceMean)} / Brier ${formatSignedMetric(brierMean)}`;
  }

  return formatSignedMetric(mean);
}

export function RankedComparisonCanvas({
  items,
  domains,
  selectedMethod,
  selectedDomain,
  onSelectMethod,
  onSelectDomain,
  onInspectMethod,
}: RankedComparisonCanvasProps) {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-3">
        {items.map((item, index) => (
          <ComparisonRankCard
            key={item.methodName}
            item={item}
            rank={index + 1}
            isSelected={selectedMethod === item.methodName}
            onSelectMethod={onSelectMethod}
            onInspectMethod={onInspectMethod}
          />
        ))}
      </section>

      <Card className="bg-background/60">
        <CardHeader className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="accent">Domain drillthrough</Badge>
            {selectedDomain ? <Badge tone="default">{selectedDomain}</Badge> : null}
          </div>
          <CardTitle className="text-[2rem] tracking-[-0.05em]">
            Why the ranking lands this way
          </CardTitle>
          <CardDescription className="max-w-3xl text-base leading-7">
            Each domain panel keeps the baseline reference visible, then shows how the official
            methods move relative to that anchor. Drill into any panel to carry the same focus into
            the Failure Explorer.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 xl:grid-cols-2">
          {domains.map((domain) => (
            <div
              key={domain.domain}
              className={cn(
                "rounded-[24px] border border-border/70 bg-card/70 p-5",
                selectedDomain === domain.domain ? "border-primary/35 shadow-panel" : "",
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    {domain.label}
                  </p>
                  <h3 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
                    {domain.description}
                  </h3>
                </div>
                <Link
                  to="/failure-explorer"
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                  onClick={() => onSelectDomain(domain.domain)}
                >
                  Trace {domain.label}
                </Link>
              </div>

              <div className="mt-4 space-y-3">
                {domain.items.map((item) => (
                  <button
                    key={`${domain.domain}-${item.methodName}`}
                    type="button"
                    className={cn(
                      "flex w-full items-center justify-between rounded-[20px] border border-border/70 bg-background/55 px-4 py-3 text-left transition-colors",
                      selectedMethod === item.methodName ? "border-primary/35 bg-primary/5" : "",
                      item.isExploratory ? "border-dashed" : "",
                    )}
                    onClick={() => onSelectMethod(item.methodName)}
                  >
                    <span className="space-y-1">
                      <span className="block text-sm font-semibold text-foreground">
                        {item.displayName}
                      </span>
                      <span className="block text-xs text-muted-foreground">
                        {formatComparisonMode(item.comparisonMode)}
                      </span>
                    </span>
                    <span className="text-sm font-semibold text-foreground">
                      {renderDomainMetric(
                        item.comparisonMode,
                        item.mean,
                        item.eceMean,
                        item.brierMean,
                      )}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
