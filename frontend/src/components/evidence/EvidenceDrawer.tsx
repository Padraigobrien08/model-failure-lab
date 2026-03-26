import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { InspectorModel } from "@/lib/manifest/types";
import { ArtifactPreviewPanel } from "@/components/evidence/ArtifactPreviewPanel";
import { InspectorEvidenceActions } from "@/components/evidence/InspectorEvidenceActions";
import { InspectorProvenanceStack } from "@/components/evidence/InspectorProvenanceStack";

type EvidenceDrawerProps = {
  model: InspectorModel;
  onClose?: () => void;
};

export function EvidenceDrawer({ model, onClose }: EvidenceDrawerProps) {
  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Live inspector
          </p>
          <h3 className="text-[1.6rem] font-semibold tracking-[-0.04em] text-foreground">
            {model.title}
          </h3>
          <p className="font-mono text-xs leading-6 text-muted-foreground">{model.subtitle}</p>
          {model.description ? (
            <p className="text-sm leading-6 text-muted-foreground">{model.description}</p>
          ) : null}
        </div>
        {onClose ? (
          <Button variant="ghost" size="sm" onClick={onClose}>
            Clear focus
          </Button>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {model.badges.map((badge) => (
          <Badge key={`${badge.label}-${badge.tone}`} tone={badge.tone}>
            {badge.label}
          </Badge>
        ))}
      </div>

      {model.warning ? (
        <div className="rounded-[16px] border border-dashed border-amber-700/35 bg-amber-950/20 px-4 py-3 text-sm leading-6 text-amber-100">
          {model.warning}
        </div>
      ) : null}

      <InspectorProvenanceStack
        title="Lineage"
        description="What produced the currently selected object and where to climb back up the chain."
        items={model.lineage}
      />

      <InspectorProvenanceStack
        title="Provenance"
        description="Manifest truth for scope, visibility, and source-path state."
        items={model.provenance}
      />

      <InspectorEvidenceActions
        routeActions={model.routeActions}
        actionGroups={model.actionGroups}
      />

      <ArtifactPreviewPanel preview={model.preview} />
    </div>
  );
}
