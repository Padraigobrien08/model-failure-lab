import { type ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  createArtifactRegressionPack,
  evolveArtifactDataset,
  loadArtifactDatasetVersions,
} from "@/lib/artifacts/load";
import {
  buildComparisonDetailSearchParams,
} from "@/lib/artifacts/detailRouteState";
import type {
  ArtifactDatasetEvolutionResponse,
  ArtifactGovernanceRecommendation,
  ArtifactSignalHistoryContext,
  ArtifactDatasetVersionsResponse,
  ArtifactRegressionPackResponse,
  ComparisonSignal,
} from "@/lib/artifacts/types";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type AsyncState<T> =
  | { status: "idle"; value: null; message: null }
  | { status: "loading"; value: null; message: null }
  | { status: "ready"; value: T; message: null }
  | { status: "error"; value: null; message: string };

type SignalDatasetAutomationPanelProps = {
  comparisonId: string;
  dataset: string | null;
  signal: ComparisonSignal;
  driverFilter?: string | null;
  recommendation?: ArtifactGovernanceRecommendation | null;
  historyContext?: ArtifactSignalHistoryContext | null;
  returnState?: unknown;
  autoLoadVersions?: boolean;
  title?: string;
  onVersionsStateChange?: (state: AsyncState<ArtifactDatasetVersionsResponse>) => void;
};

function normalizeSegment(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function buildSuggestedFamilyId(
  dataset: string | null,
  signal: ComparisonSignal,
  driverFilter?: string | null,
): string {
  const datasetSegment = normalizeSegment(dataset ?? "comparison") || "comparison";
  const filteredDriver =
    (typeof driverFilter === "string" && driverFilter.trim().length > 0
      ? driverFilter
      : signal.topDrivers.find((driver) => driver.direction === "regression")?.failureType) ??
    "general";
  const driverSegment = normalizeSegment(filteredDriver) || "general";
  return `regression-${datasetSegment}-${driverSegment}`;
}

function renderPreviewLink(
  comparisonId: string,
  caseId: string | null,
  label: string,
  returnState: unknown,
) {
  const comparisonSearch = caseId
    ? buildComparisonDetailSearchParams(new URLSearchParams(), {
        section: "transitions",
        caseId,
      }).toString()
    : "";
  return (
    <Link
      key={`${comparisonId}:${caseId}:${label}`}
      className="inline-flex rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground no-underline transition-colors hover:bg-background"
      state={returnState}
      to={{
        pathname: `/comparisons/${encodeURIComponent(comparisonId)}`,
        search: comparisonSearch.length > 0 ? `?${comparisonSearch}` : "",
      }}
    >
      {label}
    </Link>
  );
}

function formatLifecycleLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function formatPriorityBand(value: string): string {
  return value.replace(/_/g, " ");
}

type SurfaceSectionProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
};

