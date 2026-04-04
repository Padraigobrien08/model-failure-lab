import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ComparisonDetail } from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

type ComparisonDeltaStripProps = {
  signal: ComparisonDetail["signal"];
  metrics: ComparisonDetail["metrics"];
  compatible: boolean;
  onOpenDriverCase?: (caseId: string) => void;
};

function formatPercent(value: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function formatSignedPercent(value: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  const percent = value * 100;
  return `${percent > 0 ? "+" : ""}${percent.toFixed(1)}%`;
}

function deltaTone(
  value: number | null,
  invertPolarity = false,
): string {
  if (value == null || Number.isNaN(value)) {
    return "text-foreground";
  }

  const normalized = invertPolarity ? -value : value;
  if (normalized > 0) {
    return "text-primary";
  }
  if (normalized < 0) {
    return "text-destructive";
  }
  return "text-foreground";
}

function formatDeltaNarrative(
  metrics: ComparisonDetail["metrics"],
  compatible: boolean,
): {
  headline: string;
  copy: string;
} {
  if (!compatible) {
    return {
      headline: "No aggregate directional delta was computed.",
      copy:
        "This saved report still matters: use it to understand why the runs are incompatible and where the shared scope breaks down.",
    };
  }

  if (
    metrics.delta.failureRate === 0 &&
    metrics.delta.classificationCoverage === 0 &&
    metrics.delta.executionSuccessRate === 0
  ) {
    return {
      headline: "Baseline and candidate stayed flat at the aggregate level.",
      copy:
        "Use the grouped transitions below to see whether the same headline metrics are hiding offsetting case-level changes.",
    };
  }

  const failureDelta = metrics.delta.failureRate;
  if (failureDelta !== null && !Number.isNaN(failureDelta)) {
    const deltaMagnitude = `${Math.abs(failureDelta * 100).toFixed(1)} pts`;
    if (failureDelta < 0) {
      return {
        headline: `Candidate reduced saved failure rate by ${deltaMagnitude}.`,
        copy:
          "Check whether the improvement holds across grouped transitions or if it was concentrated in a narrow slice of cases.",
      };
    }
    if (failureDelta > 0) {
      return {
        headline: `Candidate increased saved failure rate by ${deltaMagnitude}.`,
        copy:
          "Use the grouped transitions to isolate exactly which cases regressed and whether coverage or execution changed alongside them.",
      };
    }
  }

  return {
    headline: "Coverage or execution shifted without changing saved failure rate.",
    copy:
      "Read the metric deltas and shared-case scope together before interpreting the grouped transition evidence.",
  };
}

function MetricCard({
  label,
  baseline,
  candidate,
  delta,
  invertPolarity = false,
}: {
  label: string;
  baseline: number | null;
  candidate: number | null;
  delta: number | null;
  invertPolarity?: boolean;
}) {
  return (
    <div className="rounded-[20px] border border-border/60 bg-background/60 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className={cn("mt-3 text-2xl font-semibold", deltaTone(delta, invertPolarity))}>
        {formatSignedPercent(delta)}
      </p>
      <p className="mt-2 text-sm text-muted-foreground">
        Baseline {formatPercent(baseline)} {"->"} Candidate {formatPercent(candidate)}
      </p>
    </div>
  );
}

export function ComparisonDeltaStrip({
  signal,
  metrics,
  compatible,
  onOpenDriverCase,
}: ComparisonDeltaStripProps) {
  const narrative = formatDeltaNarrative(metrics, compatible);

  return (
    <section className="space-y-4" aria-label="Comparison deltas">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Stage 1 · Delta summary
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Directional change at a glance
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Orient on the aggregate shift first, then use the shared-case scope and grouped evidence
          below to explain it.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1.95fr)]">
        <Card className="rounded-[24px] bg-card/75">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg">Comparison readout</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
              {narrative.headline}
            </p>
            <p className="text-sm leading-6 text-muted-foreground">{narrative.copy}</p>
            <div className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Signal verdict
                </p>
                <span className="text-sm font-semibold text-foreground">{signal.verdict}</span>
                <span className="text-xs text-muted-foreground">
                  severity {formatPercent(signal.severity)}
                </span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                Regression {formatPercent(signal.regressionScore)} · Improvement{" "}
                {formatPercent(signal.improvementScore)}
              </p>
              {signal.topDrivers.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {signal.topDrivers.map((driver) => {
                    const primaryCaseId = driver.caseIds[0] ?? null;
                    return (
                      <button
                        key={`${driver.driverRank}-${driver.failureType}`}
                        type="button"
                        className="rounded-full border border-border/60 bg-card/80 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-card"
                        disabled={primaryCaseId === null || onOpenDriverCase === undefined}
                        onClick={() => {
                          if (primaryCaseId && onOpenDriverCase) {
                            onOpenDriverCase(primaryCaseId);
                          }
                        }}
                      >
                        {driver.failureType} {formatSignedPercent(driver.delta)}
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Baseline cases
                </p>
                <p className="mt-2 text-sm text-foreground">
                  {metrics.baseline.attemptedCaseCount} attempted
                </p>
              </div>
              <div className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Candidate cases
                </p>
                <p className="mt-2 text-sm text-foreground">
                  {metrics.candidate.attemptedCaseCount} attempted
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[24px] bg-card/75">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg">
              {compatible ? "Baseline vs candidate metrics" : "Saved metric context"}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-3">
            <MetricCard
              label="Failure rate"
              baseline={metrics.baseline.failureRate}
              candidate={metrics.candidate.failureRate}
              delta={metrics.delta.failureRate}
              invertPolarity
            />
            <MetricCard
              label="Classification coverage"
              baseline={metrics.baseline.classificationCoverage}
              candidate={metrics.candidate.classificationCoverage}
              delta={metrics.delta.classificationCoverage}
            />
            <MetricCard
              label="Execution success"
              baseline={metrics.baseline.executionSuccessRate}
              candidate={metrics.candidate.executionSuccessRate}
              delta={metrics.delta.executionSuccessRate}
            />
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
