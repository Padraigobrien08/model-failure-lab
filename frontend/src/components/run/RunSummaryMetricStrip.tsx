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
          Read the operating profile first: run volume, failure rate, execution quality, and
          classification coverage.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.12fr)_minmax(0,0.88fr)]">
        <Card className="rounded-[24px] border-border/70 bg-card/82">
          <CardContent className="space-y-5 px-5 py-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Failure rate
                </p>
                <p className="text-4xl font-semibold tracking-[-0.06em] text-foreground">
                  {formatPercent(metrics.failureRate)}
                </p>
              </div>
              <div className="rounded-[20px] border border-border/60 bg-background/60 px-4 py-3 text-right">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Failure cases
                </p>
                <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                  {formatCount(metrics.failureCaseCount)}
                </p>
              </div>
            </div>

            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {formatCount(metrics.failureCaseCount)} saved failure cases across{" "}
              {formatCount(metrics.attemptedCaseCount)} attempted prompts. Use this readout to
              decide whether to stay at the summary level or move straight into evidence.
            </p>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Attempted
                </p>
                <p className="mt-2 text-xl font-semibold tracking-[-0.04em] text-foreground">
                  {formatCount(metrics.attemptedCaseCount)}
                </p>
              </div>
              <div className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Classified
                </p>
                <p className="mt-2 text-xl font-semibold tracking-[-0.04em] text-foreground">
                  {formatCount(metrics.classifiedCaseCount)}
                </p>
              </div>
              <div className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Coverage
                </p>
                <p className="mt-2 text-xl font-semibold tracking-[-0.04em] text-foreground">
                  {formatPercent(metrics.classificationCoverage)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-3 sm:grid-cols-2">
          {[items[2], items[3], items[4], items[5]].map((item) => (
            <Card key={item.label} className="rounded-[22px] bg-card/72">
              <CardContent className="px-4 py-4">
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
      </div>
    </section>
  );
}