function SurfaceSection({
  eyebrow,
  title,
  description,
  children,
}: SurfaceSectionProps) {
  return (
    <section className="space-y-3">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {eyebrow}
        </p>
        <div className="space-y-1">
          <h3 className="text-lg font-semibold tracking-[-0.02em] text-foreground">{title}</h3>
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

export function SignalDatasetAutomationPanel({
  comparisonId,
  dataset,
  signal,
  driverFilter = null,
  recommendation = null,
  historyContext = null,
  returnState = null,
  autoLoadVersions = false,
  title = "Regression pack automation",
  onVersionsStateChange = undefined,
}: SignalDatasetAutomationPanelProps) {
  const suggestedFamilyId = buildSuggestedFamilyId(dataset, signal, driverFilter);
  const targetFamilyId = recommendation?.matchedFamily.familyId ?? suggestedFamilyId;
  const [generationState, setGenerationState] = useState<AsyncState<ArtifactRegressionPackResponse>>(
    {
      status: "idle",
      value: null,
      message: null,
    },
  );
  const [evolutionState, setEvolutionState] = useState<AsyncState<ArtifactDatasetEvolutionResponse>>(
    {
      status: "idle",
      value: null,
      message: null,
    },
  );
  const [versionsState, setVersionsState] = useState<AsyncState<ArtifactDatasetVersionsResponse>>({
    status: "idle",
    value: null,
    message: null,
  });

  const loadVersions = () => {
    setVersionsState({ status: "loading", value: null, message: null });
    void loadArtifactDatasetVersions(targetFamilyId)
      .then((response) => {
        setVersionsState({ status: "ready", value: response, message: null });
      })
      .catch((error: unknown) => {
        setVersionsState({
          status: "error",
          value: null,
          message: error instanceof Error ? error.message : "Failed to load dataset versions",
        });
      });
  };

  useEffect(() => {
    if (!autoLoadVersions) {
      setVersionsState({ status: "idle", value: null, message: null });
      return;
    }
    loadVersions();
  }, [autoLoadVersions, targetFamilyId]);

  useEffect(() => {
    onVersionsStateChange?.(versionsState);
  }, [onVersionsStateChange, versionsState]);

  const activePreview =
    evolutionState.status === "ready"
      ? evolutionState.value
      : generationState.status === "ready"
        ? generationState.value
        : null;
  const activeHistoryContext = historyContext ?? recommendation?.historyContext ?? null;
  const activeClusterContext =
    recommendation?.clusterContext ??
    activeHistoryContext?.recurringClusters ??
    [];
  const activeEscalation = recommendation?.escalation ?? null;
  const activeLifecycleRecommendation = recommendation?.lifecycleRecommendation ?? null;
  const loadedFamilyHealth =
    versionsState.status === "ready" ? versionsState.value.history.datasetHealth : null;
  const lifecycleActions =
    versionsState.status === "ready" ? versionsState.value.lifecycleActions : [];
  const activeLifecycleAction =
    lifecycleActions.length > 0 ? lifecycleActions[lifecycleActions.length - 1] : null;
  const familyHealth = loadedFamilyHealth ?? activeHistoryContext?.familyHealth ?? null;
  const portfolioItem =
    versionsState.status === "ready" ? versionsState.value.portfolioItem : null;
  const portfolioPlans =
    versionsState.status === "ready" ? versionsState.value.portfolioPlans : [];

  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Dataset evolution</Badge>
          <Badge tone="muted">{signal.verdict}</Badge>
          <Badge tone="muted">{targetFamilyId}</Badge>
          {recommendation ? (
            <Badge tone={recommendation.action === "ignore" ? "default" : "accent"}>
              recommend {recommendation.action}
            </Badge>
          ) : null}
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          Turn this comparison signal into a draft regression pack or the next immutable dataset
          version, then keep the same evidence drillthrough available from the preview.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {recommendation || activeLifecycleRecommendation ? (
          <SurfaceSection
            eyebrow="1"
            title="Recommended next move"
            description="Keep the suggested dataset action, escalation pressure, and lifecycle guardrails together before mutating the family."
          >
            {recommendation ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Recommendation
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={recommendation.action === "ignore" ? "default" : "accent"}>
                    {recommendation.action}
                  </Badge>
                  <Badge tone="muted">{recommendation.policyRule}</Badge>
                  <Badge tone="muted">
                    {recommendation.matchedFamily.versionCount} versions
                  </Badge>
                  <Badge tone="muted">
                    {recommendation.matchedFamily.projectedCaseCount} projected cases
                  </Badge>
                  {activeEscalation ? (
                    <Badge tone={activeEscalation.status === "critical" ? "default" : "accent"}>
                      {activeEscalation.status}
                    </Badge>
                  ) : null}
                  {activeLifecycleRecommendation ? (
                    <Badge tone="muted">
                      {formatLifecycleLabel(activeLifecycleRecommendation.action)}
                    </Badge>
                  ) : null}
                </div>
                <p className="text-sm text-muted-foreground">{recommendation.rationale}</p>
                <p className="text-xs text-muted-foreground">
                  Family {recommendation.matchedFamily.familyId} · duplicates{" "}
                  {recommendation.matchedFamily.duplicateCaseCount}/
                  {recommendation.selectedCaseCount} · cap{" "}
                  {recommendation.matchedFamily.familyCaseCap ?? "none"}
                </p>
                {activeEscalation ? (
                  <p className="text-xs text-muted-foreground">
                    Escalation {activeEscalation.status} · score{" "}
                    {activeEscalation.score.toFixed(3)} · {activeEscalation.reason}
                  </p>
                ) : null}
                {recommendation.previewCases.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {recommendation.previewCases.slice(0, 4).map((entry) =>
                      renderPreviewLink(
                        entry.sourceReportId,
                        entry.sourceCaseId,
                        entry.promptId,
                        returnState,
                      ),
                    )}
                  </div>
                ) : null}
              </div>
            ) : null}

            {activeLifecycleRecommendation ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Lifecycle recommendation
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="accent">Lifecycle recommendation</Badge>
                  <Badge tone="muted">
                    {formatLifecycleLabel(activeLifecycleRecommendation.action)}
                  </Badge>
                  <Badge tone="muted">
                    {formatLifecycleLabel(activeLifecycleRecommendation.healthCondition)}
                  </Badge>
                  {activeLifecycleRecommendation.projectedCaseCount != null ? (
                    <Badge tone="muted">
                      {activeLifecycleRecommendation.projectedCaseCount} projected cases
                    </Badge>
                  ) : null}
                </div>
                <p className="text-sm text-muted-foreground">
                  {activeLifecycleRecommendation.rationale}
                </p>
                <p className="text-xs text-muted-foreground">
                  Source dataset {activeLifecycleRecommendation.sourceDatasetId ?? "n/a"} · Driver{" "}
                  {activeLifecycleRecommendation.primaryFailureType ?? "n/a"} · Versions{" "}
                  {activeLifecycleRecommendation.versionCount ?? 0}
                </p>
                {activeLifecycleRecommendation.targetFamilyId ? (
                  <p className="text-xs text-muted-foreground">
                    Merge target: {activeLifecycleRecommendation.targetFamilyId}
                  </p>
                ) : null}
              </div>
            ) : null}
          </SurfaceSection>
        ) : null}

        {activeHistoryContext || activeClusterContext.length > 0 || familyHealth ? (
          <SurfaceSection
            eyebrow="2"
            title="Family state"
            description="Read the recent trend, recurring failures, linked clusters, and active family health before taking action."
          >
            {activeHistoryContext ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Family history context
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="muted">{activeHistoryContext.scopeKind}</Badge>
                  <Badge tone="muted">{activeHistoryContext.scopeValue}</Badge>
                  <Badge tone="muted">
                    {activeHistoryContext.recentRegressionCount}/
                    {activeHistoryContext.recentComparisonCount} recent regressions
                  </Badge>
                  <Badge tone="muted">
                    {activeHistoryContext.comparisonTrend.label} trend
                  </Badge>
                  <Badge tone="muted">
                    {activeHistoryContext.comparisonTrend.volatilityLabel} volatility
                  </Badge>
                  {activeHistoryContext.candidateRunTrend ? (
                    <Badge tone="muted">
                      candidate {activeHistoryContext.candidateRunTrend.label}
                    </Badge>
                  ) : null}
                </div>
                {activeHistoryContext.recurringFailures.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {activeHistoryContext.recurringFailures.map((pattern) => (
                      <Badge key={pattern.failureType} tone="accent">
                        {pattern.failureType} x{pattern.occurrences}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No recurring regression driver has crossed the deterministic repeat threshold in
                    this recent history window.
                  </p>
                )}
              </div>
            ) : null}

            {activeClusterContext.length > 0 ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="accent">Recurring clusters</Badge>
                  <Badge tone="muted">{activeClusterContext.length} linked</Badge>
                </div>
                <div className="space-y-3">
                  {activeClusterContext.map((cluster) => (
                    <div
                      key={cluster.clusterId}
                      className="rounded-[16px] border border-border/60 bg-card/70 p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone="muted">{cluster.clusterKind}</Badge>
                        <Badge tone="muted">{cluster.scopeCount} artifacts</Badge>
                        <Badge tone="muted">{cluster.occurrenceCount} occurrences</Badge>
                      </div>
                      <p className="mt-2 text-sm font-semibold text-foreground">
                        {cluster.label}
                      </p>
                      <p className="text-sm text-muted-foreground">{cluster.summary}</p>
                      {cluster.representativeEvidence.length > 0 ? (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {cluster.representativeEvidence.map((reference) =>
                            renderPreviewLink(
                              reference.reportId ?? comparisonId,
                              reference.caseId,
                              reference.label,
                              returnState,
                            ),
                          )}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {familyHealth ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Current family health
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="accent">{familyHealth.familyId}</Badge>
                  <Badge tone="muted">{familyHealth.healthLabel}</Badge>
                  <Badge tone="muted">{familyHealth.trend.label} trend</Badge>
                  <Badge tone="muted">{familyHealth.trend.volatilityLabel} volatility</Badge>
                  {activeLifecycleAction ? (
                    <Badge tone="muted">{formatLifecycleLabel(activeLifecycleAction.action)}</Badge>
                  ) : null}
                </div>
                <p className="text-sm text-muted-foreground">
                  Recent fail rate{" "}
                  {familyHealth.recentFailRate == null
                    ? "n/a"
                    : `${(familyHealth.recentFailRate * 100).toFixed(1)}%`}{" "}
                  · Previous{" "}
                  {familyHealth.previousFailRate == null
                    ? "n/a"
                    : `${(familyHealth.previousFailRate * 100).toFixed(1)}%`}{" "}
                  · Evaluated in {familyHealth.evaluationRunCount} runs.
                </p>
                {activeLifecycleAction ? (
                  <p className="text-xs text-muted-foreground">
                    Active family state: {formatLifecycleLabel(activeLifecycleAction.action)} at{" "}
                    {activeLifecycleAction.appliedAt}
                  </p>
                ) : null}
              </div>
            ) : null}
          </SurfaceSection>
        ) : null}

        {portfolioItem || portfolioPlans.length > 0 ? (
          <SurfaceSection
            eyebrow="3"
            title="Portfolio context"
            description="Keep the broader priority queue and linked saved plans attached to the same family while reviewing this comparison."
          >
            {portfolioItem ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Portfolio priority
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="accent">Portfolio priority</Badge>
                  <Badge tone="muted">rank {portfolioItem.priorityRank}</Badge>
                  <Badge tone="muted">{formatPriorityBand(portfolioItem.priorityBand)}</Badge>
                  <Badge tone="muted">
                    {portfolioItem.lifecycleAction} · {portfolioItem.healthCondition}
                  </Badge>
                  {portfolioItem.escalationStatus ? (
                    <Badge tone={portfolioItem.priorityBand === "urgent" ? "default" : "muted"}>
                      {portfolioItem.escalationStatus}
                    </Badge>
                  ) : null}
                </div>
                <p className="text-sm text-muted-foreground">{portfolioItem.rationale}</p>
                <p className="text-xs text-muted-foreground">
                  Score {portfolioItem.priorityScore.toFixed(3)} ·{" "}
                  {portfolioItem.recentRegressionCount} recent regressions ·{" "}
                  {portfolioItem.recurringClusterCount} recurring clusters
                </p>
                {portfolioItem.comparisonRefs.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {portfolioItem.comparisonRefs.slice(0, 3).map((reference) =>
                      renderPreviewLink(
                        reference.comparisonId,
                        null,
                        reference.comparisonId,
                        returnState,
                      ),
                    )}
                  </div>
                ) : null}
              </div>
            ) : null}

            {portfolioPlans.length > 0 ? (
              <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="accent">Saved plans</Badge>
                  <Badge tone="muted">{portfolioPlans.length} linked</Badge>
                </div>
                <div className="space-y-3">
                  {portfolioPlans.map((plan) => {
                    const familyAction =
                      plan.actions.find((action) => action.familyId === targetFamilyId) ?? null;
                    return (
                      <div
                        key={plan.planId}
                        className="rounded-[16px] border border-border/60 bg-card/70 p-3"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone="muted">{plan.planId}</Badge>
                          <Badge tone="muted">{plan.createdAt}</Badge>
                          <Badge tone="muted">{plan.impact.actionCount} actions</Badge>
                          {familyAction ? (
                            <Badge tone="accent">
                              {formatLifecycleLabel(familyAction.action)}
                            </Badge>
                          ) : null}
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground">{plan.rationale}</p>
                        {familyAction ? (
                          <p className="mt-2 text-xs text-muted-foreground">
                            This family is included as{" "}
                            {formatLifecycleLabel(familyAction.action)}
                            {familyAction.dependencyFamilyIds.length > 0
                              ? ` with dependencies on ${familyAction.dependencyFamilyIds.join(", ")}`
                              : ""}.
                          </p>
                        ) : null}
                        {familyAction?.comparisonIds.length ? (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {familyAction.comparisonIds.slice(0, 3).map((comparisonId) =>
                              renderPreviewLink(
                                comparisonId,
                                null,
                                comparisonId,
                                returnState,
                              ),
                            )}
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}
          </SurfaceSection>
        ) : null}

        <SurfaceSection
          eyebrow="4"
          title="Take action"
          description="Generate a draft pack, evolve the family, or refresh immutable history from the same comparison context."
        >
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="h-10 rounded-full border border-primary/30 bg-primary/12 px-4 text-sm font-semibold text-primary transition-colors hover:bg-primary/18 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={generationState.status === "loading"}
              onClick={() => {
                setGenerationState({ status: "loading", value: null, message: null });
                void createArtifactRegressionPack({
                  comparisonId,
                  familyId: targetFamilyId,
                  failureType: driverFilter,
                })
                  .then((response) => {
                    setGenerationState({ status: "ready", value: response, message: null });
                    loadVersions();
                  })
                  .catch((error: unknown) => {
                    setGenerationState({
                      status: "error",
                      value: null,
                      message:
                        error instanceof Error
                          ? error.message
                          : "Failed to generate a regression pack",
                    });
                  });
              }}
            >
              {generationState.status === "loading"
                ? "Generating draft..."
                : "Generate draft pack"}
            </button>

            <button
              type="button"
              className="h-10 rounded-full border border-border/70 bg-background/70 px-4 text-sm font-semibold text-foreground transition-colors hover:bg-background disabled:cursor-not-allowed disabled:opacity-60"
              disabled={evolutionState.status === "loading"}
              onClick={() => {
                setEvolutionState({ status: "loading", value: null, message: null });
                void evolveArtifactDataset({
                  familyId: targetFamilyId,
                  comparisonId,
                  failureType: driverFilter,
                })
                  .then((response) => {
                    setEvolutionState({ status: "ready", value: response, message: null });
                    loadVersions();
                  })
                  .catch((error: unknown) => {
                    setEvolutionState({
                      status: "error",
                      value: null,
                      message:
                        error instanceof Error
                          ? error.message
                          : "Failed to evolve the dataset family",
                    });
                  });
              }}
            >
              {evolutionState.status === "loading" ? "Evolving family..." : "Evolve family"}
            </button>

            <button
              type="button"
              className="h-10 rounded-full border border-border/70 bg-background/70 px-4 text-sm font-semibold text-foreground transition-colors hover:bg-background disabled:cursor-not-allowed disabled:opacity-60"
              disabled={versionsState.status === "loading"}
              onClick={loadVersions}
            >
              {versionsState.status === "loading" ? "Loading history..." : "Show version history"}
            </button>
          </div>

          {versionsState.status === "loading" ? (
            <p className="text-sm text-muted-foreground">
              Loading immutable family history, lifecycle actions, and portfolio context for{" "}
              {targetFamilyId}.
            </p>
          ) : null}
          {generationState.status === "error" ? (
            <p className="text-sm text-destructive">{generationState.message}</p>
          ) : null}
          {evolutionState.status === "error" ? (
            <p className="text-sm text-destructive">{evolutionState.message}</p>
          ) : null}
          {versionsState.status === "error" ? (
            <p className="text-sm text-destructive">{versionsState.message}</p>
          ) : null}
        </SurfaceSection>

        {activePreview ? (
          <SurfaceSection
            eyebrow="5"
            title="Preview output"
            description="Stay anchored to the same evidence while checking the generated draft or evolved family output."
          >
            <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="accent">{activePreview.datasetId}</Badge>
                {"versionTag" in activePreview ? (
                  <Badge tone="muted">{activePreview.versionTag}</Badge>
                ) : (
                  <Badge tone="muted">draft</Badge>
                )}
                <Badge tone="muted">
                  {"addedCaseCount" in activePreview
                    ? `${activePreview.addedCaseCount} new`
                    : `${activePreview.selectedCaseCount} selected`}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {"outputPath" in activePreview ? activePreview.outputPath : null}
              </p>
              <div className="flex flex-wrap gap-2">
                {activePreview.previewCases.map((entry) =>
                  renderPreviewLink(
                    entry.sourceReportId,
                    entry.sourceCaseId,
                    entry.promptId,
                    returnState,
                  ),
                )}
              </div>
            </div>
          </SurfaceSection>
        ) : null}

        {versionsState.status === "ready" ? (
          <SurfaceSection
            eyebrow="6"
            title="Version history"
            description="Review immutable dataset lineage and lifecycle actions for the current family."
          >
            <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="muted">Family history</Badge>
                <Badge tone="muted">{versionsState.value.versions.length} versions</Badge>
                {versionsState.value.history.datasetHealth ? (
                  <Badge tone="muted">{versionsState.value.history.datasetHealth.healthLabel}</Badge>
                ) : null}
              </div>
              {versionsState.value.lifecycleActions.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Lifecycle actions
                  </p>
                  {versionsState.value.lifecycleActions.map((action) => (
                    <div
                      key={action.actionId}
                      className="rounded-2xl border border-border/60 bg-card/80 p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone="accent">{formatLifecycleLabel(action.action)}</Badge>
                        <Badge tone="muted">{formatLifecycleLabel(action.healthCondition)}</Badge>
                        <Badge tone="muted">{action.appliedAt}</Badge>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">{action.rationale}</p>
                      {action.targetFamilyId ? (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Target family: {action.targetFamilyId}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}
              {versionsState.value.versions.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No immutable versions exist yet for {targetFamilyId}.
                </p>
              ) : (
                <div className="space-y-2">
                  {versionsState.value.versions.map((version) => (
                    <div
                      key={version.datasetId}
                      className="rounded-2xl border border-border/60 bg-card/80 p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone="accent">{version.datasetId}</Badge>
                        <Badge tone="muted">{version.versionTag}</Badge>
                        <Badge tone="muted">{version.caseCount} cases</Badge>
                        {version.signalVerdict ? (
                          <Badge
                            tone={version.signalVerdict === "regression" ? "default" : "muted"}
                          >
                            {version.signalVerdict}
                          </Badge>
                        ) : null}
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">
                        Source comparison: {version.sourceComparisonId ?? "n/a"} · Parent:{" "}
                        {version.parentDatasetId ?? "root"}
                      </p>
                      {version.sourceComparisonId ? (
                        <div className="mt-3">
                          {renderPreviewLink(
                            version.sourceComparisonId,
                            null,
                            "Open source comparison",
                            returnState,
                          )}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </SurfaceSection>
        ) : null}
      </CardContent>
    </Card>
  );
}
