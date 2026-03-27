import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { formatLabel } from "@/lib/formatters";
import type {
  LaneRouteEvidenceLink,
  LaneRouteProvenanceField,
  LaneRouteRowScope,
  LaneRouteStatus,
} from "@/lib/laneRoute";
import { cn } from "@/lib/utils";

export type SharedInspectorEntity = {
  entityId: string;
  entityType: string;
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  summary?: string;
  evidenceLinks: LaneRouteEvidenceLink[];
  provenance: LaneRouteProvenanceField[];
  rawPath: string;
};

type SharedInspectorPanelProps = {
  entity: SharedInspectorEntity | null;
  className?: string;
  testId?: string;
  placeholderTitle?: string;
  placeholderMessage?: string;
};

function getStatusBadgeProps(status: LaneRouteStatus) {
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

export function SharedInspectorPanel({
  entity,
  className,
  testId,
  placeholderTitle = "Inspector",
  placeholderMessage = "Select a method or run to inspect its evidence and provenance.",
}: SharedInspectorPanelProps) {
  return (
    <aside className={cn("space-y-4", className)} data-testid={testId}>
      <div className="space-y-1.5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Inspector
        </p>
        {entity ? (
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="muted">{entity.entityType}</Badge>
              <Badge {...getStatusBadgeProps(entity.status)}>{formatLabel(entity.status)}</Badge>
              {entity.scope === "exploratory" ? (
                <Badge tone="exploratory">Exploratory</Badge>
              ) : (
                <Badge tone="muted">Official</Badge>
              )}
            </div>
            <h2 className="text-base font-semibold tracking-[-0.03em] text-foreground sm:text-lg">
              {entity.label}
            </h2>
            {entity.summary ? (
              <p className="text-sm leading-5 text-muted-foreground">{entity.summary}</p>
            ) : null}
          </div>
        ) : (
          <div className="space-y-1">
            <h2 className="text-base font-semibold tracking-[-0.03em] text-foreground sm:text-lg">
              {placeholderTitle}
            </h2>
            <p className="text-sm leading-5 text-muted-foreground">{placeholderMessage}</p>
          </div>
        )}
      </div>

      <section className="space-y-2.5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Evidence
        </p>
        {entity ? (
          <div className="space-y-1.5">
            {entity.evidenceLinks.map((link) => (
              <a
                key={`${entity.entityId}-${link.label}`}
                className={cn(
                  buttonVariants({ size: "sm", variant: "ghost" }),
                  "h-auto justify-start px-0 py-0 font-medium underline underline-offset-4",
                )}
                href={link.path}
                rel="noreferrer"
                target="_blank"
              >
                {link.label}
              </a>
            ))}
            <Link
              className={cn(
                buttonVariants({ size: "sm", variant: "ghost" }),
                "h-auto justify-start px-0 py-0 font-medium underline underline-offset-4",
              )}
              to={entity.rawPath}
            >
              Open raw
            </Link>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No entity selected yet.</p>
        )}
      </section>

      <section className="space-y-2.5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Provenance preview
        </p>
        {entity ? (
          <dl className="space-y-0">
            {entity.provenance.map((field) => (
              <div
                key={`${entity.entityId}-${field.label}`}
                className="border-t border-border/60 py-2 first:border-t-0 first:pt-0"
              >
                <dt className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  {field.label}
                </dt>
                <dd
                  className={cn(
                    "mt-1 text-sm text-foreground",
                    field.mono ? "break-all font-mono text-xs" : "",
                  )}
                >
                  {field.value}
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">Select an entity to see its provenance fields.</p>
        )}
      </section>
    </aside>
  );
}
