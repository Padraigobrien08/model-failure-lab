import { useDeferredValue, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { RunInventoryFilters } from "@/components/runs/RunInventoryFilters";
import { RunInventoryTable } from "@/components/runs/RunInventoryTable";
import {
  buildArtifactReturnState,
  createSearchString,
} from "@/lib/artifacts/navigation";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { RunInventoryItem } from "@/lib/artifacts/types";

function compareRunsNewestFirst(left: RunInventoryItem, right: RunInventoryItem): number {
  const leftTime = Date.parse(left.createdAt);
  const rightTime = Date.parse(right.createdAt);

  if (!Number.isNaN(leftTime) && !Number.isNaN(rightTime) && leftTime !== rightTime) {
    return rightTime - leftTime;
  }

  if (left.createdAt !== right.createdAt) {
    return right.createdAt.localeCompare(left.createdAt);
  }

  return right.runId.localeCompare(left.runId);
}

const DEFAULT_SORT = "timestamp_desc";

function readFilterValue(searchParams: URLSearchParams, key: string): string {
  return searchParams.get(key) ?? "";
}

function readSort(searchParams: URLSearchParams): string {
  return searchParams.get("sort") === DEFAULT_SORT ? DEFAULT_SORT : DEFAULT_SORT;
}

function buildRunsSearchParams(
  current: URLSearchParams,
  patch: Partial<{
    q: string;
    dataset: string;
    model: string;
    status: string;
    sort: string;
  }>,
): URLSearchParams {
  const next = new URLSearchParams(current);

  for (const [key, value] of Object.entries(patch)) {
    if (value === undefined) {
      continue;
    }

    if (typeof value === "string" && value.trim().length > 0) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
  }

  const sort = next.get("sort");
  if (sort === null || sort.length === 0 || sort === DEFAULT_SORT) {
    next.delete("sort");
  }

  return next;
}

export function RunsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { artifactState, artifactOverview, runInventoryState } = useAppRouteContext();
  const query = readFilterValue(searchParams, "q");
  const datasetFilter = readFilterValue(searchParams, "dataset");
  const modelFilter = readFilterValue(searchParams, "model");
  const statusFilter = readFilterValue(searchParams, "status");
  const sort = readSort(searchParams);
  const deferredQuery = useDeferredValue(query);
  const inventory = runInventoryState.status === "ready" ? runInventoryState.inventory : null;
  const runs = inventory?.runs ?? [];

  const datasetOptions = useMemo(
    () =>
      Array.from(new Set(runs.map((run) => run.dataset))).sort((left, right) =>
        left.localeCompare(right),
      ),
    [runs],
  );
  const modelOptions = useMemo(
    () =>
      Array.from(new Set(runs.map((run) => run.model))).sort((left, right) =>
        left.localeCompare(right),
      ),
    [runs],
  );
  const statusOptions = useMemo(
    () =>
      Array.from(new Set(runs.map((run) => run.status))).sort((left, right) =>
        left.localeCompare(right),
      ),
    [runs],
  );
  const filteredRuns = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();

    return runs
      .filter((run) => {
        if (normalizedQuery && !run.runId.toLowerCase().includes(normalizedQuery)) {
          return false;
        }
        if (datasetFilter && run.dataset !== datasetFilter) {
          return false;
        }
        if (modelFilter && run.model !== modelFilter) {
          return false;
        }
        if (statusFilter && run.status !== statusFilter) {
          return false;
        }
        return true;
      })
      .slice()
      .sort((left, right) => {
        if (sort === DEFAULT_SORT) {
          return compareRunsNewestFirst(left, right);
        }
        return compareRunsNewestFirst(left, right);
      });
  }, [datasetFilter, deferredQuery, modelFilter, runs, sort, statusFilter]);

  if (artifactState.status !== "ready" || artifactOverview === null) {
    return <ArtifactStatePanel area="Runs" state={artifactState} />;
  }

  const readyOverview = artifactOverview;
  if (runInventoryState.status === "idle" || runInventoryState.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Runs</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading saved runs inventory.</CardTitle>
            <CardDescription>
              The shell is resolving the browser-facing runs index from the active artifact root.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (runInventoryState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Runs</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The runs inventory could not be read.</CardTitle>
            <CardDescription>
              The shell found a runs source, but the saved artifacts do not match the supported
              inventory contract.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {runInventoryState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  if (inventory === null || inventory.runs.length === 0) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Runs</Badge>
        <Card>
          <CardHeader>
            <CardTitle>No saved runs are available yet.</CardTitle>
            <CardDescription>
              The shell is reading the right artifact root, but there are no
              `runs/&lt;run_id&gt;` directories to index yet.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p className="font-mono text-foreground">{readyOverview.source.runsPath}</p>
            <p>
              Generate a run with `failure-lab demo` or `failure-lab run` to populate the
              inventory.
            </p>
          </CardContent>
        </Card>
      </section>
    );
  }

  const readyInventory = inventory;

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Runs</Badge>
          <Badge tone="muted">{readyInventory.runs.length} detected</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Saved runs inventory.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          The home route now reads real saved run artifacts from the engine contract and renders
          them as a dense inventory you can scan, narrow, and open.
        </p>
      </div>

      <RunInventoryFilters
        search={query}
        dataset={datasetFilter}
        model={modelFilter}
        status={statusFilter}
        datasetOptions={datasetOptions}
        modelOptions={modelOptions}
        statusOptions={statusOptions}
        onSearchChange={(value) =>
          setSearchParams(buildRunsSearchParams(searchParams, { q: value, sort: DEFAULT_SORT }), {
            replace: true,
          })
        }
        onDatasetChange={(value) =>
          setSearchParams(
            buildRunsSearchParams(searchParams, { dataset: value, sort: DEFAULT_SORT }),
            { replace: true },
          )
        }
        onModelChange={(value) =>
          setSearchParams(buildRunsSearchParams(searchParams, { model: value, sort: DEFAULT_SORT }), {
            replace: true,
          })
        }
        onStatusChange={(value) =>
          setSearchParams(
            buildRunsSearchParams(searchParams, { status: value, sort: DEFAULT_SORT }),
            { replace: true },
          )
        }
        onClear={() => {
          setSearchParams(new URLSearchParams(), { replace: true });
        }}
      />

      {filteredRuns.length > 0 ? (
        <RunInventoryTable
          rows={filteredRuns}
          onOpenRun={(runId) =>
            navigate(`/runs/${encodeURIComponent(runId)}`, {
              state: buildArtifactReturnState("/", createSearchString(searchParams)),
            })
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>No runs match the current filters.</CardTitle>
            <CardDescription>
              Clear one or more filters to return to the full newest-first inventory.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </section>
  );
}
