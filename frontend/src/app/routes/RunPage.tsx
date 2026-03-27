import { useParams, useSearchParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { ArtifactSummary } from "@/components/run/ArtifactSummary";
import { InspectorPanel } from "@/components/run/InspectorPanel";
import { RunHeader } from "@/components/run/RunHeader";
import { InterpretationNote } from "@/components/run/InterpretationNote";
import { LineageStack } from "@/components/run/LineageStack";
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
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_19rem]">
        <div className="space-y-6">
          <InterpretationNote note={runRoute.interpretationNote} />
          <LineageStack lineage={runRoute.lineage} />
          <ArtifactSummary artifacts={runRoute.artifacts} />
        </div>
        <InspectorPanel entity={runRoute.inspector} />
      </div>
    </section>
  );
}
