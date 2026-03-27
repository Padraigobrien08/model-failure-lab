import { formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { RunRouteMetric } from "@/lib/runRoute";
import { cn } from "@/lib/utils";

type RunMetricStripProps = {
  metrics: RunRouteMetric[];
};

export function RunMetricStrip({ metrics }: RunMetricStripProps) {
  return (
    <section aria-label="Run metrics" className="overflow-hidden rounded-[16px] border border-border/70">
      <div className={cn("grid gap-px bg-border/70", metrics.length > 2 ? "md:grid-cols-3" : "md:grid-cols-2")}>
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="bg-background/80 px-4 py-3"
            data-testid={`run-metric-${metric.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
          >
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              {metric.label}
            </p>
            <p className="mt-2 text-lg font-semibold text-foreground">{formatMetric(metric.value)}</p>
            <p
              className={cn(
                "mt-1 text-sm",
                getMetricTextTone(metric.deltaVsBaseline, Boolean(metric.lowerIsBetter)),
              )}
            >
              {metric.deltaVsBaseline === null
                ? "No baseline delta"
                : `${formatSignedMetric(metric.deltaVsBaseline)} vs baseline`}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
