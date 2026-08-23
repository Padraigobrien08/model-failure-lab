import { X } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import {
  ConsoleButton,
  ConsoleInput,
  EmptyState,
  RouteHeader,
  SegmentedControl,
  StatusChip,
  TableHeadCell,
  RunIdText,
  formatPercent,
  formatTimestamp,
  rowActivationProps,
  runStatusTone,
  truncateRunId,
} from "@/components/console/primitives";
import type { RunInventoryItem } from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

const MAX_DATASET_SEGMENTS = 3;

function runStatusLabel(run: RunInventoryItem): string {
  if (run.executionErrorCount != null && run.executionErrorCount > 0) {
    return `${run.executionErrorCount} ${run.executionErrorCount === 1 ? "error" : "errors"}`;
  }
  return run.status;
}

export function RunsPage() {
  const context = useAppRouteContext();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [pairMessage, setPairMessage] = useState<string | null>(null);

  const q = searchParams.get("q") ?? "";
  const datasetFilter = searchParams.get("dataset") ?? "";
  const modelFilter = searchParams.get("model") ?? "";
  const statusFilter = searchParams.get("status") ?? "";

  const inventory = context.runInventoryState.inventory;
  const runs = useMemo(() => {
    const rows = inventory?.runs ?? [];
    return [...rows].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }, [inventory]);

  const datasetSegments = useMemo(() => {
    const counts = new Map<string, number>();
    for (const run of runs) {
      counts.set(run.dataset, (counts.get(run.dataset) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, MAX_DATASET_SEGMENTS)
      .map(([dataset]) => dataset);
  }, [runs]);

  const filtered = runs.filter(
    (run) =>
      (!q || run.runId.includes(q)) &&
      (!datasetFilter || run.dataset === datasetFilter) &&
      (!modelFilter || run.model === modelFilter) &&
      (!statusFilter || run.status === statusFilter),
  );

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next, { replace: true });
  };

  const toggleSelected = (runId: string) => {
    setPairMessage(null);
    setSelectedRunIds((current) => {
      if (current.includes(runId)) return current.filter((id) => id !== runId);
      if (current.length >= 2) return [current[1], runId];
      return [...current, runId];
    });
  };

  const selectedRuns = selectedRunIds
    .map((id) => runs.find((run) => run.runId === id))
    .filter((run): run is RunInventoryItem => Boolean(run));
  const orderedPair =
    selectedRuns.length === 2
      ? [...selectedRuns].sort((a, b) => a.createdAt.localeCompare(b.createdAt))
      : null;

  const buildComparison = () => {
    if (!orderedPair) return;
    const [baseline, candidate] = orderedPair;
    const match = context.comparisonInventoryState.inventory?.comparisons.find(
      (comparison) =>
        (comparison.baselineRunId === baseline.runId &&
          comparison.candidateRunId === candidate.runId) ||
        (comparison.baselineRunId === candidate.runId &&
          comparison.candidateRunId === baseline.runId),
    );
    if (match) {
      navigate(`/comparisons/${encodeURIComponent(match.reportId)}`);
      return;
    }
    setPairMessage(
      `no saved comparison for this pair · run: failure-lab compare ${baseline.runId} ${candidate.runId}`,
    );
  };

  const runsPath = context.artifactOverview?.source.runsPath ?? "runs/";
  const isLoading =
    context.runInventoryState.status === "loading" ||
    context.runInventoryState.status === "idle";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <RouteHeader
        eyebrow="Inventory"
        title="Saved runs"
        actions={
          <ConsoleButton
            onClick={buildComparison}
            disabled={selectedRuns.length !== 2}
            variant="secondary"
          >
            Compare selected
          </ConsoleButton>
        }
      />

      <div className="flex items-center gap-[9px] border-b border-line bg-panel px-7 py-[11px]">
        <ConsoleInput
          aria-label="Filter runs by id"
          placeholder="run id contains…"
          value={q}
          onChange={(event) => setParam("q", event.target.value)}
          className="w-60"
        />
        {datasetSegments.length > 0 ? (
          <SegmentedControl
            aria-label="Filter by dataset"
            options={[
              { value: "", label: "All datasets" },
              ...datasetSegments.map((dataset) => ({
                value: dataset,
                label: dataset.replace(/[-_]failures[-_]v\d+$/, "").replace(/[-_]v\d+$/, ""),
              })),
            ]}
            value={datasetSegments.includes(datasetFilter) ? datasetFilter : ""}
            onChange={(value) => setParam("dataset", value)}
          />
        ) : null}
        {modelFilter ? (
          <button
            type="button"
            onClick={() => setParam("model", "")}
            className="inline-flex cursor-pointer items-center gap-2 rounded-tok border border-line bg-transparent px-[11px] py-[5px] font-body text-[12px] font-medium text-ink"
          >
            model: <span className="font-mono">{modelFilter}</span>
            <span className="text-muted-ink"><X size={12} strokeWidth={1.5} aria-hidden="true" /></span>
          </button>
        ) : null}
        {statusFilter ? (
          <button
            type="button"
            onClick={() => setParam("status", "")}
            className="inline-flex cursor-pointer items-center gap-2 rounded-tok border border-line bg-transparent px-[11px] py-[5px] font-body text-[12px] font-medium text-ink"
          >
            status: <span className="font-mono">{statusFilter}</span>
            <span className="text-muted-ink"><X size={12} strokeWidth={1.5} aria-hidden="true" /></span>
          </button>
        ) : null}
        <span className="ml-auto text-[12px] text-muted-ink">
          {filtered.length} {filtered.length === 1 ? "run" : "runs"} · newest first
        </span>
      </div>

      <div className="flex-1 overflow-auto px-7 pb-[22px]">
        {isLoading ? (
          <div aria-label="Loading runs" className="mt-4 flex flex-col gap-2">
            {[0, 1, 2, 3].map((row) => (
              <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
            ))}
          </div>
        ) : context.runInventoryState.status === "incompatible" ? (
          <EmptyState
            title="Run inventory failed to load."
            detail={context.runInventoryState.message}
            action={<ConsoleButton onClick={context.reloadRunInventory}>Retry</ConsoleButton>}
          />
        ) : runs.length === 0 ? (
          <EmptyState
            title="No saved runs."
            detail={`read ${runsPath} · run: failure-lab run <dataset> --model <model>`}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No runs match the current filters."
            detail={
              q
                ? `clear the run id filter "${q}"`
                : datasetFilter
                  ? `clear the dataset filter "${datasetFilter}"`
                  : modelFilter
                    ? `clear the model filter "${modelFilter}"`
                    : `clear the status filter "${statusFilter}"`
            }
            action={
              <ConsoleButton onClick={() => setSearchParams({}, { replace: true })}>
                Clear filters
              </ConsoleButton>
            }
          />
        ) : (
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr className="border-b border-line">
                <TableHeadCell className="w-7" />
                <TableHeadCell>Run id</TableHeadCell>
                <TableHeadCell>Dataset</TableHeadCell>
                <TableHeadCell>Model</TableHeadCell>
                <TableHeadCell align="right">Cases</TableHeadCell>
                <TableHeadCell align="right">Failure rate</TableHeadCell>
                <TableHeadCell align="right">Coverage</TableHeadCell>
                <TableHeadCell>Saved at</TableHeadCell>
                <TableHeadCell>Status</TableHeadCell>
                <TableHeadCell />
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {filtered.map((run, index) => {
                const selected = selectedRunIds.includes(run.runId);
                return (
                  <tr
                    key={run.runId}
                    {...rowActivationProps(() =>
                      navigate(`/runs/${encodeURIComponent(run.runId)}`),
                    )}
                    className={cn(
                      "cursor-pointer hover:bg-accent-wash",
                      index < filtered.length - 1 && "border-b border-line-soft",
                      selected && "bg-accent-wash",
                    )}
                  >
                    <td className="px-2 py-[9px]">
                      <input
                        type="checkbox"
                        aria-label={`Select ${run.runId} for comparison`}
                        checked={selected}
                        onChange={() => toggleSelected(run.runId)}
                        onClick={(event) => event.stopPropagation()}
                        className="h-3 w-3 cursor-pointer accent-[var(--accent)]"
                      />
                    </td>
                    <td className="max-w-[420px] break-all px-2 py-[9px] font-semibold">
                      <RunIdText runId={run.runId} />
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">{run.dataset}</td>
                    <td className="px-2 py-[9px] text-muted-ink">{run.model}</td>
                    <td className="px-2 py-[9px] text-right text-muted-ink">
                      {run.attemptedCaseCount ?? "—"}
                    </td>
                    <td className="px-2 py-[9px] text-right text-muted-ink">
                      {formatPercent(run.failureRate)}
                    </td>
                    <td className="px-2 py-[9px] text-right text-muted-ink">
                      {formatPercent(run.classificationCoverage)}
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {formatTimestamp(run.createdAt)}
                    </td>
                    <td className="px-2 py-[9px]">
                      <StatusChip tone={runStatusTone(runStatusLabel(run))}>
                        {runStatusLabel(run)}
                      </StatusChip>
                    </td>
                    <td className="px-2 py-[9px] text-right font-body text-[12.5px] text-accent-text">
                      open →
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {orderedPair ? (
          <div className="mt-[22px] flex items-center gap-[18px] rounded-tok border border-line bg-panel px-4 py-[14px]">
            <div className="font-heading text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-ink">
              2 selected
            </div>
            <div className="font-mono text-[12px]">
              {truncateRunId(orderedPair[0].runId)} <span className="text-muted-ink">→</span>{" "}
              {truncateRunId(orderedPair[1].runId)}
            </div>
            <span className="font-mono text-[11px] text-muted-ink">
              {orderedPair[0].dataset === orderedPair[1].dataset
                ? `same dataset · ${orderedPair[0].dataset}`
                : "different datasets · comparison may be incompatible"}
            </span>
            {pairMessage ? (
              <span className="font-mono text-[11px] text-warn">{pairMessage}</span>
            ) : null}
            <ConsoleButton variant="primary" onClick={buildComparison} className="ml-auto">
              Build comparison
            </ConsoleButton>
          </div>
        ) : null}
      </div>
    </div>
  );
}
