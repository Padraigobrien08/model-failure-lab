import { RunCard } from "@/components/runs/RunCard";
import { Badge } from "@/components/ui/badge";
import type { RunLaneModel } from "@/lib/manifest/types";

type RunGroupSectionProps = {
  lane: RunLaneModel;
  activeRunId: string | null;
  onSelectRun: (runId: string) => void;
};

export function RunGroupSection({
  lane,
  activeRunId,
  onSelectRun,
}: RunGroupSectionProps) {
  return (
    <section className="space-y-5 rounded-[28px] border border-border/70 bg-background/45 p-5">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={lane.isExploratoryLane ? "exploratory" : "accent"}>{lane.laneLabel}</Badge>
          {lane.isExploratoryLane ? <Badge tone="exploratory">Optional scope</Badge> : null}
        </div>
        <h3 className="text-[1.9rem] font-semibold tracking-[-0.05em] text-foreground">
          {lane.laneLabel}
        </h3>
        <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{lane.description}</p>
      </header>

      <div className="space-y-5">
        {lane.seedGroups.map((seedGroup) => (
          <div key={`${lane.laneKey}-${seedGroup.seedLabel}`} className="space-y-3">
            <div className="flex items-center gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {seedGroup.seedLabel}
              </p>
              <div className="h-px flex-1 bg-border/70" />
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              {seedGroup.runs.map((run) => (
                <RunCard
                  key={run.runId}
                  run={run}
                  isSelected={activeRunId === run.runId}
                  onSelectRun={onSelectRun}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
