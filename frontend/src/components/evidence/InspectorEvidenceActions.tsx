import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import type { EvidenceActionGroup, InspectorRouteActionModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type InspectorEvidenceActionsProps = {
  routeActions: InspectorRouteActionModel[];
  actionGroups: EvidenceActionGroup[];
};

export function InspectorEvidenceActions({
  routeActions,
  actionGroups,
}: InspectorEvidenceActionsProps) {
  if (routeActions.length === 0 && actionGroups.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <div className="space-y-2">
        <Badge tone="muted">Evidence actions</Badge>
        <p className="text-sm leading-6 text-muted-foreground">
          Keep the current context on screen, then jump deeper only when you need the larger route.
        </p>
      </div>

      {routeActions.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {routeActions.map((action, index) => (
            <Link
              key={`${action.label}-${action.href}`}
              to={action.href}
              className={cn(
                buttonVariants({
                  variant: index === 0 ? "default" : "outline",
                  size: "sm",
                }),
              )}
            >
              {action.label}
            </Link>
          ))}
        </div>
      ) : null}

      <div className="space-y-3">
        {actionGroups.map((group) => (
          <div
            key={group.title}
            className="rounded-[16px] border border-border/70 bg-background/55 p-4"
          >
            <p className="text-sm font-semibold text-foreground">{group.title}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {group.actions.map((action) => (
                <a
                  key={`${group.title}-${action.label}-${action.path}`}
                  href={action.path}
                  target="_blank"
                  rel="noreferrer"
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                >
                  {action.label}
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
