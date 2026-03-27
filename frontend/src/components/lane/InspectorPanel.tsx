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
      className="space-y-4 rounded-[16px] border border-border/70 bg-background/70 p-4 xl:sticky xl:top-24"
      entity={{ ...entity, rawPath: buildRawDebugPath(entity.entityId, scope) }}
      testId="lane-inspector"
    />
  );
}
