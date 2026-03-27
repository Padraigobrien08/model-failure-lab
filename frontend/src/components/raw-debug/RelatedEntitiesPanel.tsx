import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { RawDebugRelatedEntity } from "@/lib/rawDebugRoute";

type RelatedEntitiesPanelProps = {
  entities: RawDebugRelatedEntity[];
};

export function RelatedEntitiesPanel({ entities }: RelatedEntitiesPanelProps) {
  return (
    <aside
      className="space-y-3 border border-border/70 bg-muted/10 p-4"
      data-testid="related-entities"
    >
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Related entities
        </p>
        <p className="text-sm text-muted-foreground">
          Keep tracing without leaving raw mode.
        </p>
      </div>

      <div className="space-y-3">
        {entities.map((entity) => (
          <div
            key={`${entity.entityId}-${entity.relation}`}
            className="space-y-2 border border-border/70 bg-background/70 p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="muted">{entity.entityType}</Badge>
              {entity.scope === "exploratory" ? (
                <Badge tone="exploratory">Exploratory</Badge>
              ) : (
                <Badge tone="muted">Official</Badge>
              )}
            </div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              {entity.relation}
            </p>
            <Link className="text-sm font-medium text-foreground underline-offset-4 hover:underline" to={entity.path}>
              {entity.label}
            </Link>
            <p className="break-all font-mono text-[11px] text-muted-foreground">{entity.entityId}</p>
          </div>
        ))}
      </div>
    </aside>
  );
}
