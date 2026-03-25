import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { RunDetailModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type RunDetailPanelProps = {
  detail: RunDetailModel;
  onOpenDrawer?: () => void;
};

export function RunDetailPanel({ detail, onOpenDrawer }: RunDetailPanelProps) {
  return (
    <Card
      className={cn(
        "rounded-[18px] bg-background/55",
        detail.isExploratory ? "border-dashed" : "",
      )}
    >
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Run detail</Badge>
          <Badge tone={detail.isExploratory ? "exploratory" : "default"}>
            {detail.isOfficial ? "Official" : "Exploratory"}
          </Badge>
          <Badge tone="muted">{detail.verdict}</Badge>
          <Badge tone="default">{detail.seedLabel}</Badge>
        </div>
        <div className="space-y-2">
          <CardDescription>Lineage → summary → artifacts</CardDescription>
          <CardTitle className="text-[2rem]">{detail.displayName}</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">{detail.storyNote ?? detail.summaryLabel}</p>
        </div>
      </CardHeader>
      <CardContent className="space-y-8">
        <section className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Lineage
              </p>
              <h4 className="mt-1 text-lg font-semibold text-foreground">
                Provenance before raw artifacts
              </h4>
            </div>
            {onOpenDrawer ? (
              <Button variant="outline" size="sm" onClick={onOpenDrawer}>
                Open evidence drawer
              </Button>
            ) : null}
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {detail.lineage.map((item) => (
              <div
                key={`${detail.runId}-${item.label}`}
                className="rounded-[16px] border border-border/70 bg-card/45 px-4 py-4"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {item.label}
                </p>
                <p className="mt-2 text-sm leading-6 text-foreground">{item.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Summary
            </p>
            <h4 className="mt-1 text-lg font-semibold text-foreground">
              What changed for this run
            </h4>
          </div>

          <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
            {detail.metrics.map((metric) => (
              <div
                key={`${detail.runId}-${metric.label}`}
                className="rounded-[16px] border border-border/70 bg-card/45 px-4 py-4"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {metric.label}
                </p>
                <p className="mt-2 text-xl font-semibold text-foreground">{metric.value}</p>
                {metric.note ? (
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{metric.note}</p>
                ) : null}
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Artifacts
            </p>
            <h4 className="mt-1 text-lg font-semibold text-foreground">
              Saved evidence, linked directly from the manifest
            </h4>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {detail.actionGroups.map((group) => (
              <div
                key={`${detail.runId}-${group.title}`}
                className="rounded-[16px] border border-border/70 bg-card/45 p-4"
              >
                <p className="text-sm font-semibold text-foreground">{group.title}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {group.actions.map((action) => (
                    <a
                      key={`${detail.runId}-${group.title}-${action.label}-${action.path}`}
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
      </CardContent>
    </Card>
  );
}
