import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useParams, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { ComparisonCaseDetailPanel } from "@/components/comparisons/ComparisonCaseDetailPanel";
import { ComparisonCoverageSummary } from "@/components/comparisons/ComparisonCoverageSummary";
import { ComparisonDeltaStrip } from "@/components/comparisons/ComparisonDeltaStrip";
import { ComparisonDetailHeader } from "@/components/comparisons/ComparisonDetailHeader";
import { ComparisonTransitionGroups } from "@/components/comparisons/ComparisonTransitionGroups";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  buildComparisonDetailSearchParams,
  buildRunDetailSearchParams,
  COMPARISON_DETAIL_SECTIONS,
  parseComparisonDetailSearch,
  resolveComparisonCaseForTransition,
  resolveComparisonDetailSection,
  searchParamsEqual,
  type ComparisonDetailSectionKey,
} from "@/lib/artifacts/detailRouteState";
import { createSearchString, resolveArtifactReturnHref } from "@/lib/artifacts/navigation";
import { loadComparisonDetail } from "@/lib/artifacts/load";
import type {
  ComparisonCaseDeltaRecord,
  ComparisonDetailState,
} from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

function selectCasesByOrder(
  orderedCaseIds: string[],
  cases: ComparisonCaseDeltaRecord[],
): ComparisonCaseDeltaRecord[] {
  const caseMap = new Map(cases.map((caseRow) => [caseRow.caseId, caseRow]));
  return orderedCaseIds
    .map((caseId) => caseMap.get(caseId))
    .filter((caseRow): caseRow is ComparisonCaseDeltaRecord => caseRow !== undefined);
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

function buildRunCaseDrillthroughHref(runId: string, caseId: string): string {
  const search = buildRunDetailSearchParams(new URLSearchParams(), {
    section: "evidence",
    caseId,
    lens: null,
  });

  return `/runs/${encodeURIComponent(runId)}${createSearchString(search)}`;
}

export function ComparisonDetailPage() {
  const { reportId } = useParams();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { artifactState, comparisonInventoryState, runInventoryState } =
    useAppRouteContext();
  const [detailState, setDetailState] = useState<ComparisonDetailState>({
    status: "idle",
    detail: null,
    message: null,
  });

  const inventory =
    comparisonInventoryState.status === "ready" ? comparisonInventoryState.inventory : null;
  const comparison = inventory?.comparisons.find((item) => item.reportId === reportId);
  const requestedState = useMemo(
    () => parseComparisonDetailSearch(searchParams),
    [searchParams],
  );
  const returnHref = useMemo(
    () => resolveArtifactReturnHref(location.state, "/comparisons"),
    [location.state],
  );

  useEffect(() => {
    if (!reportId || comparison === undefined) {
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

    void loadComparisonDetail(reportId)
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
          error instanceof Error ? error.message : "Failed to load comparison detail";
        startTransition(() => {
          setDetailState({
            status: "incompatible",
            detail: null,
            message,
          });
        });
      });
  }, [comparison, reportId]);

  const orderedCases = useMemo(() => {
    if (detailState.status !== "ready") {
      return [];
    }

    const orderedIds = detailState.detail.transitions.summary.flatMap((row) => row.caseIds);
    return selectCasesByOrder(orderedIds, detailState.detail.caseDeltas);
  }, [detailState]);

  const resolvedSelection = useMemo(() => {
    if (detailState.status !== "ready") {
      return {
        caseId: null as string | null,
        transition: null as string | null,
      };
    }

    const caseMap = new Map(
      detailState.detail.caseDeltas.map((caseRow) => [caseRow.caseId, caseRow]),
    );
    const requestedCase =
      requestedState.caseId !== null ? caseMap.get(requestedState.caseId) ?? null : null;
    const requestedTransitionCase = resolveComparisonCaseForTransition(
      detailState.detail.transitions.summary,
      detailState.detail.caseDeltas,
      requestedState.transition,
    );

    if (requestedCase) {
      if (
        requestedState.transition === null ||
        requestedCase.transitionType === requestedState.transition
      ) {
        return {
          caseId: requestedCase.caseId,
          transition: requestedCase.transitionType,
        };
      }

      if (requestedTransitionCase) {
        return {
          caseId: requestedTransitionCase.caseId,
          transition: requestedTransitionCase.transitionType,
        };
      }
    }

    if (requestedTransitionCase) {
      return {
        caseId: requestedTransitionCase.caseId,
        transition: requestedTransitionCase.transitionType,
      };
    }

    return {
      caseId: orderedCases[0]?.caseId ?? null,
      transition: orderedCases[0]?.transitionType ?? null,
    };
  }, [detailState, orderedCases, requestedState.caseId, requestedState.transition]);

  const selectedCase = useMemo(() => {
    if (resolvedSelection.caseId === null) {
      return null;
    }

    return orderedCases.find((caseRow) => caseRow.caseId === resolvedSelection.caseId) ?? null;
  }, [orderedCases, resolvedSelection.caseId]);

  const selectedCaseId = resolvedSelection.caseId;

  const resolvedSection = useMemo(
    () =>
      resolveComparisonDetailSection(
        requestedState.section,
        requestedState.caseId,
        requestedState.transition,
      ),
    [requestedState.caseId, requestedState.section, requestedState.transition],
  );
  const [activeSectionId, setActiveSectionId] =
    useState<ComparisonDetailSectionKey>(resolvedSection);
  const [highlightedSectionId, setHighlightedSectionId] =
    useState<ComparisonDetailSectionKey | null>(null);
  const [highlightedTransitionType, setHighlightedTransitionType] = useState<string | null>(
    null,
  );
  const [landingNotice, setLandingNotice] = useState<string | null>(null);
  const sectionRefs = useRef<Record<ComparisonDetailSectionKey, HTMLElement | null>>({
    framing: null,
    coverage: null,
    transitions: null,
  });
  const groupRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const setSectionRef =
    (sectionId: ComparisonDetailSectionKey) => (element: HTMLElement | null) => {
      sectionRefs.current[sectionId] = element;
    };
  const setGroupRef = (transitionType: string) => (element: HTMLDivElement | null) => {
    groupRefs.current[transitionType] = element;
  };

  const resolvedLandingNotice = useMemo(() => {
    const notices: string[] = [];

    if (
      requestedState.transition !== null &&
      requestedState.transition !== resolvedSelection.transition
    ) {
      notices.push(
        `Requested transition ${requestedState.transition} is unavailable. Showing ${resolvedSelection.transition ?? "the nearest available transition section"} instead.`,
      );
    }

    if (requestedState.caseId !== null && requestedState.caseId !== resolvedSelection.caseId) {
      notices.push(
        resolvedSelection.caseId
          ? `Requested case ${requestedState.caseId} is unavailable in this transition context. Showing ${resolvedSelection.caseId} instead.`
          : `Requested case ${requestedState.caseId} is unavailable in this transition context.`,
      );
    }

    return notices.length > 0 ? notices.join(" ") : null;
  }, [
    requestedState.caseId,
    requestedState.transition,
    resolvedSelection.caseId,
    resolvedSelection.transition,
  ]);

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

  useEffect(() => {
    if (detailState.status !== "ready") {
      return;
    }

    const nextSearchParams = buildComparisonDetailSearchParams(searchParams, {
      section: resolvedSection,
      caseId: resolvedSelection.caseId,
      transition: resolvedSelection.transition,
    });

    if (searchParamsEqual(searchParams, nextSearchParams)) {
      return;
    }

    setSearchParams(nextSearchParams, {
      replace: true,
      state: location.state,
    });
  }, [
    detailState.status,
    location.state,
    resolvedSection,
    resolvedSelection.caseId,
    resolvedSelection.transition,
    searchParams,
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
        const observedSection =
          resolveObservedSection<ComparisonDetailSectionKey>(entries);
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

    const transitionTarget =
      resolvedSection === "transitions" && resolvedSelection.transition
        ? groupRefs.current[resolvedSelection.transition] ?? null
        : null;
    const targetElement = transitionTarget ?? sectionRefs.current[resolvedSection];
    if (!targetElement) {
      return;
    }

    const animationFrame = window.requestAnimationFrame(() => {
      if (typeof targetElement.scrollIntoView === "function") {
        targetElement.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }

      setActiveSectionId(resolvedSection);
      setHighlightedSectionId(resolvedSection);
      setHighlightedTransitionType(transitionTarget ? resolvedSelection.transition : null);
    });

    const timeout = window.setTimeout(() => {
      setHighlightedSectionId((current) =>
        current === resolvedSection ? null : current,
      );
      setHighlightedTransitionType((current) =>
        current === resolvedSelection.transition ? null : current,
      );
    }, 1800);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.clearTimeout(timeout);
    };
  }, [
    detailState.status,
    resolvedSection,
    resolvedSelection.caseId,
    resolvedSelection.transition,
  ]);

  if (artifactState.status !== "ready") {
    return <ArtifactStatePanel area="Comparisons" state={artifactState} />;
  }

  if (
    comparisonInventoryState.status === "idle" ||
    comparisonInventoryState.status === "loading"
  ) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Comparison detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading selected comparison.</CardTitle>
            <CardDescription>
              The comparisons route is resolving the saved comparison detail payload from the
              default local artifact root.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (comparisonInventoryState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Comparison detail</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The selected comparison could not be resolved.</CardTitle>
            <CardDescription>
              The comparisons inventory is not available under the supported artifact contract.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {comparisonInventoryState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  if (inventory === null || !reportId) {
    return null;
  }

  if (comparison === undefined) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Comparison detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Comparison not found.</CardTitle>
            <CardDescription>
              The requested comparison id is not present in the active inventory.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link className="text-sm font-semibold text-primary no-underline" to={returnHref}>
              Back to comparisons
            </Link>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (detailState.status === "idle" || detailState.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Comparison detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading comparison report detail.</CardTitle>
            <CardDescription>
              Reading `report.json` and `report_details.json` for {comparison.reportId}.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (detailState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Comparison detail</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The saved comparison detail could not be loaded.</CardTitle>
            <CardDescription>
              The selected comparison exists in the inventory, but its saved detail artifacts do
              not match the supported contract.
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
  const detailReturnState = {
    returnTo: {
      pathname: location.pathname,
      search: location.search,
    },
  };
  const baselineUnavailableReason =
    runInventoryState.status === "incompatible"
      ? "Saved runs are unavailable under the active artifact contract."
      : runInventoryState.status === "ready" &&
          !runInventoryState.inventory.runs.some(
            (candidate) => candidate.runId === detail.comparison.baselineRunId,
          )
        ? `Saved baseline run ${detail.comparison.baselineRunId} is unavailable in the active run inventory.`
        : null;
  const candidateUnavailableReason =
    runInventoryState.status === "incompatible"
      ? "Saved runs are unavailable under the active artifact contract."
      : runInventoryState.status === "ready" &&
          !runInventoryState.inventory.runs.some(
            (candidate) => candidate.runId === detail.comparison.candidateRunId,
          )
        ? `Saved candidate run ${detail.comparison.candidateRunId} is unavailable in the active run inventory.`
        : null;
  const baselineCaseHref =
    selectedCase !== null
      ? buildRunCaseDrillthroughHref(
          detail.comparison.baselineRunId,
          selectedCase.caseId,
        )
      : null;
  const candidateCaseHref =
    selectedCase !== null
      ? buildRunCaseDrillthroughHref(
          detail.comparison.candidateRunId,
          selectedCase.caseId,
        )
      : null;

  return (
    <section className="space-y-8">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(18rem,0.7fr)] xl:items-start">
        <div className="min-w-0 space-y-8">
          <section
            id="comparison-detail-framing"
            ref={setSectionRef("framing")}
            data-section-id="framing"
            className={cn(
              "scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
              highlightedSectionId === "framing"
                ? "border-primary/25 bg-primary/[0.035]"
                : "",
            )}
          >
            <div className="space-y-8">
              <ComparisonDetailHeader
                comparison={detail.comparison}
                inventoryHref={returnHref}
                baselineRunState={detailReturnState}
                candidateRunState={detailReturnState}
              />

              <ComparisonDeltaStrip
                metrics={detail.metrics}
                compatible={detail.comparison.compatible}
              />
            </div>
          </section>

          <section
            id="comparison-detail-coverage"
            ref={setSectionRef("coverage")}
            data-section-id="coverage"
            className={cn(
              "scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
              highlightedSectionId === "coverage"
                ? "border-primary/25 bg-primary/[0.035]"
                : "",
            )}
          >
            <ComparisonCoverageSummary
              comparison={detail.comparison}
              coverage={detail.coverage}
            />
          </section>
        </div>

        <aside className="space-y-4 xl:sticky xl:top-28">
          <Card className="rounded-[24px] border border-border/70 bg-card/75">
            <CardHeader className="space-y-1 pb-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Section jumps
              </p>
              <CardTitle className="text-lg">Traverse comparison evidence</CardTitle>
              <CardDescription>
                Move between framing, shared-case scope, and grouped transition evidence without
                dropping the current selection.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {COMPARISON_DETAIL_SECTIONS.map((section, index) => (
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
                      buildComparisonDetailSearchParams(searchParams, {
                        section: section.id,
                        caseId: resolvedSelection.caseId,
                        transition: resolvedSelection.transition,
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
                Comparison context
              </p>
              <CardTitle className="text-lg">Keep the artifact graph visible</CardTitle>
              <CardDescription>
                Preserve the baseline/candidate lineage and scope while you inspect grouped
                transition evidence below.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3">
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
                      Compare mode
                    </p>
                    <p className="mt-2 text-sm text-foreground">
                      {detail.comparison.comparisonMode ?? "n/a"}
                    </p>
                  </div>
                  <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      Metrics scope
                    </p>
                    <p className="mt-2 text-sm text-foreground">
                      {detail.comparison.metricsComputedOn ?? "n/a"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <Link
                  className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3 text-inherit no-underline transition-colors hover:bg-background"
                  to={`/runs/${encodeURIComponent(detail.comparison.baselineRunId)}`}
                  state={detailReturnState}
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Open baseline
                  </p>
                  <p className="mt-2 break-all text-sm font-semibold text-foreground">
                    {detail.comparison.baselineRunId}
                  </p>
                </Link>
                <Link
                  className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3 text-inherit no-underline transition-colors hover:bg-background"
                  to={`/runs/${encodeURIComponent(detail.comparison.candidateRunId)}`}
                  state={detailReturnState}
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Open candidate
                  </p>
                  <p className="mt-2 break-all text-sm font-semibold text-foreground">
                    {detail.comparison.candidateRunId}
                  </p>
                </Link>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Shared cases
                  </p>
                  <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                    {detail.coverage.sharedCaseCount}
                  </p>
                </div>
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Baseline only
                  </p>
                  <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                    {detail.coverage.baselineOnlyCaseCount}
                  </p>
                </div>
                <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Candidate only
                  </p>
                  <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-foreground">
                    {detail.coverage.candidateOnlyCaseCount}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>

      <section
        id="comparison-detail-transitions"
        ref={setSectionRef("transitions")}
        data-section-id="transitions"
        aria-label="Case transitions"
        className={cn(
          "space-y-4 scroll-mt-28 rounded-[28px] border border-transparent transition-colors duration-300",
          highlightedSectionId === "transitions"
            ? "border-primary/25 bg-primary/[0.035]"
            : "",
        )}
      >
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Stage 3 · Transition evidence
          </p>
          <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
            Grouped case transitions
          </h2>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Follow the saved transition groups first, then inspect one changed case at a time
            without leaving this comparison route.
          </p>
        </div>

        {landingNotice ? (
          <div className="rounded-[18px] border border-border/60 bg-background/75 px-4 py-3 text-sm text-muted-foreground">
            {landingNotice}
          </div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(22rem,0.9fr)] lg:items-start">
          <ComparisonTransitionGroups
            summary={detail.transitions.summary}
            caseDeltas={detail.caseDeltas}
            selectedCaseId={selectedCaseId}
            highlightedTransitionType={highlightedTransitionType}
            setGroupRef={setGroupRef}
            onSelectCase={(caseId) => {
              const caseRow =
                detail.caseDeltas.find((candidate) => candidate.caseId === caseId) ?? null;
              setSearchParams(
                buildComparisonDetailSearchParams(searchParams, {
                  section: "transitions",
                  caseId,
                  transition: caseRow?.transitionType ?? null,
                }),
                {
                  replace: true,
                  state: location.state,
                },
              );
            }}
          />
          <div className="lg:sticky lg:top-6">
            <ComparisonCaseDetailPanel
              baselineAction={
                selectedCase
                  ? {
                      label: "Open baseline evidence",
                      ariaLabel: `Open case ${selectedCase.caseId} in baseline run ${detail.comparison.baselineRunId}`,
                      href: baselineUnavailableReason ? null : baselineCaseHref,
                      runId: detail.comparison.baselineRunId,
                      state: detailReturnState,
                      disabledReason: baselineUnavailableReason,
                    }
                  : null
              }
              candidateAction={
                selectedCase
                  ? {
                      label: "Open candidate evidence",
                      ariaLabel: `Open case ${selectedCase.caseId} in candidate run ${detail.comparison.candidateRunId}`,
                      href: candidateUnavailableReason ? null : candidateCaseHref,
                      runId: detail.comparison.candidateRunId,
                      state: detailReturnState,
                      disabledReason: candidateUnavailableReason,
                    }
                  : null
              }
              artifactContext={
                selectedCase
                  ? {
                      reportId: detail.comparison.reportId,
                      baselineRunId: detail.comparison.baselineRunId,
                      candidateRunId: detail.comparison.candidateRunId,
                      sourcePath: detail.source.path,
                    }
                  : null
              }
              caseDelta={selectedCase}
            />
          </div>
        </div>
      </section>

      <Link className="text-sm font-semibold text-primary no-underline" to={returnHref}>
        Back to comparisons
      </Link>
    </section>
  );
}
