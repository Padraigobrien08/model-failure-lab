import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { MethodHeader } from "@/components/method/MethodHeader";
import { MethodMetricStrip } from "@/components/method/MethodMetricStrip";
import { RunTable } from "@/components/method/RunTable";
import { buildMethodRouteModel, getDefaultMethodRunEntityId, resolveMethodRunEntityId } from "@/lib/methodRoute";

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
      <RunTable
        laneId={methodRoute.laneId}
        methodLabel={methodRoute.methodLabel}
        onSelectRun={setSelectedRunEntityId}
        runs={methodRoute.runs}
        scope={scope}
        selectedEntityId={selectedRunEntityId}
      />
    </section>
  );
}
