import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useParams, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { RunCaseDetailPanel } from "@/components/run/RunCaseDetailPanel";
import { RunCaseLensTabs } from "@/components/run/RunCaseLensTabs";
import { RunCaseTable } from "@/components/run/RunCaseTable";
import { RunDetailHeader } from "@/components/run/RunDetailHeader";
import { RunNotableCases } from "@/components/run/RunNotableCases";
import { RunSummaryMetricStrip } from "@/components/run/RunSummaryMetricStrip";
import { RunSummarySections } from "@/components/run/RunSummarySections";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  buildRunDetailSearchParams,
  parseRunDetailSearch,
  resolveRunDetailSection,
  resolveRunLensForCase,
  RUN_DETAIL_SECTIONS,
  searchParamsEqual,
  type RunDetailSectionKey,
} from "@/lib/artifacts/detailRouteState";
import { resolveArtifactReturnHref } from "@/lib/artifacts/navigation";
import { loadRunDetail } from "@/lib/artifacts/load";
import type {
  RunCaseLensKey,
  RunCaseRecord,
  RunDetailState,
} from "@/lib/artifacts/types";
import type { ComparisonInventoryItem } from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

function selectCasesById(caseIds: string[], cases: RunCaseRecord[]): RunCaseRecord[] {
  const caseMap = new Map(cases.map((caseRow) => [caseRow.caseId, caseRow]));
  return caseIds
    .map((caseId) => caseMap.get(caseId))
    .filter((caseRow): caseRow is RunCaseRecord => caseRow !== undefined);
}

function resolveLensCases(
  lens: RunCaseLensKey,
  detail: {
    lenses: {
      mismatchCaseIds: string[];
      notableCaseIds: string[];
      allCaseIds: string[];
      errorCaseIds: string[];
    };
    cases: RunCaseRecord[];
  },
) {
  if (lens === "mismatches") {
    return selectCasesById(detail.lenses.mismatchCaseIds, detail.cases);
  }

  if (lens === "notable") {
    return selectCasesById(detail.lenses.notableCaseIds, detail.cases);
  }

  if (lens === "errors") {
    return selectCasesById(detail.lenses.errorCaseIds, detail.cases);
  }

  return selectCasesById(detail.lenses.allCaseIds, detail.cases);
}

function resolvePreferredLens(detail: {
  lenses: {
    mismatchCaseIds: string[];
    notableCaseIds: string[];
    allCaseIds: string[];
    errorCaseIds: string[];
  };
}): RunCaseLensKey {
  if (detail.lenses.mismatchCaseIds.length > 0) {
    return "mismatches";
  }

  if (detail.lenses.notableCaseIds.length > 0) {
    return "notable";
  }

  if (detail.lenses.allCaseIds.length > 0) {
    return "all";
  }

  if (detail.lenses.errorCaseIds.length > 0) {
    return "errors";
  }

  return "mismatches";
}

function formatOptionalValue(value: string | number | null): string {
  if (value === null || value === "") {
    return "n/a";
  }
  return String(value);
}

function resolveObservedSection<SectionKey extends string>(
  entries: IntersectionObserverEntry[],
): SectionKey | null {
  const visibleEntries = entries.filter((entry) => entry.isIntersecting);
  if (visibleEntries.length === 0) {
    return null;
  }

  const closestEntry = visibleEntries.sort(
    (left, right) =>
      Math.abs(left.boundingClientRect.top) - Math.abs(right.boundingClientRect.top),
  )[0];

  const sectionId = closestEntry.target.getAttribute("data-section-id");
  return sectionId as SectionKey | null;
}

