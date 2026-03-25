import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
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
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Runs</Badge>
            {activeRunId ? <Badge tone="default">Focused run: {activeRunId}</Badge> : null}
          </>
        }
        title="Grouped runs by method lane, then by seed."
        description="Start with method families, move into individual saved runs, then read the selected lineage, summary, and artifact stack without losing the official-versus-exploratory boundary."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active run
              </p>
              <p className="mt-1 break-all text-foreground">
                {activeRunId ?? "No selected run"}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Scope
              </p>
              <p className="mt-1 text-foreground">
                {includeExploratory ? "Official + exploratory" : "Official only"}
              </p>
            </div>
          </div>
        }
      />

      <ScopeStateBanner
        includeExploratory={includeExploratory}
        onChange={setIncludeExploratory}
      />

      <WorkbenchSection
        eyebrow="Run workspace"
        title="Lane inventory"
        description="Scan the saved run families first, then open the balanced lineage → summary → artifacts panel for the currently selected run."
      >
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
      </WorkbenchSection>

      {detail ? (
        <RunDetailPanel
          detail={detail}
          onOpenDrawer={() => openEvidenceDrawer(detail.runId)}
        />
      ) : null}
    </section>
  );
}
