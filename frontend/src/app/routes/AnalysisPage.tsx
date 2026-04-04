import { useDeferredValue, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { SignalDatasetAutomationPanel } from "@/components/datasets/SignalDatasetAutomationPanel";
import { InsightPanel } from "@/components/insights/InsightPanel";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { buildComparisonDetailSearchParams, buildRunDetailSearchParams } from "@/lib/artifacts/detailRouteState";
import { buildArtifactQueryPath, createArtifactHarvestDraft, loadArtifactQuery } from "@/lib/artifacts/load";
import { buildArtifactReturnState, createSearchString } from "@/lib/artifacts/navigation";
import type {
  ArtifactHarvestResponse,
  ArtifactInsightEvidenceRef,
  ArtifactQueryMode,
  ArtifactQueryState,
} from "@/lib/artifacts/types";

type FilterSelectProps = {
  label: string;
  value: string;
  options: string[];
  placeholder?: string;
  onChange: (value: string) => void;
};

const AGGREGATE_OPTIONS = ["failure_type", "model", "dataset", "prompt_id"];
const LAST_N_OPTIONS = ["1", "5", "10"];

type ExportState =
  | { status: "idle"; response: null; message: null }
  | { status: "loading"; response: null; message: null }
  | { status: "ready"; response: ArtifactHarvestResponse; message: null }
  | { status: "error"; response: null; message: string };

function readSearchValue(searchParams: URLSearchParams, key: string): string {
  return searchParams.get(key) ?? "";
}

function readMode(searchParams: URLSearchParams): ArtifactQueryMode {
  const mode = searchParams.get("mode");
  if (mode === "deltas" || mode === "aggregates" || mode === "signals") {
    return mode;
  }
  return "cases";
}

function readSignalDirection(searchParams: URLSearchParams): string {
  return searchParams.get("signalDirection") ?? "regression";
}

function buildAnalysisSearchParams(
  current: URLSearchParams,
  patch: Partial<Record<string, string>>,
): URLSearchParams {
  const next = new URLSearchParams(current);
  for (const [key, value] of Object.entries(patch)) {
    if (typeof value === "string" && value.trim().length > 0) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
  }
  return next;
}

function buildAnalysisExportStem(
  mode: ArtifactQueryMode,
  values: { failureType: string; delta: string; dataset: string; model: string },
): string {
  const descriptor =
    values.failureType || values.delta || values.dataset || values.model || "selection";
  return `analysis-${mode}-${descriptor}`
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function FilterSelect({
  label,
  value,
  options,
  placeholder = "All",
  onChange,
}: FilterSelectProps) {
  return (
    <label className="flex min-w-[11rem] flex-col gap-2">
      <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </span>
      <select
        aria-label={label}
        className="h-11 rounded-full border border-border/70 bg-card/80 px-4 text-sm text-foreground outline-none transition-colors focus:border-primary/40"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

export function AnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { artifactState, artifactOverview } = useAppRouteContext();
  const [queryState, setQueryState] = useState<ArtifactQueryState>({
    status: "idle",
    response: null,
    message: null,
  });
  const [exportState, setExportState] = useState<ExportState>({
    status: "idle",
    response: null,
    message: null,
  });

  const mode = readMode(searchParams);
  const deferredSearch = useDeferredValue(searchParams.toString());

  useEffect(() => {
    if (artifactState.status !== "ready") {
      setQueryState({ status: "idle", response: null, message: null });
      return;
    }

    const requestSearchParams = new URLSearchParams(deferredSearch);
    if (!requestSearchParams.has("mode")) {
      requestSearchParams.set("mode", mode);
    }
    if (!requestSearchParams.has("limit")) {
      requestSearchParams.set("limit", "20");
    }
    if (mode === "aggregates" && !requestSearchParams.has("aggregateBy")) {
      requestSearchParams.set("aggregateBy", "failure_type");
    }
    requestSearchParams.set("summarize", "1");

    setQueryState({ status: "loading", response: null, message: null });
    void loadArtifactQuery(requestSearchParams)
      .then((response) => {
        setQueryState({ status: "ready", response, message: null });
      })
      .catch((error: unknown) => {
        setQueryState({
          status: "incompatible",
          response: null,
          message: error instanceof Error ? error.message : "Failed to load artifact query",
        });
      });
  }, [artifactState.status, deferredSearch, mode]);

  useEffect(() => {
    setExportState({ status: "idle", response: null, message: null });
  }, [deferredSearch, mode]);

  if (artifactState.status !== "ready" || artifactOverview === null) {
    return <ArtifactStatePanel area="Analysis" state={artifactState} />;
  }

  if (queryState.status === "idle" || queryState.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Analysis</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading cross-run analysis.</CardTitle>
            <CardDescription>
              The debugger is resolving query-backed results from the derived local artifact index.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (queryState.status === "incompatible" || queryState.response === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Analysis</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The cross-run analysis view could not be loaded.</CardTitle>
            <CardDescription>
              The query layer failed to build or read the derived local index for the current
              artifact workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {queryState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  const response = queryState.response;
  const returnState = buildArtifactReturnState("/analysis", createSearchString(searchParams));
  const resultCount = response.rows.length;
  const failureType = readSearchValue(searchParams, "failureType");
  const model = readSearchValue(searchParams, "model");
  const dataset = readSearchValue(searchParams, "dataset");
  const delta = readSearchValue(searchParams, "delta");
  const aggregateBy = readSearchValue(searchParams, "aggregateBy");
  const signalDirection = readSignalDirection(searchParams);
  const since = readSearchValue(searchParams, "since");
  const lastN = readSearchValue(searchParams, "lastN");
  const canExportDraft = response.mode !== "aggregates" && response.mode !== "signals" && resultCount > 0;

  const renderEvidenceLink = (reference: ArtifactInsightEvidenceRef) => {
    if (reference.kind === "run_case" && reference.runId && reference.caseId) {
      const runSearch = buildRunDetailSearchParams(new URLSearchParams(), {
        section: reference.section === "evidence" ? "evidence" : null,
        caseId: reference.caseId,
      }).toString();
      return (
        <Link
          key={`${reference.kind}:${reference.runId}:${reference.caseId}`}
          className="inline-flex rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground no-underline transition-colors hover:bg-background"
          state={returnState}
          to={{
            pathname: `/runs/${encodeURIComponent(reference.runId)}`,
            search: runSearch.length > 0 ? `?${runSearch}` : "",
          }}
        >
          {reference.label}
        </Link>
      );
    }

    if (reference.kind === "comparison_case" && reference.reportId && reference.caseId) {
      const comparisonSearch = buildComparisonDetailSearchParams(new URLSearchParams(), {
        section: reference.section === "transitions" ? "transitions" : null,
        caseId: reference.caseId,
        transition: reference.transitionType,
      }).toString();
      return (
        <Link
          key={`${reference.kind}:${reference.reportId}:${reference.caseId}`}
          className="inline-flex rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground no-underline transition-colors hover:bg-background"
          state={returnState}
          to={{
            pathname: `/comparisons/${encodeURIComponent(reference.reportId)}`,
            search: comparisonSearch.length > 0 ? `?${comparisonSearch}` : "",
          }}
        >
          {reference.label}
        </Link>
      );
    }

    return null;
  };

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Analysis</Badge>
          <Badge tone="muted">{mode}</Badge>
          <Badge tone="muted">{resultCount} rows</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Cross-run artifact analysis.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          Ask the artifact workspace a structured question first, then drill straight into saved
          evidence. This view is backed by the derived local query index instead of raw directory
          scans.
        </p>
      </div>

      <div className="rounded-[24px] border border-border/70 bg-card/70 p-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <FilterSelect
              label="Mode"
              value={mode}
              options={["cases", "deltas", "aggregates", "signals"]}
              placeholder="Cases"
              onChange={(value) => {
                const nextMode = value || "cases";
                const patch: Partial<Record<string, string>> = { mode: nextMode };
                if (nextMode === "aggregates" && aggregateBy.length === 0) {
                  patch.aggregateBy = "failure_type";
                }
                if (nextMode === "signals") {
                  patch.signalDirection = "regression";
                }
                setSearchParams(buildAnalysisSearchParams(searchParams, patch), {
                  replace: true,
                });
              }}
            />

            {mode === "cases" || mode === "signals" ? (
              <FilterSelect
                label={mode === "signals" ? "Driver type" : "Failure type"}
                value={failureType}
                options={response.facets.failureTypes}
                onChange={(value) =>
                  setSearchParams(
                    buildAnalysisSearchParams(searchParams, { failureType: value }),
                    { replace: true },
                  )
                }
              />
            ) : null}

            {mode === "deltas" ? (
              <FilterSelect
                label="Delta"
                value={delta}
                options={response.facets.deltaTypes}
                onChange={(value) =>
                  setSearchParams(buildAnalysisSearchParams(searchParams, { delta: value }), {
                    replace: true,
                  })
                }
              />
            ) : null}

            {mode === "signals" ? (
              <FilterSelect
                label="Direction"
                value={signalDirection}
                options={["regression", "improvement", "neutral", "incompatible", "all"]}
                placeholder="regression"
                onChange={(value) =>
                  setSearchParams(
                    buildAnalysisSearchParams(searchParams, {
                      signalDirection: value || "regression",
                    }),
                    { replace: true },
                  )
                }
              />
            ) : null}

            {mode === "aggregates" ? (
              <FilterSelect
                label="Group by"
                value={aggregateBy || "failure_type"}
                options={AGGREGATE_OPTIONS}
                placeholder="failure_type"
                onChange={(value) =>
                  setSearchParams(
                    buildAnalysisSearchParams(searchParams, {
                      aggregateBy: value || "failure_type",
                    }),
                    { replace: true },
                  )
                }
              />
            ) : null}

            <FilterSelect
              label="Dataset"
              value={dataset}
              options={response.facets.datasets}
              onChange={(value) =>
                setSearchParams(buildAnalysisSearchParams(searchParams, { dataset: value }), {
                  replace: true,
                })
              }
            />

            <FilterSelect
              label="Model"
              value={model}
              options={response.facets.models}
              onChange={(value) =>
                setSearchParams(buildAnalysisSearchParams(searchParams, { model: value }), {
                  replace: true,
                })
              }
            />

            <FilterSelect
              label="Last N"
              value={lastN}
              options={LAST_N_OPTIONS}
              onChange={(value) =>
                setSearchParams(buildAnalysisSearchParams(searchParams, { lastN: value }), {
                  replace: true,
                })
              }
            />

            <label className="flex min-w-[11rem] flex-col gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Since
              </span>
              <input
                aria-label="Since"
                type="date"
                value={since}
                onChange={(event) =>
                  setSearchParams(
                    buildAnalysisSearchParams(searchParams, { since: event.target.value }),
                    { replace: true },
                  )
                }
                className="h-11 rounded-full border border-border/70 bg-card/80 px-4 text-sm text-foreground outline-none transition-colors focus:border-primary/40"
              />
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {canExportDraft ? (
              <button
                type="button"
                className="h-11 rounded-full border border-primary/30 bg-primary/12 px-5 text-sm font-semibold text-primary transition-colors hover:bg-primary/18 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={exportState.status === "loading"}
                onClick={() => {
                  setExportState({ status: "loading", response: null, message: null });
                  void createArtifactHarvestDraft({
                    mode: response.mode,
                    filters: {
                      failureType,
                      model,
                      dataset,
                      runId: readSearchValue(searchParams, "runId"),
                      promptId: readSearchValue(searchParams, "promptId"),
                      reportId: readSearchValue(searchParams, "reportId"),
                      baselineRunId: readSearchValue(searchParams, "baselineRunId"),
                      candidateRunId: readSearchValue(searchParams, "candidateRunId"),
                      delta,
                      lastN: lastN.length > 0 ? Number(lastN) : null,
                      since,
                      until: readSearchValue(searchParams, "until"),
                      limit: Number(readSearchValue(searchParams, "limit") || "20"),
                    },
                    outputStem: buildAnalysisExportStem(response.mode, {
                      failureType,
                      delta,
                      dataset,
                      model,
                    }),
                  })
                    .then((harvestResponse) => {
                      setExportState({
                        status: "ready",
                        response: harvestResponse,
                        message: null,
                      });
                    })
                    .catch((error: unknown) => {
                      setExportState({
                        status: "error",
                        response: null,
                        message:
                          error instanceof Error
                            ? error.message
                            : "Failed to export a draft dataset pack",
                      });
                    });
                }}
              >
                {exportState.status === "loading" ? "Exporting draft..." : "Export draft dataset"}
              </button>
            ) : null}
            <button
              type="button"
              className="h-11 rounded-full border border-border/70 bg-background/70 px-5 text-sm font-semibold text-foreground transition-colors hover:bg-background"
              onClick={() =>
                setSearchParams(new URLSearchParams({ mode: "cases" }), { replace: true })
              }
            >
              Clear filters
            </button>
          </div>
        </div>
      </div>

      {exportState.status === "ready" ? (
        <Card className="border-primary/20 bg-primary/[0.04]">
          <CardHeader>
            <CardTitle>Draft dataset exported.</CardTitle>
            <CardDescription>
              {exportState.response.datasetId} was written to {exportState.response.outputPath} with{" "}
              {exportState.response.selectedCaseCount} selected cases.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {exportState.status === "error" ? (
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>Draft export failed.</CardTitle>
            <CardDescription>{exportState.message}</CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {response.mode !== "signals" ? (
        <InsightPanel
          badgeLabel="Insights"
          title="Grounded cross-run readout"
          description="The heuristic insight layer summarizes the current filtered result set and keeps every pattern anchored to drillable saved evidence."
          report={response.insightReport}
          renderEvidenceLink={renderEvidenceLink}
        />
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Active artifact root</CardTitle>
          <CardDescription>
            Querying {artifactOverview.source.label.toLowerCase()} at {artifactOverview.source.path}
          </CardDescription>
        </CardHeader>
      </Card>

      {response.mode === "signals" ? (
        <div className="grid gap-4">
          {response.rows.map((row) => {
            const primaryDriver = row.topDrivers[0] ?? null;
            const primaryCaseId = primaryDriver?.caseIds[0] ?? null;
            const comparisonSearch = buildComparisonDetailSearchParams(new URLSearchParams(), {
              section: "transitions",
              caseId: primaryCaseId,
            }).toString();
            return (
              <Card key={row.reportId}>
                <CardHeader>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={row.signalVerdict === "improvement" ? "accent" : row.signalVerdict === "regression" ? "default" : "muted"}>
                      {row.signalVerdict}
                    </Badge>
                    <Badge tone="muted">{(row.severity * 100).toFixed(1)}% severity</Badge>
                    {row.dataset ? <Badge tone="muted">{row.dataset}</Badge> : null}
                  </div>
                  <CardTitle className="text-xl">{row.reportId}</CardTitle>
                  <CardDescription>
                    {row.baselineRunId} → {row.candidateRunId} • {row.createdAt}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Regression {`${(row.regressionScore * 100).toFixed(1)}%`} · Improvement{" "}
                    {`${(row.improvementScore * 100).toFixed(1)}%`}
                  </p>
                  {row.topDrivers.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {row.topDrivers.map((driver) => (
                        <span
                          key={`${row.reportId}-${driver.driverRank}`}
                          className="inline-flex rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground"
                        >
                          {driver.failureType} {driver.delta > 0 ? "+" : ""}
                          {(driver.delta * 100).toFixed(1)}%
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="flex flex-wrap gap-3">
                    <Link
                      className="inline-flex rounded-full border border-border/70 bg-background/70 px-4 py-2 text-sm font-semibold text-foreground no-underline transition-colors hover:bg-background"
                      state={returnState}
                      to={{
                        pathname: `/comparisons/${encodeURIComponent(row.reportId)}`,
                        search: comparisonSearch.length > 0 ? `?${comparisonSearch}` : "",
                      }}
                    >
                      {primaryCaseId ? "Inspect strongest driver" : "Open comparison"}
                    </Link>
                  </div>
                  <SignalDatasetAutomationPanel
                    comparisonId={row.reportId}
                    dataset={row.dataset}
                    signal={{
                      verdict: row.signalVerdict,
                      reason: null,
                      regressionScore: row.regressionScore,
                      improvementScore: row.improvementScore,
                      netScore: row.netScore,
                      severity: row.severity,
                      topDrivers: row.topDrivers,
                    }}
                    driverFilter={failureType || null}
                    returnState={returnState}
                    title="Turn this signal into a dataset"
                  />
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : response.mode === "cases" ? (
        <div className="grid gap-4">
          {response.rows.map((row) => {
            const runSearch = buildRunDetailSearchParams(new URLSearchParams(), {
              section: "evidence",
              caseId: row.caseId,
            }).toString();
            return (
              <Card key={`${row.runId}-${row.caseId}`}>
                <CardHeader>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="accent">{row.failureType ?? "unclassified"}</Badge>
                    <Badge tone="muted">{row.model}</Badge>
                    <Badge tone="muted">{row.dataset}</Badge>
                  </div>
                  <CardTitle className="text-xl">{row.prompt}</CardTitle>
                  <CardDescription>
                    {row.runId} • {row.caseId} • {row.createdAt}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {row.explanation ? (
                    <p className="text-sm text-muted-foreground">{row.explanation}</p>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-2">
                    {row.tags.map((tag) => (
                      <Badge key={`${row.caseId}-${tag}`} tone="muted">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <Link
                    className="inline-flex rounded-full border border-primary/30 bg-primary/12 px-4 py-2 text-sm font-semibold text-primary no-underline"
                    to={{
                      pathname: `/runs/${encodeURIComponent(row.runId)}`,
                      search: runSearch.length > 0 ? `?${runSearch}` : "",
                    }}
                    state={returnState}
                  >
                    Inspect run evidence
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : null}

      {response.mode === "deltas" ? (
        <div className="grid gap-4">
          {response.rows.map((row) => {
            const comparisonSearch = buildComparisonDetailSearchParams(new URLSearchParams(), {
              section: "transitions",
              caseId: row.caseId,
              transition: row.transitionType,
            }).toString();
            return (
              <Card key={`${row.reportId}-${row.caseId}`}>
                <CardHeader>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="accent">{row.deltaKind}</Badge>
                    <Badge tone="muted">{row.dataset ?? "unknown dataset"}</Badge>
                  </div>
                  <CardTitle className="text-xl">{row.prompt}</CardTitle>
                  <CardDescription>
                    {row.reportId} • {row.baselineRunId} → {row.candidateRunId}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    {row.transitionLabel}
                    {row.baselineFailureType || row.candidateFailureType
                      ? ` • ${row.baselineFailureType ?? "none"} → ${row.candidateFailureType ?? "none"}`
                      : ""}
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    {row.tags.map((tag) => (
                      <Badge key={`${row.reportId}-${row.caseId}-${tag}`} tone="muted">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <Link
                    className="inline-flex rounded-full border border-primary/30 bg-primary/12 px-4 py-2 text-sm font-semibold text-primary no-underline"
                    to={{
                      pathname: `/comparisons/${encodeURIComponent(row.reportId)}`,
                      search: comparisonSearch.length > 0 ? `?${comparisonSearch}` : "",
                    }}
                    state={returnState}
                  >
                    Inspect comparison evidence
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : null}

      {response.mode === "aggregates" ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {response.rows.map((row) => (
            <Card key={row.groupKey}>
              <CardHeader>
                <Badge tone="muted">{row.caseCount} cases</Badge>
                <CardTitle className="text-xl">{row.groupLabel}</CardTitle>
                <CardDescription>{row.groupKey}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : null}

      {resultCount === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No query rows match the current filters.</CardTitle>
            <CardDescription>
              Adjust one or more analysis filters to broaden the cross-run result set.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Request URL: {buildArtifactQueryPath(searchParams)}
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}
