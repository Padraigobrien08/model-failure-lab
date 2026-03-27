import { Link } from "react-router-dom";

import type { TraceScope } from "@/app/scope";
import type { MethodRouteLineage } from "@/lib/methodRoute";

type LineageChainProps = {
  lineage: MethodRouteLineage;
  scope: TraceScope;
};

function withScope(path: string, scope: TraceScope) {
  return `${path}?scope=${scope}`;
}

export function LineageChain({ lineage, scope }: LineageChainProps) {
  return (
    <section aria-label="Method lineage" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 pb-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Lineage
        </h2>
        <p className="text-xs text-muted-foreground">Parent to child trace</p>
      </div>

      <div className="space-y-4 lg:flex lg:items-start lg:gap-4 lg:space-y-0">
        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Parent
          </p>
          <Link
            className="block text-sm leading-6 text-foreground underline decoration-border underline-offset-4"
            to={withScope(lineage.parentPath, scope)}
          >
            {lineage.parentLabel}
          </Link>
        </div>

        <div aria-hidden="true" className="hidden pt-6 text-muted-foreground lg:block">
          →
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Current method
          </p>
          <p className="text-sm font-medium text-foreground">{lineage.currentLabel}</p>
        </div>

        <div aria-hidden="true" className="hidden pt-6 text-muted-foreground lg:block">
          →
        </div>

        <div className="min-w-0 flex-[1.2] space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Child runs
          </p>
          <div className="flex flex-wrap gap-x-4 gap-y-2">
            {lineage.childRuns.map((run) => (
              <Link
                key={run.label}
                className="text-sm leading-6 text-foreground underline decoration-border underline-offset-4"
                to={withScope(run.path, scope)}
              >
                {run.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
