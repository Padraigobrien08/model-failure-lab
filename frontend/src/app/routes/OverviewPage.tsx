import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  formatComparisonMode,
  formatLabel,
  formatMetric,
  formatSignedMetric,
} from "@/lib/formatters";
import { buildOverviewSnapshot, buildVerdictWorkspaceModel } from "@/lib/manifest/selectors";
import { cn } from "@/lib/utils";

export function OverviewPage() {
  const {
    index,
    isLoading,
    error,
    includeExploratory,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selectedLane,
    setSelectedLane,
    setSelectedMethod,
    openEvidenceDrawer,
  } = useAppRouteContext();

  if (isLoading || isFinalRobustnessBundleLoading) {
    return (
      <section className="space-y-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-primary">
            Loading verdict lineage
          </p>
          <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
            Preparing the verdict-first workbench.
          </h2>
        </header>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-destructive">
            Verdict trace unavailable
          </p>
          <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
            The workbench could not load the saved verdict package.
          </h2>
        </header>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Missing saved verdict payload."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const snapshot = buildOverviewSnapshot(index, includeExploratory);
  const workspace = buildVerdictWorkspaceModel(index, finalRobustnessBundle, includeExploratory);
  const activeLaneKey = selectedLane ?? workspace.dominantLaneKey;
  const activeLane =
    workspace.lanes.find((lane) => lane.key === activeLaneKey) ??
    workspace.lanes.find((lane) => lane.dominant) ??
    workspace.lanes[0];

  function handleTraceMethod(methodName: string, runId: string | null | undefined) {
    setSelectedLane(activeLane.key);
    setSelectedMethod(methodName);
    if (runId) {
      openEvidenceDrawer(runId);
    }
  }

  return (
    <section className="space-y-8">
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Verdicts</Badge>
            {includeExploratory ? (
              <Badge tone="exploratory">Exploratory scope active</Badge>
            ) : (
              <Badge tone="muted">Official-first</Badge>
            )}
            <Badge tone="default">{formatLabel(workspace.finalVerdict)}</Badge>
          </>
        }
        title="Verdict traceability starts with the final decision."
        description="Read the final verdict, see which lane is carrying it, and move straight into the supporting method or artifact path without passing through summary-heavy dashboard chrome."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Final verdict
              </p>
              <p className="mt-2 text-lg font-semibold text-foreground">
                {formatLabel(workspace.finalVerdict)}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Dominant lane
              </p>
              <p className="mt-2 text-lg font-semibold text-foreground">
                {formatLabel(workspace.dominantLaneKey)}
              </p>
            </div>
          </div>
        }
      />

      <WorkbenchSection
        eyebrow="Decision"
        title="Final verdict and first evidence path"
        description="The official closeout still lands on the same conclusion: calibration is stable, robustness is still mixed, and the underlying report package remains the contract of record."
        aside={
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
              Supporting report
            </p>
            <p className="text-sm text-foreground">{workspace.supportingReportScope}</p>
          </div>
        }
      >
        <div className="flex flex-wrap gap-3">
          <Link to={`/lanes?lane=${workspace.dominantLaneKey}`} className={cn(buttonVariants({ variant: "default" }))}>
            Trace Evidence
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
          {workspace.primaryActions.map((action) => (
            <a
              key={`${action.label}-${action.path}`}
              href={action.path}
              target="_blank"
              rel="noreferrer"
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              {action.label}
            </a>
          ))}
        </div>
      </WorkbenchSection>

      <WorkbenchSection
        eyebrow="Supporting lanes"
        title="Lane stack"
        description="Lanes stay visible immediately. The dominant lane opens by default, and every method row keeps a direct path into the supporting evidence context."
      >
        <div className="space-y-4">
          {workspace.lanes.map((lane) => {
            const isActive = lane.key === activeLane.key;

            return (
              <section
                key={lane.key}
                className={cn(
                  "rounded-[18px] border border-border/70 bg-card/45",
                  isActive ? "border-primary/25 bg-primary/5" : undefined,
                )}
              >
                <button
                  type="button"
                  className="flex w-full flex-wrap items-start justify-between gap-4 px-4 py-4 text-left"
                  onClick={() => setSelectedLane(lane.key)}
                >
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={lane.dominant ? "accent" : "default"}>{lane.label}</Badge>
                      <Badge tone={lane.dominant ? "accent" : "muted"}>
                        {formatLabel(lane.verdict)}
                      </Badge>
                    </div>
                    <h3 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
                      {lane.description}
                    </h3>
                    <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                      {lane.summary}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-primary">
                    {isActive ? "Expanded" : "Expand"}
                  </span>
                </button>

                {isActive ? (
                  <div className="space-y-3 border-t border-border/70 px-4 py-4">
                    {lane.items.map((item) => (
                      <div
                        key={`${lane.key}-${item.methodName}`}
                        className={cn(
                          "rounded-[16px] border border-border/70 bg-background/55 px-4 py-4",
                          item.isExploratory ? "border-dashed" : undefined,
                        )}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-4">
                          <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge tone={item.isExploratory ? "exploratory" : "default"}>
                                {item.displayName}
                              </Badge>
                              <Badge tone="muted">{formatComparisonMode(item.comparisonMode)}</Badge>
                              <Badge tone="default">{formatLabel(item.verdict)}</Badge>
                            </div>
                            <p className="text-sm leading-6 text-muted-foreground">
                              {item.storyNote}
                            </p>
                          </div>
                          <div className="space-y-2 text-right">
                            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                              {lane.sourceDomain === "calibration" ? "Calibration shift" : "Lane metric"}
                            </p>
                            <p className="text-lg font-semibold text-foreground">
                              {lane.sourceDomain === "calibration"
                                ? `ECE ${formatSignedMetric(item.eceMean)} / Brier ${formatSignedMetric(item.brierMean)}`
                                : item.comparisonMode === "baseline_metric"
                                  ? formatMetric(item.mean)
                                  : formatSignedMetric(item.mean)}
                            </p>
                          </div>
                        </div>

                        <div className="mt-4 flex flex-wrap gap-3">
                          <button
                            type="button"
                            className={cn(buttonVariants({ variant: "default", size: "sm" }))}
                            onClick={() =>
                              handleTraceMethod(item.methodName, item.representativeRunId)
                            }
                          >
                            Trace Evidence
                          </button>
                          <Link
                            to={`/lanes?lane=${lane.key}&method=${item.methodName}`}
                            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                            onClick={() => setSelectedMethod(item.methodName)}
                          >
                            Open lane workspace
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </section>
            );
          })}
        </div>
      </WorkbenchSection>

      <details className="rounded-[20px] border border-border/70 bg-background/55 px-4 py-4">
        <summary className="cursor-pointer text-sm font-semibold text-foreground">
          Supporting narrative and reopen conditions
        </summary>
        <div className="mt-4 space-y-3 text-sm leading-6 text-muted-foreground">
          {workspace.summaryBullets.map((bullet) => (
            <p key={bullet}>{bullet}</p>
          ))}
          {workspace.recommendationReason ? <p>{workspace.recommendationReason}</p> : null}
          {workspace.nextStep ? <p className="text-foreground">{workspace.nextStep}</p> : null}
          {snapshot.reopenConditions.length > 0 ? (
            <ul className="space-y-2">
              {snapshot.reopenConditions.map((condition) => (
                <li
                  key={condition}
                  className="rounded-[14px] border border-border/70 bg-card/45 px-3 py-3 text-foreground"
                >
                  {condition}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </details>
    </section>
  );
}
