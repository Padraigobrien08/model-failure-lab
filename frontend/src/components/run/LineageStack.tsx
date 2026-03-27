import { Link } from "react-router-dom";

import type { RunRouteLineageEntry } from "@/lib/runRoute";

type LineageStackProps = {
  lineage: RunRouteLineageEntry[];
};

export function LineageStack({ lineage }: LineageStackProps) {
  return (
    <section aria-label="Run lineage" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 pb-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Lineage
        </h2>
        <p className="text-xs text-muted-foreground">Parent to child trace</p>
      </div>

      <div className="space-y-3">
        {lineage.map((entry) => (
          <section key={entry.relation} className="border-l border-border/70 pl-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              {entry.relation}
            </p>
            <div className="mt-2 space-y-2">
              {entry.items.map((item) =>
                item.path ? (
                  <Link
                    key={`${entry.relation}-${item.label}`}
                    className="block text-sm leading-6 text-foreground underline decoration-border underline-offset-4"
                    to={item.path}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <p
                    key={`${entry.relation}-${item.label}`}
                    className={item.mono ? "font-mono text-xs text-foreground" : "text-sm leading-6 text-foreground"}
                  >
                    {item.label}
                  </p>
                ),
              )}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}
