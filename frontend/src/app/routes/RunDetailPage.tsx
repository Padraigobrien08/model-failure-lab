import { startTransition, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
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
import { loadRunDetail } from "@/lib/artifacts/load";
import type { RunCaseRecord, RunDetailState } from "@/lib/artifacts/types";

function selectCasesById(caseIds: string[], cases: RunCaseRecord[]): RunCaseRecord[] {
  const caseMap = new Map(cases.map((caseRow) => [caseRow.caseId, caseRow]));
  return caseIds
    .map((caseId) => caseMap.get(caseId))
    .filter((caseRow): caseRow is RunCaseRecord => caseRow !== undefined);
}

export function RunDetailPage() {
  const { runId } = useParams();
  const { artifactState, runInventoryState } = useAppRouteContext();
  const [detailState, setDetailState] = useState<RunDetailState>({
    status: "idle",
    detail: null,
    message: null,
  });
  const inventory = runInventoryState.status === "ready" ? runInventoryState.inventory : null;
  const run = inventory?.runs.find((item) => item.runId === runId);

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

  const notableCases = useMemo(() => {
    if (detailState.status !== "ready") {
      return [];
    }
    return selectCasesById(
      detailState.detail.lenses.notableCaseIds,
      detailState.detail.cases,
    ).slice(0, 3);
  }, [detailState]);

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
            <Link className="text-sm font-semibold text-primary no-underline" to="/">
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

  const detail = detailState.detail;

  return (
    <section className="space-y-8">
      <RunDetailHeader
        runId={detail.run.runId}
        dataset={detail.run.dataset}
        model={detail.run.model}
        status={detail.run.status}
        createdAt={detail.run.createdAt}
      />

      <RunSummaryMetricStrip metrics={detail.metrics} />

      <RunSummarySections
        failureTypes={detail.summary.failureTypes}
        expectationVerdicts={detail.summary.expectationVerdicts}
        tagSlices={detail.summary.tagSlices}
      />

      <RunNotableCases cases={notableCases} />

      <section className="space-y-3" aria-label="Case inspection">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Inspection
          </p>
          <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
            Case inspection
          </h2>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Case lenses land next in this phase.</CardTitle>
            <CardDescription>
              The summary-first page is now live. The next plan adds mismatches-first case tabs and
              in-page selected-case drilldown without leaving this route.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>

      <Link className="text-sm font-semibold text-primary no-underline" to="/">
        Back to runs
      </Link>
    </section>
  );
}
