import { buttonVariants } from "@/components/ui/button";
import type { RunRouteArtifactGroup } from "@/lib/runRoute";
import { cn } from "@/lib/utils";

type ArtifactSummaryProps = {
  artifacts: RunRouteArtifactGroup[];
};

export function ArtifactSummary({ artifacts }: ArtifactSummaryProps) {
  return (
    <section aria-label="Run artifacts" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Artifacts
        </h2>
        <p className="text-xs text-muted-foreground">Grouped by type</p>
      </div>

      <div className="space-y-3">
        {artifacts.map((group) => (
          <section key={group.label} className="space-y-2.5 border-t border-border/60 pt-2.5 first:border-t-0 first:pt-0">
            <h3 className="text-sm font-semibold text-foreground">{group.label}</h3>
            <div className="flex flex-wrap gap-2">
              {group.items.map((item) => (
                <a
                  key={`${group.label}-${item.label}`}
                  className={cn(
                    buttonVariants({ size: "sm", variant: "ghost" }),
                    "h-auto px-0 py-0 font-medium underline underline-offset-4",
                  )}
                  href={item.path}
                  rel="noreferrer"
                  target="_blank"
                >
                  {item.label}
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}
