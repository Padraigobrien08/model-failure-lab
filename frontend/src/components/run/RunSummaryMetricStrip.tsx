import { Card, CardContent } from "@/components/ui/card";

type RunSummaryMetricStripProps = {
  metrics: {
    attemptedCaseCount: number;
    classifiedCaseCount: number;
    executionErrorCount: number;
    unclassifiedCount: number;
    failureRate: number | null;
    classificationCoverage: number | null;
  };
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatPercent(value: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function RunSummaryMetricStrip({ metrics }: RunSummaryMetricStripProps) {
  const items = [
    { label: "Attempted", value: formatCount(metrics.attemptedCaseCount) },
    { label: "Classified", value: formatCount(metrics.classifiedCaseCount) },
    { label: "Errors", value: formatCount(metrics.executionErrorCount) },
    { label: "Unclassified", value: formatCount(metrics.unclassifiedCount) },
    { label: "Failure rate", value: formatPercent(metrics.failureRate) },
    { label: "Coverage", value: formatPercent(metrics.classificationCoverage) },
  ];

  return (
    <section aria-label="Run metrics">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <Card key={item.label} className="rounded-[22px] bg-card/75">
            <CardContent className="px-5 py-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {item.label}
              </p>
              <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                {item.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
