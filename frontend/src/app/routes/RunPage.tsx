import { useParams, useSearchParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { RunHeader } from "@/components/run/RunHeader";
import { InterpretationNote } from "@/components/run/InterpretationNote";
import { RunMetricStrip } from "@/components/run/RunMetricStrip";
import { buildRunRouteModel } from "@/lib/runRoute";

export function RunPage() {
  const { runId } = useParams();
  const [searchParams] = useSearchParams();
  const { scope } = useTraceScope();
  const runRoute = buildRunRouteModel(runId, scope, {
    laneId: searchParams.get("lane"),
    methodId: searchParams.get("method"),
  });

  return (
    <section className="space-y-6">
      <RunHeader
        breadcrumbs={runRoute.breadcrumbs}
        laneLabel={runRoute.laneLabel}
        methodLabel={runRoute.methodLabel}
        runId={runRoute.runId}
        seed={runRoute.seed}
        status={runRoute.status}
      />
      <RunMetricStrip metrics={runRoute.metricStrip} />
      <InterpretationNote note={runRoute.interpretationNote} />
    </section>
  );
}
