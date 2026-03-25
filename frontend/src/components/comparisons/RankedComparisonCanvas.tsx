import { Link } from "react-router-dom";

import { ComparisonRankCard } from "@/components/comparisons/ComparisonRankCard";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
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
      <WorkbenchSection
        eyebrow="Ranking"
        title="Ranked comparison canvas"
        description="Read the official lane ordering first, then expand into per-seed breakdown or evidence links once you know which lane you want to inspect."
      >
        <div className="grid gap-4 xl:grid-cols-3">
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
        </div>
      </WorkbenchSection>

      <WorkbenchSection
        eyebrow={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="accent">Domain drillthrough</Badge>
            {selectedDomain ? <Badge tone="default">{selectedDomain}</Badge> : null}
          </div>
        }
        title="Why the ranking lands this way"
        description="Each domain panel keeps the baseline reference visible, then shows how the official methods move relative to that anchor. Carry any panel focus into Failure Explorer when you need the deeper domain workspace."
      >
        <div className="grid gap-4 xl:grid-cols-2">
          {domains.map((domain) => (
            <div
              key={domain.domain}
              className={cn(
                "rounded-[18px] border border-border/70 bg-card/55 p-4",
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
                      "flex w-full items-center justify-between rounded-[16px] border border-border/70 bg-background/55 px-4 py-3 text-left transition-colors",
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
        </div>
      </WorkbenchSection>
    </div>
  );
}
