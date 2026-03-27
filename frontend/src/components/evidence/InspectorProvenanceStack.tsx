import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { InspectorFieldModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type InspectorProvenanceStackProps = {
  title: string;
  description?: string;
  items: InspectorFieldModel[];
};

export function InspectorProvenanceStack({
  title,
  description,
  items,
}: InspectorProvenanceStackProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3">
      <div className="space-y-2">
        <Badge tone="muted">{title}</Badge>
        {description ? (
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        {items.map((item) => {
          const body = (
            <div
              className={cn(
                "rounded-[16px] border border-border/70 bg-background/55 px-4 py-3",
                item.href ? "transition-colors hover:border-primary/25" : "",
              )}
            >
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {item.label}
              </p>
              <p
                className={cn(
                  "mt-1 text-sm leading-6 text-foreground",
                  item.mono ? "break-all font-mono text-xs" : "",
                )}
              >
                {item.value}
              </p>
            </div>
          );

          return item.href ? (
            <Link
              key={`${title}-${item.label}-${item.value}`}
              to={item.href}
              className="block"
            >
              {body}
            </Link>
          ) : (
            <div key={`${title}-${item.label}-${item.value}`}>{body}</div>
          );
        })}
      </div>
    </section>
  );
}