export function RunDetailPage() {
  const { runId } = useParams();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { artifactState, runInventoryState, comparisonInventoryState } = useAppRouteContext();
  const [detailState, setDetailState] = useState<RunDetailState>({
    status: "idle",
    detail: null,
    message: null,
  });
  const inventory = runInventoryState.status === "ready" ? runInventoryState.inventory : null;
  const run = inventory?.runs.find((item) => item.runId === runId);
  const requestedState = useMemo(() => parseRunDetailSearch(searchParams), [searchParams]);
  const returnHref = useMemo(
    () => resolveArtifactReturnHref(location.state, "/"),
    [location.state],
  );

  useEffect(() => {
    if (!runId || run === undefined) {
      startTransition(() => {
        setDetailState({
          status: "idle",
          detail: null,
          message: null,
        });
      });
      return;
    }

    startTransition(() => {
      setDetailState({
        status: "loading",
        detail: null,
        message: null,
      });
    });

    void loadRunDetail(runId)
      .then((detail) => {
        startTransition(() => {
          setDetailState({
            status: "ready",
            detail,
            message: null,
          });
        });
      })
      .catch((error: unknown) => {
        const message =
          error instanceof Error ? error.message : "Failed to load run detail";
        startTransition(() => {
          setDetailState({
            status: "incompatible",
            detail: null,
            message,
          });
        });
      });
  }, [run, runId]);

  const activeLens = useMemo<RunCaseLensKey>(() => {
    if (detailState.status !== "ready") {
      return "mismatches";
    }

    return (
      requestedState.lens ??
      resolveRunLensForCase(detailState.detail, requestedState.caseId) ??
      resolvePreferredLens(detailState.detail)
    );
  }, [detailState, requestedState.caseId, requestedState.lens]);

  const notableCases = useMemo(() => {
    if (detailState.status !== "ready") {
      return [];
    }
    return selectCasesById(
      detailState.detail.lenses.notableCaseIds,
      detailState.detail.cases,
    ).slice(0, 3);
  }, [detailState]);

  const caseLensCounts = useMemo(
    () => ({
      mismatches:
        detailState.status === "ready" ? detailState.detail.lenses.mismatchCaseIds.length : 0,
      notable:
        detailState.status === "ready" ? detailState.detail.lenses.notableCaseIds.length : 0,
      all: detailState.status === "ready" ? detailState.detail.lenses.allCaseIds.length : 0,
      errors: detailState.status === "ready" ? detailState.detail.lenses.errorCaseIds.length : 0,
    }),
    [detailState],
  );

  const visibleCases = useMemo(() => {
    if (detailState.status !== "ready") {
      return [];
    }

    return resolveLensCases(activeLens, detailState.detail);
  }, [activeLens, detailState]);

  const selectedCase = useMemo(() => {
    const selectedCaseId =
      requestedState.caseId &&
      visibleCases.some((caseRow) => caseRow.caseId === requestedState.caseId)
        ? requestedState.caseId
        : visibleCases[0]?.caseId ?? null;

    if (selectedCaseId === null) {
      return null;
    }

    return visibleCases.find((caseRow) => caseRow.caseId === selectedCaseId) ?? null;
  }, [requestedState.caseId, visibleCases]);

  const selectedCaseId = selectedCase?.caseId ?? null;

  const resolvedSection = useMemo(
    () =>
      resolveRunDetailSection(
        requestedState.section,
        requestedState.lens,
        requestedState.caseId,
      ),
    [requestedState.caseId, requestedState.lens, requestedState.section],
  );
  const [activeSectionId, setActiveSectionId] =
    useState<RunDetailSectionKey>(resolvedSection);
  const [highlightedSectionId, setHighlightedSectionId] =
    useState<RunDetailSectionKey | null>(null);
  const [landingNotice, setLandingNotice] = useState<string | null>(null);
  const sectionRefs = useRef<Record<RunDetailSectionKey, HTMLElement | null>>({
    identity: null,
    shape: null,
    diagnosis: null,
    notable: null,
    evidence: null,
  });

  const setSectionRef =
    (sectionId: RunDetailSectionKey) => (element: HTMLElement | null) => {
      sectionRefs.current[sectionId] = element;
    };

  const resolvedLandingNotice = useMemo(() => {
    if (requestedState.caseId === null || requestedState.caseId === selectedCaseId) {
      return null;
    }

    if (selectedCaseId === null) {
      return `Requested case ${requestedState.caseId} is unavailable. Showing the nearest available evidence section instead.`;
    }

    return `Requested case ${requestedState.caseId} is unavailable in this evidence state. Showing ${selectedCaseId} instead.`;
  }, [requestedState.caseId, selectedCaseId]);

  useEffect(() => {
    if (resolvedLandingNotice === null) {
      return;
    }

    setLandingNotice(resolvedLandingNotice);
    const timeout = window.setTimeout(() => {
      setLandingNotice((current) =>
        current === resolvedLandingNotice ? null : current,
      );
    }, 2400);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [resolvedLandingNotice]);

  const relatedComparisons = useMemo(() => {
    if (comparisonInventoryState.status !== "ready" || !runId) {
      return [];
    }

    return comparisonInventoryState.inventory.comparisons
      .filter(
        (comparison) =>
          comparison.baselineRunId === runId || comparison.candidateRunId === runId,
      )
      .slice()
      .sort((left, right) => {
        const leftTime = Date.parse(left.createdAt);
        const rightTime = Date.parse(right.createdAt);

        if (!Number.isNaN(leftTime) && !Number.isNaN(rightTime) && leftTime !== rightTime) {
          return rightTime - leftTime;
        }

        if (left.createdAt !== right.createdAt) {
          return right.createdAt.localeCompare(left.createdAt);
        }

        return right.reportId.localeCompare(left.reportId);
      });
  }, [comparisonInventoryState, runId]);

  const handleSelectNotableCase = (caseId: string) => {
    setSearchParams(
      buildRunDetailSearchParams(searchParams, {
        section: "evidence",
        lens: "notable",
        caseId,
      }),
      {
        replace: true,
        state: location.state,
      },
    );
  };

  useEffect(() => {
    if (detailState.status !== "ready") {
      return;
    }

    const nextSearchParams = buildRunDetailSearchParams(searchParams, {
      section: resolvedSection,
      lens: activeLens,
      caseId: selectedCaseId,
    });

    if (searchParamsEqual(searchParams, nextSearchParams)) {
      return;
    }

    setSearchParams(nextSearchParams, {
      replace: true,
      state: location.state,
    });
  }, [
    activeLens,
    detailState.status,
    location.state,
    resolvedSection,
    searchParams,
    selectedCaseId,
    setSearchParams,
  ]);

  useEffect(() => {
    setActiveSectionId(resolvedSection);
  }, [resolvedSection]);

  useEffect(() => {
    if (detailState.status !== "ready" || typeof IntersectionObserver === "undefined") {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const observedSection = resolveObservedSection<RunDetailSectionKey>(entries);
        if (observedSection) {
          setActiveSectionId(observedSection);
        }
      },
      {
        rootMargin: "-18% 0px -58% 0px",
        threshold: [0.2, 0.35, 0.5, 0.7],
      },
    );

    for (const sectionRef of Object.values(sectionRefs.current)) {
      if (sectionRef) {
        observer.observe(sectionRef);
      }
    }

    return () => {
      observer.disconnect();
    };
  }, [detailState.status]);

  useEffect(() => {
    if (detailState.status !== "ready") {
      return;
    }

    const targetSection = sectionRefs.current[resolvedSection];
    if (!targetSection) {
      return;
    }

    const animationFrame = window.requestAnimationFrame(() => {
      if (typeof targetSection.scrollIntoView === "function") {
        targetSection.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
      setActiveSectionId(resolvedSection);
      setHighlightedSectionId(resolvedSection);
    });

    const timeout = window.setTimeout(() => {
      setHighlightedSectionId((current) =>
        current === resolvedSection ? null : current,
      );
    }, 1800);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.clearTimeout(timeout);
    };
  }, [detailState.status, resolvedSection, activeLens, selectedCaseId]);

  if (artifactState.status !== "ready") {
    return <ArtifactStatePanel area="Runs" state={artifactState} />;
  }

  if (runInventoryState.status === "idle" || runInventoryState.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Run detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading selected run.</CardTitle>
            <CardDescription>
              The inventory route is resolving the saved run detail payload from the default
              local artifact root.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (runInventoryState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Run detail</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The selected run could not be resolved.</CardTitle>
            <CardDescription>
              The runs inventory is not available under the supported artifact contract.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {runInventoryState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  if (inventory === null || !runId) {
    return null;
  }

  if (run === undefined) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Run detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Run not found.</CardTitle>
            <CardDescription>
              The requested run id is not present in the active inventory.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link className="text-sm font-semibold text-primary no-underline" to={returnHref}>
              Back to runs
            </Link>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (detailState.status === "idle" || detailState.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Run detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading run report detail.</CardTitle>
            <CardDescription>
              Reading `run.json`, `results.json`, `report.json`, and `report_details.json` for{" "}
              {run.runId}.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (detailState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Run detail</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The saved run detail could not be loaded.</CardTitle>
            <CardDescription>
              The selected run exists in the inventory, but its saved detail artifacts do not
              match the supported contract.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {detailState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  if (detailState.status !== "ready") {
    return null;
  }

  const detail = detailState.detail;

  return (
    <section className="space-y-8">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.58fr)_minmax(14rem,0.42fr)] xl:items-start">
        <div className="min-w-0 space-y-8">
          <section
            id="run-detail-identity"
            ref={setSectionRef("identity")}
            data-section-id="identity"
            className={cn(
              "scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
              highlightedSectionId === "identity"
                ? "border-primary/25 bg-primary/[0.035]"
                : "",
            )}
          >
            <RunDetailHeader
              runId={detail.run.runId}
              dataset={detail.run.dataset}
              model={detail.run.model}
              status={detail.run.status}
              createdAt={detail.run.createdAt}
              inventoryHref={returnHref}
              reportId={detail.run.reportId}
              adapterId={detail.run.adapterId}
              classifierId={detail.run.classifierId}
              runSeed={detail.run.runSeed}
            />
          </section>

          <section
            id="run-detail-shape"
            ref={setSectionRef("shape")}
            data-section-id="shape"
            className={cn(
              "scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
              highlightedSectionId === "shape"
                ? "border-primary/25 bg-primary/[0.035]"
                : "",
            )}
          >
            <RunSummaryMetricStrip metrics={detail.metrics} />
          </section>

          <section
            id="run-detail-diagnosis"
            ref={setSectionRef("diagnosis")}
            data-section-id="diagnosis"
            className={cn(
              "scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
              highlightedSectionId === "diagnosis"
                ? "border-primary/25 bg-primary/[0.035]"
                : "",
            )}
          >
            <RunSummarySections
              failureTypes={detail.summary.failureTypes}
              expectationVerdicts={detail.summary.expectationVerdicts}
              tagSlices={detail.summary.tagSlices}
            />
          </section>

          <section
            id="run-detail-notable"
            ref={setSectionRef("notable")}
            data-section-id="notable"
            className={cn(
              "scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
              highlightedSectionId === "notable"
                ? "border-primary/25 bg-primary/[0.035]"
                : "",
            )}
          >
            <RunNotableCases
              cases={notableCases}
              selectedCaseId={selectedCaseId}
              onSelectCase={handleSelectNotableCase}
            />
          </section>
        </div>

        <aside className="space-y-4 xl:sticky xl:top-24">
          <Card className="rounded-[24px] border border-border/70 bg-card/75">
            <CardHeader className="space-y-1 pb-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Section jumps
              </p>
              <CardTitle className="text-lg">Stay inside the run flow</CardTitle>
              <CardDescription>
                Move between the saved investigation stages without dropping the selected evidence
                state.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {RUN_DETAIL_SECTIONS.map((section, index) => (
                <button
                  key={section.id}
                  type="button"
                  aria-pressed={activeSectionId === section.id}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-[18px] border px-3 py-3 text-left transition-colors",
                    activeSectionId === section.id
                      ? "border-primary/35 bg-primary/10 text-primary"
                      : "border-border/60 bg-background/70 text-muted-foreground hover:text-foreground",
                  )}
                  onClick={() =>
                    setSearchParams(
                      buildRunDetailSearchParams(searchParams, {
                        section: section.id,
                        lens: activeLens,
                        caseId: selectedCaseId,
                      }),
                      {
                        replace: true,
                        state: location.state,
                      },
                    )
                  }
                >
                  <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-background/85 text-[11px] font-semibold text-muted-foreground">
                    {index + 1}
                  </span>
                  <span className="text-sm font-semibold">{section.label}</span>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[24px] border border-border/70 bg-card/75">
            <CardHeader className="space-y-1 pb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Debugger context
              </p>
              <CardTitle className="text-lg">Persistent run provenance</CardTitle>
              <CardDescription>
                Keep the saved lineage visible while you read the failure shape, diagnosis, and
                case evidence.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Source root
                </p>
                <p className="mt-2 break-all font-mono text-xs text-foreground">
                  {detail.source.path}
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Report id
                  </p>
                  <p className="mt-2 break-all text-sm font-semibold text-foreground">
                    {detail.run.reportId}
                  </p>
                </div>
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Adapter
                  </p>
                  <p className="mt-2 text-sm text-foreground">
                    {formatOptionalValue(detail.run.adapterId)}
                  </p>
                </div>
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Classifier
                  </p>
                  <p className="mt-2 text-sm text-foreground">
                    {formatOptionalValue(detail.run.classifierId)}
                  </p>
                </div>
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Run seed
                  </p>
                  <p className="mt-2 text-sm text-foreground">
                    {formatOptionalValue(detail.run.runSeed)}
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Mismatch cases
                  </p>
                  <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                    {detail.lenses.mismatchCaseIds.length}
                  </p>
                </div>
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Notable cases
                  </p>
                  <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                    {detail.lenses.notableCaseIds.length}
                  </p>
                </div>
              </div>
              {relatedComparisons.length > 0 ? (
                <div className="space-y-3 border-t border-border/60 pt-4">
                  <div className="space-y-1">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Related comparisons
                    </p>
                    <h3 className="text-lg font-semibold tracking-[-0.03em] text-foreground">
                      Saved comparisons touching this run
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Jump directly into saved reports that reference this run.
                    </p>
                  </div>
                  <div className="space-y-3">
                    {relatedComparisons.map((comparison: ComparisonInventoryItem) => (
                      <div
                        key={comparison.reportId}
                        className="space-y-2 rounded-[18px] border border-border/55 bg-background/60 px-3 py-3"
                      >
                        <div className="space-y-1">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                            {comparison.baselineRunId === runId ? "Candidate report" : "Baseline report"}
                          </p>
                          <Link
                            className="block break-all font-mono text-sm font-semibold text-primary no-underline"
                            to={`/comparisons/${encodeURIComponent(comparison.reportId)}`}
                            state={{
                              returnTo: {
                                pathname: location.pathname,
                                search: location.search,
                              },
                            }}
                          >
                            {comparison.reportId}
                          </Link>
                          <p className="text-sm text-muted-foreground">
                            {comparison.baselineRunId === runId ? "Baseline" : "Candidate"}{" "}
                            counterpart:{" "}
                            <span className="break-all font-mono text-xs text-foreground">
                              {comparison.baselineRunId === runId
                                ? comparison.candidateRunId
                                : comparison.baselineRunId}
                            </span>
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <Badge tone="muted">{comparison.dataset ?? "Multiple datasets"}</Badge>
                          <Badge tone={comparison.compatible ? "accent" : "default"}>
                            {comparison.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </aside>
      </div>

      <section
        id="run-detail-evidence"
        ref={setSectionRef("evidence")}
        data-section-id="evidence"
        aria-label="Case inspection"
        className={cn(
          "space-y-3 scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
          highlightedSectionId === "evidence"
            ? "border-primary/25 bg-primary/[0.035]"
            : "",
        )}
      >
        <div className="space-y-3">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Stage 5 · Selected evidence
            </p>
            <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
              Selected case evidence
            </h2>
            <p className="text-sm text-muted-foreground">
              Stay inside the run flow while you move between mismatches, notable examples, saved
              errors, and the full case set. The evidence panel is the destination.
            </p>
          </div>

          {landingNotice ? (
            <div className="rounded-[18px] border border-border/60 bg-background/75 px-4 py-3 text-sm text-muted-foreground">
              {landingNotice}
            </div>
          ) : null}

          <RunCaseLensTabs
            value={activeLens}
            counts={caseLensCounts}
            onValueChange={(lens) =>
              setSearchParams(
                buildRunDetailSearchParams(searchParams, {
                  section: "evidence",
                  lens,
                  caseId: null,
                }),
                {
                  replace: true,
                  state: location.state,
                },
              )
            }
          />
        </div>

        {visibleCases.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No cases match this lens.</CardTitle>
              <CardDescription>
                This run has no saved rows under the {activeLens} lens. Switch lenses to inspect
                other cases without leaving the route.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-[minmax(16rem,0.78fr)_minmax(0,1.22fr)] lg:items-start">
            <div>
              <RunCaseTable
                cases={visibleCases}
                selectedCaseId={selectedCaseId}
                onSelectCase={(caseId) =>
                  setSearchParams(
                    buildRunDetailSearchParams(searchParams, {
                      section: "evidence",
                      lens: activeLens,
                      caseId,
                    }),
                    {
                      replace: true,
                      state: location.state,
                    },
                  )
                }
              />
            </div>
            <div className="lg:sticky lg:top-24">
              <RunCaseDetailPanel caseRow={selectedCase} />
            </div>
          </div>
        )}
      </section>

      <Link className="text-sm font-semibold text-primary no-underline" to={returnHref}>
        Back to runs
      </Link>
    </section>
  );
}
