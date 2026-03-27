import { buttonVariants } from "@/components/ui/button";
import type { RunRouteArtifactGroup } from "@/lib/runRoute";
import { cn } from "@/lib/utils";

type ArtifactSummaryProps = {
  artifacts: RunRouteArtifactGroup[];
};

export function ArtifactSummary({ artifacts }: ArtifactSummaryProps) {
  return (
    <section aria-label="Run artifacts" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 pb-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Artifacts
        </h2>
        <p className="text-xs text-muted-foreground">Grouped by type</p>
      </div>

      <div className="space-y-4">
        {artifacts.map((group) => (
          <section key={group.label} className="space-y-3 border-l border-border/70 pl-4">
            <h3 className="text-sm font-semibold text-foreground">{group.label}</h3>
            <div className="flex flex-wrap gap-2">
              {group.items.map((item) => (
                <a
                  key={`${group.label}-${item.label}`}
                  className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
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
