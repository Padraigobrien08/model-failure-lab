import { useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { LaneHeader } from "@/components/lane/LaneHeader";
import { MethodComparisonTable } from "@/components/lane/MethodComparisonTable";
import { buildLaneRouteModel } from "@/lib/laneRoute";

export function LanePage() {
  const { laneId } = useParams();
  const { scope } = useTraceScope();
  const lane = buildLaneRouteModel(laneId, scope);

  return (
    <section className="space-y-6">
      <LaneHeader
        laneLabel={lane.label}
        scope={scope}
        status={lane.status}
        summary={lane.summary}
      />

      <MethodComparisonTable
        columns={lane.columns}
        laneId={lane.laneId}
        rows={lane.rows}
        scope={scope}
      />
    </section>
  );
}
