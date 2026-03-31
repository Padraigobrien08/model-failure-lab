import { Card, CardContent } from "@/components/ui/card";

type RunSummaryMetricStripProps = {
  metrics: {
    attemptedCaseCount: number;
    classifiedCaseCount: number;
    executionErrorCount: number;
    unclassifiedCount: number;
    executionSuccessRate: number | null;
    failureCaseCount: number;
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
    { label: "Coverage", value: formatPercent(metrics.classificationCoverage) },
    { label: "Execution success", value: formatPercent(metrics.executionSuccessRate) },
  ];

  return (
    <section className="space-y-4" aria-label="Run metrics">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Stage 2 · Overall failure shape
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Overall failure shape
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Read the operational profile before diving into causes: run volume, saved failure rate,
          execution quality, and classification coverage.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <Card className="rounded-[24px] bg-card/80 md:col-span-2 xl:col-span-1">
          <CardContent className="space-y-3 px-5 py-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Failure rate
            </p>
            <p className="text-3xl font-semibold tracking-[-0.05em] text-foreground">
              {formatPercent(metrics.failureRate)}
            </p>
            <p className="text-sm leading-6 text-muted-foreground">
              {formatCount(metrics.failureCaseCount)} saved failure cases across{" "}
              {formatCount(metrics.attemptedCaseCount)} attempted prompts.
            </p>
          </CardContent>
        </Card>

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
