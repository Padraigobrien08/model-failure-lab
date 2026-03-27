import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { ScopeRouteNote } from "@/components/layout/ScopeRouteNote";
import { InspectorPanel } from "@/components/lane/InspectorPanel";
import { LaneHeader } from "@/components/lane/LaneHeader";
import { MethodComparisonTable } from "@/components/lane/MethodComparisonTable";
import {
  buildLaneRouteModel,
  getDefaultLaneSelection,
  getLaneInspectorEntity,
  resolveLaneSelection,
  type LaneRouteMethodId,
  type LaneRouteSelection,
} from "@/lib/laneRoute";

export function LanePage() {
  const { laneId } = useParams();
  const { scope } = useTraceScope();
  const lane = buildLaneRouteModel(laneId, scope);
  const [selection, setSelection] = useState<LaneRouteSelection | null>(null);
  const [expandedMethodIds, setExpandedMethodIds] = useState<LaneRouteMethodId[]>([]);

  useEffect(() => {
    setSelection((current) => {
      const next = resolveLaneSelection(lane, current);

      if (
        current &&
        current.entityType === next.entityType &&
        current.entityId === next.entityId
      ) {
        return current;
      }

      return next;
    });
  }, [lane.laneId, scope]);

  useEffect(() => {
    setExpandedMethodIds((current) => {
      const next = current.filter((methodId) =>
        lane.rows.some((row) => row.methodId === methodId),
      );

      return next.length === current.length ? current : next;
    });
  }, [lane.laneId, scope]);

  const activeSelection = resolveLaneSelection(lane, selection ?? getDefaultLaneSelection(lane));
  const inspectorEntity = getLaneInspectorEntity(lane, activeSelection);

  function handleToggleRuns(methodId: LaneRouteMethodId) {
    setExpandedMethodIds((current) =>
      current.includes(methodId)
        ? current.filter((candidate) => candidate !== methodId)
        : [...current, methodId],
    );
  }

  return (
    <section className="space-y-6">
      <LaneHeader
        laneLabel={lane.label}
        scope={scope}
        status={lane.status}
        statusModifier={lane.statusModifier}
        summary={lane.summary}
      />
      {lane.scopeNote ? <ScopeRouteNote message={lane.scopeNote} /> : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <MethodComparisonTable
          columns={lane.columns}
          expandedMethodIds={expandedMethodIds}
          exploratoryRows={lane.exploratoryRows}
          laneId={lane.laneId}
          onSelectMethod={(entityId) => {
            setSelection({ entityType: "method", entityId });
          }}
          onSelectRun={(entityId) => {
            setSelection({ entityType: "run", entityId });
          }}
          onToggleRuns={handleToggleRuns}
          officialRows={lane.officialRows}
          scope={scope}
          selected={activeSelection}
        />
        <InspectorPanel entity={inspectorEntity} scope={scope} />
      </div>
    </section>
  );
}
