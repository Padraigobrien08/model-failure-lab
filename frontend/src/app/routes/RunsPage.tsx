import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { RunDetailPanel } from "@/components/runs/RunDetailPanel";
import { RunGroupSection } from "@/components/runs/RunGroupSection";
import { useAppRouteContext } from "@/app/router";
import { buildRunDetailModel, buildRunLaneModels } from "@/lib/manifest/selectors";

export function RunsPage() {
  const {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selectedRunId,
    setSelectedRunId,
    openEvidenceDrawer,
  } = useAppRouteContext();

  if (isLoading || isFinalRobustnessBundleLoading) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Runs</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading run-level drillthrough.
        </h2>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Runs</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The run explorer could not load its saved evidence.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Missing saved run payload."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const lanes = buildRunLaneModels(index, finalRobustnessBundle, includeExploratory);
  const fallbackRunId = lanes[0]?.seedGroups[0]?.runs[0]?.runId ?? null;
  const activeRunId = selectedRunId ?? fallbackRunId;
  const detail = buildRunDetailModel(index, finalRobustnessBundle, activeRunId);

  return (
    <section className="space-y-8">
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Runs</Badge>
          {activeRunId ? <Badge tone="default">Focused run: {activeRunId}</Badge> : null}
        </div>
        <div className="space-y-3">
          <h2 className="text-[2.75rem] font-semibold tracking-[-0.06em] text-foreground">
            Grouped runs by method lane, then by seed.
          </h2>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Start with method families, move into individual saved runs, then read the selected
            lineage, summary, and artifact stack without losing the official-versus-exploratory
            boundary.
          </p>
        </div>
      </header>

      <ScopeStateBanner
        includeExploratory={includeExploratory}
        onChange={setIncludeExploratory}
      />

      <div className="space-y-6">
        {lanes.map((lane) => (
          <RunGroupSection
            key={lane.laneKey}
            lane={lane}
            activeRunId={activeRunId}
            onSelectRun={setSelectedRunId}
          />
        ))}
      </div>

      {detail ? (
        <RunDetailPanel
          detail={detail}
          onOpenDrawer={() => openEvidenceDrawer(detail.runId)}
        />
      ) : null}
    </section>
  );
}
