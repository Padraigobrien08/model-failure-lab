import { useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";
import { RelatedEntitiesPanel } from "@/components/raw-debug/RelatedEntitiesPanel";
import { RawEntityTabs } from "@/components/raw-debug/RawEntityTabs";
import { ScopeStateNotice } from "@/components/raw-debug/ScopeStateNotice";
import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";
import { buildRawDebugRouteModel } from "@/lib/rawDebugRoute";

export function RawDebugPage() {
  const { entityId } = useParams();
  const { scope } = useTraceScope();
  const rawRoute = buildRawDebugRouteModel(entityId, scope);

  return (
    <section className="space-y-5">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          {rawRoute.question}
        </p>
        <div className="space-y-2">
          {"entityType" in rawRoute ? (
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="muted">{rawRoute.entityType}</Badge>
              {"status" in rawRoute ? <Badge tone={rawRoute.status === "stable" ? "accent" : "muted"}>{formatLabel(rawRoute.status)}</Badge> : null}
              {"scope" in rawRoute ? (
                rawRoute.scope === "exploratory" ? (
                  <Badge tone="exploratory">Exploratory</Badge>
                ) : (
                  <Badge tone="muted">Official</Badge>
                )
              ) : null}
            </div>
          ) : null}
          <h1 className="break-all font-mono text-xl font-semibold tracking-[-0.03em] text-foreground">
            {rawRoute.entityId}
          </h1>
        </div>
      </header>

      {rawRoute.state === "ready" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_17rem]">
          <RawEntityTabs tabs={rawRoute.tabs} />
          <RelatedEntitiesPanel entities={rawRoute.relatedEntities} />
        </div>
      ) : rawRoute.state === "scope-hidden" ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_17rem]">
          <ScopeStateNotice
            state="scope-hidden"
            title={rawRoute.label}
            message={rawRoute.message}
            recoveryPath={rawRoute.recoveryPath}
          />
          <RelatedEntitiesPanel entities={rawRoute.relatedEntities} />
        </div>
      ) : (
        <ScopeStateNotice
          state="missing"
          title="Entity unavailable"
          message={rawRoute.message}
        />
      )}
    </section>
  );
}
