import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { CardDescription, CardTitle } from "@/components/ui/card";
import type { EvidenceDrawerModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type EvidenceDrawerProps = {
  model: EvidenceDrawerModel;
  onClose: () => void;
  onOpenRunsView: (runId: string) => void;
};

export function EvidenceDrawer({
  model,
  onClose,
  onOpenRunsView,
}: EvidenceDrawerProps) {
  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <CardDescription>Evidence drawer</CardDescription>
          <CardTitle>{model.detail.displayName}</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">
            Quick drillthrough keeps current-page context intact. Move to the full Runs route only
            when you need the larger lineage panel.
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Close
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={model.run.isExploratory ? "exploratory" : "accent"}>
          {model.run.isOfficial ? "Official" : "Exploratory"}
        </Badge>
        <Badge tone="default">{model.run.seedLabel}</Badge>
        <Badge tone="muted">{model.run.verdict}</Badge>
      </div>

      <div className="rounded-[22px] border border-border/80 bg-background/55 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Run
        </p>
        <p className="mt-2 font-mono text-xs leading-6 text-foreground">{model.run.runId}</p>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{model.detail.storyNote}</p>
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Lineage
        </p>
        <div className="space-y-2">
          {model.detail.lineage.map((item) => (
            <div
              key={`${model.run.runId}-${item.label}`}
              className="rounded-[20px] border border-border/70 bg-background/55 px-4 py-3"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                {item.label}
              </p>
              <p className="mt-1 text-sm leading-6 text-foreground">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Summary
        </p>
        <div className="grid gap-3">
          {model.detail.metrics.map((metric) => (
            <div
              key={`${model.run.runId}-${metric.label}`}
              className="rounded-[20px] border border-border/70 bg-background/55 px-4 py-3"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                {metric.label}
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">{metric.value}</p>
              {metric.note ? (
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{metric.note}</p>
              ) : null}
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Artifacts
        </p>
        <div className="space-y-4">
          {model.detail.actionGroups.map((group) => (
            <div
              key={`${model.run.runId}-${group.title}`}
              className="rounded-[20px] border border-border/70 bg-background/55 p-4"
            >
              <p className="text-sm font-semibold text-foreground">{group.title}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {group.actions.map((action) => (
                  <a
                    key={`${model.run.runId}-${group.title}-${action.label}-${action.path}`}
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
      </div>

      <Button className="w-full" onClick={() => onOpenRunsView(model.run.runId)}>
        Open in Runs view
      </Button>
    </div>
  );
}
