import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { ComparisonInventoryTable } from "@/components/comparisons/ComparisonInventoryTable";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ComparisonInventoryItem } from "@/lib/artifacts/types";

function compareComparisonsNewestFirst(
  left: ComparisonInventoryItem,
  right: ComparisonInventoryItem,
): number {
  const leftTime = Date.parse(left.createdAt);
  const rightTime = Date.parse(right.createdAt);

  if (!Number.isNaN(leftTime) && !Number.isNaN(rightTime) && leftTime !== rightTime) {
    return rightTime - leftTime;
  }

  if (left.createdAt !== right.createdAt) {
    return right.createdAt.localeCompare(left.createdAt);
  }

  return right.reportId.localeCompare(left.reportId);
}

export function ComparisonsPage() {
  const navigate = useNavigate();
  const { reportId } = useParams();
  const { artifactState, artifactOverview, comparisonInventoryState } = useAppRouteContext();

  const inventory =
    comparisonInventoryState.status === "ready" ? comparisonInventoryState.inventory : null;
  const comparisons = inventory?.comparisons ?? [];
  const sortedComparisons = useMemo(
    () => comparisons.slice().sort(compareComparisonsNewestFirst),
    [comparisons],
  );

  if (artifactState.status !== "ready" || artifactOverview === null) {
    return <ArtifactStatePanel area="Comparisons" state={artifactState} />;
  }

  const readyOverview = artifactOverview;

  if (
    comparisonInventoryState.status === "idle" ||
    comparisonInventoryState.status === "loading"
  ) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Comparisons</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading saved comparisons inventory.</CardTitle>
            <CardDescription>
              The shell is resolving the browser-facing comparison index from the default local
              artifact root.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (comparisonInventoryState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Comparisons</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The comparisons inventory could not be read.</CardTitle>
            <CardDescription>
              The shell found report artifacts, but the saved comparison inventory does not match
              the supported contract.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {comparisonInventoryState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  if (inventory === null || inventory.comparisons.length === 0) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Comparisons</Badge>
        <Card>
          <CardHeader>
            <CardTitle>No comparison reports are available yet.</CardTitle>
            <CardDescription>
              The shell is reading the right artifact root, but there are no saved comparison
              reports to index yet.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p className="font-mono text-foreground">{readyOverview.source.reportsPath}</p>
            <p>Generate a comparison with `failure-lab compare` to populate the inventory.</p>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (reportId) {
    const selectedComparison = inventory.comparisons.find((item) => item.reportId === reportId);
    if (!selectedComparison) {
      return (
        <section className="space-y-4">
          <Badge tone="default">Comparisons</Badge>
          <Card>
            <CardHeader>
              <CardTitle>Comparison not found.</CardTitle>
              <CardDescription>
                The requested comparison id is not present in the active inventory.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link className="text-sm font-semibold text-primary no-underline" to="/comparisons">
                Back to comparisons
              </Link>
            </CardContent>
          </Card>
        </section>
      );
    }

    return (
      <section className="space-y-6">
        <header className="space-y-4 border-b border-border/60 pb-5">
          <nav
            aria-label="Comparison breadcrumb"
            className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
          >
            <Link className="font-semibold text-foreground no-underline" to="/comparisons">
              Comparisons
            </Link>
            <span aria-hidden="true">/</span>
            <span className="font-mono text-xs text-foreground">{selectedComparison.reportId}</span>
          </nav>

          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <Badge tone="accent">Comparison detail</Badge>
              <Badge tone="muted">{selectedComparison.baselineRunId}</Badge>
              <Badge tone="muted">{selectedComparison.candidateRunId}</Badge>
            </div>
            <div className="space-y-1">
              <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
                {selectedComparison.reportId}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-muted-foreground">
                The dedicated comparison route handoff is now live. The full summary-first explorer
                lands next in this phase.
              </p>
            </div>
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Selected comparison route is ready.</CardTitle>
            <CardDescription>
              The inventory now opens one dedicated comparison route per saved report instead of
              keeping analysis trapped in the top-level list.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>
              Baseline <span className="font-mono text-foreground">{selectedComparison.baselineRunId}</span>
            </p>
            <p>
              Candidate <span className="font-mono text-foreground">{selectedComparison.candidateRunId}</span>
            </p>
            <Link className="text-sm font-semibold text-primary no-underline" to="/comparisons">
              Back to comparisons
            </Link>
          </CardContent>
        </Card>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Comparisons</Badge>
          <Badge tone="muted">{sortedComparisons.length} detected</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Saved comparisons inventory.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          The comparisons route now reads saved baseline-to-candidate reports from the engine
          contract and renders them as a dense newest-first inventory you can scan and open.
        </p>
      </div>

      <ComparisonInventoryTable
        rows={sortedComparisons}
        onOpenComparison={(selectedReportId) =>
          navigate(`/comparisons/${encodeURIComponent(selectedReportId)}`)
        }
      />
    </section>
  );
}
