import { useTraceScope } from "@/app/scope";
import { ScopeRouteNote } from "@/components/layout/ScopeRouteNote";
import { LaneSummaryPanel } from "@/components/summary/LaneSummaryPanel";
import { VerdictStrip } from "@/components/summary/VerdictStrip";
import { buildSummaryRouteModel } from "@/lib/summaryRoute";

export function SummaryPage() {
  const { scope } = useTraceScope();
  const summaryRoute = buildSummaryRouteModel(scope);

  return (
    <section className="space-y-4">
      <header className="space-y-1.5">
        <h1 className="text-xl font-semibold tracking-[-0.04em] text-foreground sm:text-2xl">
          Where should I look?
        </h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
          Start with the lane that best explains the verdict, then jump directly into the supporting
          method path.
        </p>
      </header>

      <VerdictStrip verdict={summaryRoute.verdict} />
      {summaryRoute.scopeNote ? <ScopeRouteNote message={summaryRoute.scopeNote} /> : null}

      <div className="space-y-3">
        {summaryRoute.laneOrder.map((laneId) => (
          <LaneSummaryPanel key={laneId} lane={summaryRoute.lanes[laneId]} scope={scope} />
        ))}
      </div>
    </section>
  );
}
