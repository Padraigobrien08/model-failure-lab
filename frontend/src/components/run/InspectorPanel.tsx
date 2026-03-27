import { SharedInspectorPanel } from "@/components/inspector/SharedInspectorPanel";
import type { RunRouteInspectorEntity } from "@/lib/runRoute";

type InspectorPanelProps = {
  entity: RunRouteInspectorEntity;
};

export function InspectorPanel({ entity }: InspectorPanelProps) {
  return (
    <SharedInspectorPanel
      className="space-y-4 border-t border-border/60 pt-4 xl:sticky xl:top-24 xl:border-t-0 xl:border-l xl:pl-5 xl:pt-0"
      entity={entity}
      testId="run-inspector"
    />
  );
}
