import { formatMetric, formatSignedMetric, getMetricTextTone } from "@/lib/formatters";
import type { MethodRouteMetric } from "@/lib/methodRoute";
import { cn } from "@/lib/utils";

type MethodMetricStripProps = {
  metrics: MethodRouteMetric[];
};

export function MethodMetricStrip({ metrics }: MethodMetricStripProps) {
  return (
    <section aria-label="Method metrics" className="overflow-hidden rounded-[16px] border border-border/70">
      <div className="grid gap-px bg-border/70 md:grid-cols-3">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="bg-background/80 px-4 py-3"
            data-testid={`metric-${metric.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
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
