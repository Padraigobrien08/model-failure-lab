import { useEffect, useState } from "react";
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
  returnState?: unknown;
  autoLoadVersions?: boolean;
  title?: string;
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

export function SignalDatasetAutomationPanel({
  comparisonId,
  dataset,
  signal,
  driverFilter = null,
  recommendation = null,
  returnState = null,
  autoLoadVersions = false,
  title = "Regression pack automation",
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

  const activePreview =
    evolutionState.status === "ready"
      ? evolutionState.value
      : generationState.status === "ready"
        ? generationState.value
        : null;

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
      <CardContent className="space-y-4">
        {recommendation ? (
          <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
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
            </div>
            <p className="text-sm text-muted-foreground">{recommendation.rationale}</p>
            <p className="text-xs text-muted-foreground">
              Family {recommendation.matchedFamily.familyId} · duplicates{" "}
              {recommendation.matchedFamily.duplicateCaseCount}/{recommendation.selectedCaseCount} ·
              cap{" "}
              {recommendation.matchedFamily.familyCaseCap ?? "none"}
            </p>
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
            {generationState.status === "loading" ? "Generating draft..." : "Generate draft pack"}
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
                      error instanceof Error ? error.message : "Failed to evolve the dataset family",
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

        {generationState.status === "error" ? (
          <p className="text-sm text-destructive">{generationState.message}</p>
        ) : null}
        {evolutionState.status === "error" ? (
          <p className="text-sm text-destructive">{evolutionState.message}</p>
        ) : null}
        {versionsState.status === "error" ? (
          <p className="text-sm text-destructive">{versionsState.message}</p>
        ) : null}

        {activePreview ? (
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
        ) : null}

        {versionsState.status === "ready" ? (
          <div className="space-y-3 rounded-[20px] border border-border/70 bg-background/70 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="muted">Family history</Badge>
              <Badge tone="muted">{versionsState.value.versions.length} versions</Badge>
            </div>
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
                        <Badge tone={version.signalVerdict === "regression" ? "default" : "muted"}>
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
        ) : null}
      </CardContent>
    </Card>
  );
}
