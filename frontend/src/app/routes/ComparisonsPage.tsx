import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import {
  ConsoleButton,
  ConsoleInput,
  EmptyState,
  RouteHeader,
  StatusChip,
  TableHeadCell,
  formatScore,
  truncateRunId,
  formatTimestamp,
} from "@/components/console/primitives";
import type { ChipTone } from "@/components/console/primitives";
import { cn } from "@/lib/utils";

export function verdictTone(verdict: string): ChipTone {
  switch (verdict) {
    case "regression":
      return "bad";
    case "improvement":
      return "good";
    case "incompatible":
      return "warn";
    default:
      return "neutral";
  }
}

export function ComparisonsPage() {
  const context = useAppRouteContext();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";

  const comparisons = useMemo(() => {
    const rows = context.comparisonInventoryState.inventory?.comparisons ?? [];
    return [...rows].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }, [context.comparisonInventoryState.inventory]);

  const filtered = comparisons.filter(
    (comparison) =>
      !q ||
      comparison.reportId.includes(q) ||
      comparison.baselineRunId.includes(q) ||
      comparison.candidateRunId.includes(q),
  );

  const reportsPath = context.artifactOverview?.source.reportsPath ?? "reports/";
  const isLoading =
    context.comparisonInventoryState.status === "loading" ||
    context.comparisonInventoryState.status === "idle";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <RouteHeader eyebrow="Inventory" title="Comparisons" />

      <div className="flex items-center gap-[9px] border-b border-line bg-panel px-7 py-[11px]">
        <ConsoleInput
          aria-label="Filter comparisons by id"
          placeholder="report or run id contains…"
          value={q}
          onChange={(event) => {
            const next = new URLSearchParams(searchParams);
            if (event.target.value) {
              next.set("q", event.target.value);
            } else {
              next.delete("q");
            }
            setSearchParams(next, { replace: true });
          }}
          className="w-72"
        />
        <span className="ml-auto text-[12px] text-muted-ink">
          {filtered.length} {filtered.length === 1 ? "comparison" : "comparisons"} · newest first
        </span>
      </div>

      <div className="flex-1 overflow-auto px-7 pb-[22px]">
        {isLoading ? (
          <div aria-label="Loading comparisons" className="mt-4 flex flex-col gap-2">
            {[0, 1, 2].map((row) => (
              <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
            ))}
          </div>
        ) : context.comparisonInventoryState.status === "incompatible" ? (
          <EmptyState
            title="Comparison inventory failed to load."
            detail={context.comparisonInventoryState.message}
            action={
              <ConsoleButton onClick={context.reloadComparisonInventory}>Retry</ConsoleButton>
            }
          />
        ) : comparisons.length === 0 ? (
          <EmptyState
            title="No saved comparisons."
            detail={`read ${reportsPath} · run: failure-lab compare <baseline-run> <candidate-run>`}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No comparisons match the current filter."
            detail={`clear the id filter "${q}"`}
            action={
              <ConsoleButton onClick={() => setSearchParams({}, { replace: true })}>
                Clear filter
              </ConsoleButton>
            }
          />
        ) : (
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr className="border-b border-line">
                <TableHeadCell>Report id</TableHeadCell>
                <TableHeadCell>Dataset</TableHeadCell>
                <TableHeadCell>Baseline → candidate</TableHeadCell>
                <TableHeadCell>Verdict</TableHeadCell>
                <TableHeadCell align="right">Severity</TableHeadCell>
                <TableHeadCell align="right">Net score</TableHeadCell>
                <TableHeadCell>Top driver</TableHeadCell>
                <TableHeadCell>Saved at</TableHeadCell>
                <TableHeadCell />
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {filtered.map((comparison, index) => {
                const topDriver = comparison.topDrivers[0] ?? null;
                return (
                  <tr
                    key={comparison.reportId}
                    onClick={() =>
                      navigate(`/comparisons/${encodeURIComponent(comparison.reportId)}`)
                    }
                    className={cn(
                      "cursor-pointer hover:bg-accent-wash",
                      index < filtered.length - 1 && "border-b border-line-soft",
                    )}
                  >
                    <td className="px-2 py-[9px] font-semibold">{comparison.reportId}</td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {comparison.dataset ?? "—"}
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {truncateRunId(comparison.baselineRunId)} →{" "}
                      {truncateRunId(comparison.candidateRunId)}
                    </td>
                    <td className="px-2 py-[9px]">
                      <StatusChip tone={verdictTone(comparison.signalVerdict)}>
                        {comparison.signalVerdict}
                      </StatusChip>
                    </td>
                    <td
                      className={cn(
                        "px-2 py-[9px] text-right",
                        comparison.signalVerdict === "regression"
                          ? "font-semibold text-bad"
                          : "text-muted-ink",
                      )}
                    >
                      {formatScore(comparison.severity)}
                    </td>
                    <td className="px-2 py-[9px] text-right text-muted-ink">
                      {formatScore(comparison.netScore).replace("-", "−")}
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {topDriver ? topDriver.failureType : "—"}
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {formatTimestamp(comparison.createdAt)}
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
      </div>
    </div>
  );
}
