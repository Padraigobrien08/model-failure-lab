import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

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
          The comparisons route reads saved baseline-to-candidate reports from the engine contract
          and renders them as a dense newest-first inventory you can scan and open.
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
