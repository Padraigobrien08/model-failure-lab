import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { formatLabel } from "@/lib/formatters";
import type { MethodRouteInspectorEntity } from "@/lib/methodRoute";
import { cn } from "@/lib/utils";

type InspectorPanelProps = {
  entity: MethodRouteInspectorEntity;
  scope: TraceScope;
};

function getStatusBadgeProps(status: MethodRouteInspectorEntity["status"]) {
  if (status === "stable") {
    return { tone: "accent" as const };
  }

  if (status === "failure") {
    return {
      tone: "default" as const,
      className: "border border-destructive/25 bg-destructive/10 text-destructive",
    };
  }

  return { tone: "default" as const };
}

function withScope(path: string, scope: TraceScope) {
  return `${path}?scope=${scope}`;
}

export function InspectorPanel({ entity, scope }: InspectorPanelProps) {
  return (
    <aside
      className="space-y-4 border-t border-border/70 pt-4 xl:sticky xl:top-24 xl:border-t-0 xl:border-l xl:pl-6 xl:pt-0"
      data-testid="method-inspector"
    >
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Inspector
        </p>
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="muted">{entity.entityType}</Badge>
            <Badge {...getStatusBadgeProps(entity.status)}>{formatLabel(entity.status)}</Badge>
            {entity.scope === "exploratory" ? (
              <Badge tone="exploratory">Exploratory</Badge>
            ) : (
              <Badge tone="muted">Official</Badge>
            )}
          </div>
          <h2 className="text-lg font-semibold tracking-[-0.03em] text-foreground">{entity.label}</h2>
          <p className="text-sm leading-6 text-muted-foreground">{entity.summary}</p>
        </div>
      </div>

      <section className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Evidence
        </p>
        <div className="flex flex-wrap gap-2">
          {entity.evidenceLinks.map((link) => (
            <a
              key={`${entity.entityId}-${link.label}`}
              className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
              href={link.path}
              rel="noreferrer"
              target="_blank"
            >
              {link.label}
            </a>
          ))}
          <Link
            className={cn(buttonVariants({ size: "sm", variant: "default" }))}
            to={withScope(`/debug/raw/${entity.entityId}`, scope)}
          >
            Open raw
          </Link>
        </div>
      </section>

      <section className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Provenance preview
        </p>
        <div className="space-y-2">
          {entity.provenance.map((field) => (
            <div key={`${entity.entityId}-${field.label}`} className="border border-border/70 px-3 py-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                {field.label}
              </p>
              <p
                className={cn(
                  "mt-1 text-sm text-foreground",
                  field.mono ? "break-all font-mono text-xs" : "",
                )}
              >
                {field.value}
              </p>
            </div>
          ))}
        </div>
      </section>
    </aside>
  );
}
