import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";
import type { SummaryRouteVerdictStrip } from "@/lib/summaryRoute";

type VerdictStripProps = {
  verdict: SummaryRouteVerdictStrip;
};

function getVerdictTone(status: SummaryRouteVerdictStrip["status"]) {
  return status === "stable" ? "accent" : "default";
}

export function VerdictStrip({ verdict }: VerdictStripProps) {
  return (
    <section className="rounded-[18px] border border-border/70 bg-card/45 px-4 py-4 sm:px-5">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Final verdict</Badge>
          <Badge tone={getVerdictTone(verdict.status)}>{formatLabel(verdict.status)}</Badge>
          {verdict.modifier ? <Badge tone="exploratory">{verdict.modifier}</Badge> : null}
        </div>
        <p className="max-w-3xl text-sm leading-6 text-foreground">{verdict.implication}</p>
      </div>
    </section>
  );
}
