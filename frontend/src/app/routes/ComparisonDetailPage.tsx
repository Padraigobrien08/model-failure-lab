import { startTransition, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

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
import { resolveArtifactReturnHref } from "@/lib/artifacts/navigation";
import { loadComparisonDetail } from "@/lib/artifacts/load";
import type {
  ComparisonCaseDeltaRecord,
  ComparisonDetailState,
} from "@/lib/artifacts/types";

function selectCasesByOrder(
  orderedCaseIds: string[],
  cases: ComparisonCaseDeltaRecord[],
): ComparisonCaseDeltaRecord[] {
  const caseMap = new Map(cases.map((caseRow) => [caseRow.caseId, caseRow]));
  return orderedCaseIds
    .map((caseId) => caseMap.get(caseId))
    .filter((caseRow): caseRow is ComparisonCaseDeltaRecord => caseRow !== undefined);
}

export function ComparisonDetailPage() {
  const { reportId } = useParams();
  const location = useLocation();
  const { artifactState, comparisonInventoryState } = useAppRouteContext();
  const [detailState, setDetailState] = useState<ComparisonDetailState>({
    status: "idle",
    detail: null,
    message: null,
  });
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  const inventory =
    comparisonInventoryState.status === "ready" ? comparisonInventoryState.inventory : null;
  const comparison = inventory?.comparisons.find((item) => item.reportId === reportId);
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
        setSelectedCaseId(null);
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

  const selectedCase = useMemo(() => {
    if (selectedCaseId === null) {
      return null;
    }

    return orderedCases.find((caseRow) => caseRow.caseId === selectedCaseId) ?? null;
  }, [orderedCases, selectedCaseId]);

  useEffect(() => {
    if (detailState.status !== "ready") {
      startTransition(() => {
        setSelectedCaseId(null);
      });
      return;
    }

    startTransition(() => {
      setSelectedCaseId((current) => {
        if (orderedCases.length === 0) {
          return null;
        }

        if (current && orderedCases.some((caseRow) => caseRow.caseId === current)) {
          return current;
        }

        return orderedCases[0]?.caseId ?? null;
      });
    });
  }, [detailState.status, orderedCases]);

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

  return (
    <section className="space-y-8">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(18rem,0.7fr)] xl:items-start">
        <div className="space-y-8">
          <ComparisonDetailHeader comparison={detail.comparison} inventoryHref={returnHref} />

          <ComparisonDeltaStrip
            metrics={detail.metrics}
            compatible={detail.comparison.compatible}
          />

          <ComparisonCoverageSummary
            comparison={detail.comparison}
            coverage={detail.coverage}
          />
        </div>

        <aside className="space-y-4 xl:sticky xl:top-28">
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
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Open baseline
                  </p>
                  <p className="mt-2 text-sm font-semibold text-foreground">
                    {detail.comparison.baselineRunId}
                  </p>
                </Link>
                <Link
                  className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3 text-inherit no-underline transition-colors hover:bg-background"
                  to={`/runs/${encodeURIComponent(detail.comparison.candidateRunId)}`}
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Open candidate
                  </p>
                  <p className="mt-2 text-sm font-semibold text-foreground">
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

      <section className="space-y-4" aria-label="Case transitions">
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

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(22rem,0.9fr)] lg:items-start">
          <ComparisonTransitionGroups
            summary={detail.transitions.summary}
            caseDeltas={detail.caseDeltas}
            selectedCaseId={selectedCaseId}
            onSelectCase={setSelectedCaseId}
          />
          <div className="lg:sticky lg:top-6">
            <ComparisonCaseDetailPanel caseDelta={selectedCase} />
          </div>
        </div>
      </section>

      <Link className="text-sm font-semibold text-primary no-underline" to={returnHref}>
        Back to comparisons
      </Link>
    </section>
  );
}
