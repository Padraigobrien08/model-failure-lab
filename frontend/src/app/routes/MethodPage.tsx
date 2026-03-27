import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { ScopeRouteNote } from "@/components/layout/ScopeRouteNote";
import { MethodHeader } from "@/components/method/MethodHeader";
import { MethodExplanation } from "@/components/method/MethodExplanation";
import { InspectorPanel } from "@/components/method/InspectorPanel";
import { LineageChain } from "@/components/method/LineageChain";
import { MethodMetricStrip } from "@/components/method/MethodMetricStrip";
import { RunTable } from "@/components/method/RunTable";
import { ScopeFilteredState } from "@/components/routes/ScopeFilteredState";
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
  const [selectedRunEntityId, setSelectedRunEntityId] = useState<string | null>(
    methodRoute.state === "ready" ? getDefaultMethodRunEntityId(methodRoute) : null,
  );

  useEffect(() => {
    if (methodRoute.state !== "ready") {
      setSelectedRunEntityId(null);
      return;
    }

    setSelectedRunEntityId((current) => resolveMethodRunEntityId(methodRoute, current));
  }, [laneId, methodId, scope]);

  if (methodRoute.state === "scope-hidden") {
    return (
      <section className="space-y-6">
        <MethodHeader
          laneId={methodRoute.laneId}
          laneLabel={methodRoute.laneLabel}
          methodLabel={methodRoute.methodLabel}
          methodScope={methodRoute.scope}
          question={methodRoute.question}
          scope={scope}
          status={methodRoute.status}
          summary={methodRoute.summary}
        />
        <ScopeFilteredState
          message={methodRoute.message}
          recoveryPath={methodRoute.recoveryPath}
          state="scope-hidden"
          testId="method-scope-hidden"
          title={methodRoute.methodLabel}
        />
      </section>
    );
  }

  const selectedInspectorEntity = getMethodInspectorEntity(
    methodRoute,
    selectedRunEntityId ?? getDefaultMethodRunEntityId(methodRoute),
  );

  return (
    <section className="space-y-5">
      <MethodHeader
        laneId={methodRoute.laneId}
        laneLabel={methodRoute.laneLabel}
        methodLabel={methodRoute.methodLabel}
        methodScope={methodRoute.scope}
        question="Why is this method judged this way?"
        scope={scope}
        status={methodRoute.status}
        statusModifier={methodRoute.statusModifier}
        summary={methodRoute.summary}
      />
      {methodRoute.scopeNote ? <ScopeRouteNote message={methodRoute.scopeNote} /> : null}
      <MethodMetricStrip metrics={methodRoute.metricStrip} />
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]">
        <div className="space-y-6">
          <RunTable
            laneId={methodRoute.laneId}
            methodId={methodRoute.methodId}
            methodLabel={methodRoute.methodLabel}
            onSelectRun={setSelectedRunEntityId}
            officialRuns={methodRoute.officialRuns}
            exploratoryRuns={methodRoute.exploratoryRuns}
            scope={scope}
            selectedEntityId={selectedRunEntityId ?? getDefaultMethodRunEntityId(methodRoute)}
          />
          <MethodExplanation sections={methodRoute.explanation} />
          <LineageChain lineage={methodRoute.lineage} scope={scope} />
        </div>
        <InspectorPanel entity={selectedInspectorEntity} scope={scope} />
      </div>
    </section>
  );
}
