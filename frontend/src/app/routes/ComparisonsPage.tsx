import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { ComparisonInventoryTable } from "@/components/comparisons/ComparisonInventoryTable";
import {
  buildArtifactReturnState,
  createSearchString,
} from "@/lib/artifacts/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ComparisonInventoryItem } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonTriageLens = "all" | "actionable" | "critical" | "lifecycle";
type ComparisonOrder = "severity" | "priority" | "newest";

function compareComparisonsSeverityFirst(
  left: ComparisonInventoryItem,
  right: ComparisonInventoryItem,
): number {
  if (left.severity !== right.severity) {
    return right.severity - left.severity;
  }

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

function isActionableComparison(row: ComparisonInventoryItem): boolean {
  return row.governanceRecommendation?.action != null
    && row.governanceRecommendation.action !== "ignore";
}

function hasLifecycleFollowUp(row: ComparisonInventoryItem): boolean {
  const lifecycleAction =
    row.governanceRecommendation?.lifecycleRecommendation?.action
    ?? row.portfolioItem?.lifecycleAction
    ?? null;
  return lifecycleAction != null && lifecycleAction !== "keep";
}

function isCriticalComparison(row: ComparisonInventoryItem): boolean {
  return row.governanceRecommendation?.escalation?.status === "critical"
    || row.portfolioItem?.priorityBand === "urgent";
}

function compareComparisonsPriorityFirst(
  left: ComparisonInventoryItem,
  right: ComparisonInventoryItem,
): number {
  const leftRank = left.portfolioItem?.priorityRank ?? Number.MAX_SAFE_INTEGER;
  const rightRank = right.portfolioItem?.priorityRank ?? Number.MAX_SAFE_INTEGER;
  if (leftRank !== rightRank) {
    return leftRank - rightRank;
  }

  const leftActionable = isActionableComparison(left) ? 1 : 0;
  const rightActionable = isActionableComparison(right) ? 1 : 0;
  if (leftActionable !== rightActionable) {
    return rightActionable - leftActionable;
  }

  return compareComparisonsSeverityFirst(left, right);
}

function readTriageLens(searchParams: URLSearchParams): ComparisonTriageLens {
  const value = searchParams.get("triage");
  if (value === "actionable" || value === "critical" || value === "lifecycle") {
    return value;
  }
  return "all";
}

function readComparisonOrder(searchParams: URLSearchParams): ComparisonOrder {
  const value = searchParams.get("order");
  if (value === "priority" || value === "newest") {
    return value;
  }
  return "severity";
}

function buildComparisonsSearchParams(
  current: URLSearchParams,
  patch: Partial<Record<"triage" | "order", string>>,
): URLSearchParams {
  const next = new URLSearchParams(current);
  for (const [key, value] of Object.entries(patch)) {
    if (!value || value === "all" || value === "severity") {
      next.delete(key);
    } else {
      next.set(key, value);
    }
  }
  return next;
}

export function ComparisonsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { artifactState, artifactOverview, comparisonInventoryState } = useAppRouteContext();

  const inventory =
    comparisonInventoryState.status === "ready" ? comparisonInventoryState.inventory : null;
  const comparisons = inventory?.comparisons ?? [];
  const triageLens = readTriageLens(searchParams);
  const order = readComparisonOrder(searchParams);
  const actionableCount = useMemo(
    () => comparisons.filter(isActionableComparison).length,
    [comparisons],
  );
  const criticalCount = useMemo(
    () => comparisons.filter(isCriticalComparison).length,
    [comparisons],
  );
  const lifecycleCount = useMemo(
    () => comparisons.filter(hasLifecycleFollowUp).length,
    [comparisons],
  );
  const visibleComparisons = useMemo(
    () => {
      const filtered = comparisons.filter((row) => {
        if (triageLens === "actionable") {
          return isActionableComparison(row);
        }
        if (triageLens === "critical") {
          return isCriticalComparison(row);
        }
        if (triageLens === "lifecycle") {
          return hasLifecycleFollowUp(row);
        }
        return true;
      });

      const compare =
        order === "priority"
          ? compareComparisonsPriorityFirst
          : order === "newest"
            ? compareComparisonsNewestFirst
            : compareComparisonsSeverityFirst;

      return filtered.slice().sort(compare);
    },
    [comparisons, order, triageLens],
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
          <Badge tone="muted">{visibleComparisons.length} visible</Badge>
          <Badge tone="muted">{actionableCount} actionable</Badge>
          <Badge tone="muted">{criticalCount} critical</Badge>
          <Badge tone="muted">{lifecycleCount} lifecycle follow-up</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Saved comparisons inventory.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          The comparisons route reads saved baseline-to-candidate reports from the engine contract
          and now surfaces the operator context needed to triage what deserves attention before you
          open a report: recommendation, escalation, lifecycle posture, matched family, and
          portfolio priority.
        </p>
      </div>

      <Card className="border-border/70 bg-card/70">
        <CardHeader className="space-y-2">
          <CardTitle className="text-xl">Triage focus</CardTitle>
          <CardDescription>
            Move between all comparisons, immediately actionable items, critical escalations, and
            lifecycle follow-up without leaving the saved inventory.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {[
              { value: "all", label: "All comparisons" },
              { value: "actionable", label: "Actionable" },
              { value: "critical", label: "Critical" },
              { value: "lifecycle", label: "Lifecycle follow-up" },
            ].map((lens) => (
              <Button
                key={lens.value}
                variant={triageLens === lens.value ? "default" : "ghost"}
                size="sm"
                onClick={() =>
                  setSearchParams(
                    buildComparisonsSearchParams(searchParams, { triage: lens.value }),
                    { replace: true },
                  )
                }
              >
                {lens.label}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Order
            </span>
            {[
              { value: "severity", label: "Severity first" },
              { value: "priority", label: "Priority first" },
              { value: "newest", label: "Newest first" },
            ].map((option) => (
              <Button
                key={option.value}
                variant={order === option.value ? "default" : "ghost"}
                size="sm"
                onClick={() =>
                  setSearchParams(
                    buildComparisonsSearchParams(searchParams, { order: option.value }),
                    { replace: true },
                  )
                }
              >
                {option.label}
              </Button>
            ))}
            <Badge tone="muted">
              {formatLabel(triageLens === "all" ? "all" : triageLens)}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <ComparisonInventoryTable
        rows={visibleComparisons}
        onOpenComparison={(selectedReportId) =>
          navigate(`/comparisons/${encodeURIComponent(selectedReportId)}`, {
            state: buildArtifactReturnState(
              "/comparisons",
              createSearchString(searchParams),
            ),
          })
        }
      />
    </section>
  );
}
