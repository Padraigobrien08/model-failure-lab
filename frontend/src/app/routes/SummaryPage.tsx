import { useTraceScope } from "@/app/scope";
import { LaneSummaryPanel } from "@/components/summary/LaneSummaryPanel";
import { VerdictStrip } from "@/components/summary/VerdictStrip";
import { buildSummaryRouteModel } from "@/lib/summaryRoute";

export function SummaryPage() {
  const { scope } = useTraceScope();
  const summaryRoute = buildSummaryRouteModel(scope);

  return (
    <section className="space-y-5">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">Where should I look?</h1>
        <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
          Start with the lane that best explains the verdict, then jump directly into the supporting
          method path.
        </p>
      </header>

      <VerdictStrip verdict={summaryRoute.verdict} />

      <div className="space-y-4">
        {summaryRoute.laneOrder.map((laneId) => (
          <LaneSummaryPanel key={laneId} lane={summaryRoute.lanes[laneId]} scope={scope} />
        ))}
      </div>
    </section>
  );
}
