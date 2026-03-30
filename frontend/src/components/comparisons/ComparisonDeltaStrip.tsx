import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ComparisonDetail } from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

type ComparisonDeltaStripProps = {
  metrics: ComparisonDetail["metrics"];
  compatible: boolean;
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
  metrics,
  compatible,
}: ComparisonDeltaStripProps) {
  return (
    <section className="space-y-4" aria-label="Comparison deltas">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Delta summary
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Directional change at a glance
        </h2>
      </div>

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
    </section>
  );
}
