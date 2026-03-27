import type { TraceScope } from "@/app/scope";
import { SharedInspectorPanel } from "@/components/inspector/SharedInspectorPanel";
import type { LaneRouteInspectorEntity } from "@/lib/laneRoute";
import { buildRawDebugPath } from "@/lib/runRoute";

type InspectorPanelProps = {
  entity: LaneRouteInspectorEntity;
  scope: TraceScope;
};

export function InspectorPanel({ entity, scope }: InspectorPanelProps) {
  return (
    <SharedInspectorPanel
      className="space-y-4 border-t border-border/60 pt-4 xl:sticky xl:top-24 xl:border-t-0 xl:border-l xl:pl-5 xl:pt-0"
      entity={{ ...entity, rawPath: buildRawDebugPath(entity.entityId, scope) }}
      testId="lane-inspector"
    />
  );
}
