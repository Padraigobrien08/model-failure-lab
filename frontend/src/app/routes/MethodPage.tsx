import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { MethodHeader } from "@/components/method/MethodHeader";
import { MethodExplanation } from "@/components/method/MethodExplanation";
import { InspectorPanel } from "@/components/method/InspectorPanel";
import { LineageChain } from "@/components/method/LineageChain";
import { MethodMetricStrip } from "@/components/method/MethodMetricStrip";
import { RunTable } from "@/components/method/RunTable";
import {
  buildMethodRouteModel,
  getDefaultMethodRunEntityId,
  getMethodInspectorEntity,
  resolveMethodRunEntityId,
} from "@/lib/methodRoute";

export function MethodPage() {
  const { laneId, methodId } = useParams();
  const { scope } = useTraceScope();
  const methodRoute = buildMethodRouteModel(laneId, methodId, scope);
  const [selectedRunEntityId, setSelectedRunEntityId] = useState<string>(
    getDefaultMethodRunEntityId(methodRoute),
  );

  useEffect(() => {
    setSelectedRunEntityId((current) => resolveMethodRunEntityId(methodRoute, current));
  }, [laneId, methodId, scope]);

  const selectedInspectorEntity = getMethodInspectorEntity(methodRoute, selectedRunEntityId);

  return (
    <section className="space-y-6">
      <MethodHeader
        laneId={methodRoute.laneId}
        laneLabel={methodRoute.laneLabel}
        methodLabel={methodRoute.methodLabel}
        question="Why is this method judged this way?"
        scope={scope}
        status={methodRoute.status}
        summary={methodRoute.summary}
      />
      <MethodMetricStrip metrics={methodRoute.metricStrip} />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_19rem]">
        <div className="space-y-6">
          <RunTable
            laneId={methodRoute.laneId}
            methodId={methodRoute.methodId}
            methodLabel={methodRoute.methodLabel}
            onSelectRun={setSelectedRunEntityId}
            runs={methodRoute.runs}
            scope={scope}
            selectedEntityId={selectedRunEntityId}
          />
          <MethodExplanation sections={methodRoute.explanation} />
          <LineageChain lineage={methodRoute.lineage} scope={scope} />
        </div>
        <InspectorPanel entity={selectedInspectorEntity} scope={scope} />
      </div>
    </section>
  );
}
