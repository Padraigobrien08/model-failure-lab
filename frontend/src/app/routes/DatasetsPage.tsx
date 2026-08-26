import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import {
  ConsoleButton,
  ConsoleInput,
  EmptyState,
  RouteHeader,
  SectionLabel,
  StatusChip,
  TableHeadCell,
  formatPercent,
  formatTimestamp,
  rowActivationProps,
  truncateRunId,
} from "@/components/console/primitives";
import type { ChipTone } from "@/components/console/primitives";
import type { DatasetDraftsResponse } from "@/lib/artifacts/extended";
import { loadDatasetDrafts } from "@/lib/artifacts/extended";
import { cn } from "@/lib/utils";

export function healthTone(healthLabel: string | null): ChipTone {
  if (!healthLabel) return "neutral";
  const normalized = healthLabel.toLowerCase();
  if (normalized.includes("regress")) return "bad";
  if (normalized.includes("stale") || normalized.includes("overgrown")) return "warn";
  if (normalized.includes("healthy")) return "good";
  return "neutral";
}

type DraftsState =
  | { status: "loading"; data: null }
  | { status: "ready"; data: DatasetDraftsResponse }
  | { status: "failed"; data: null };

/** Harvested packs awaiting promotion — the step between a write and a family. */
function DraftsSection({ navigate }: { navigate: (to: string) => void }) {
  const [state, setState] = useState<DraftsState>({ status: "loading", data: null });

  useEffect(() => {
    let cancelled = false;
    void loadDatasetDrafts()
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "failed", data: null });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const drafts = state.status === "ready" ? state.data.drafts : [];

  return (
    <div className="mt-6 flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <SectionLabel>Drafts · awaiting promotion</SectionLabel>
        {state.status === "ready" ? (
          <span className="font-mono text-[11px] text-muted-ink">
            {drafts.length} {drafts.length === 1 ? "draft" : "drafts"} · datasets/harvested/
          </span>
        ) : null}
      </div>
      {state.status === "loading" ? (
        <div role="status" aria-label="Loading drafts" className="flex flex-col gap-2">
          <div className="h-9 animate-pulse rounded-tok bg-panel" />
        </div>
      ) : state.status === "failed" || drafts.length === 0 ? (
        <div className="rounded-tok border border-line bg-panel px-4 py-3 font-mono text-[11.5px] text-muted-ink">
          no drafts awaiting promotion · harvest one from a comparison or a run
        </div>
      ) : (
        <>
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr className="border-b border-line">
                <TableHeadCell>Draft id</TableHeadCell>
                <TableHeadCell align="right">Cases</TableHeadCell>
                <TableHeadCell>Source</TableHeadCell>
                <TableHeadCell>Suggested family</TableHeadCell>
                <TableHeadCell>Created</TableHeadCell>
                <TableHeadCell>Lifecycle</TableHeadCell>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {drafts.map((draft, index) => {
                const sourceHref = draft.comparisonReportId
                  ? `/comparisons/${encodeURIComponent(draft.comparisonReportId)}`
                  : draft.runId
                    ? `/runs/${encodeURIComponent(draft.runId)}`
                    : null;
                const sourceLabel = draft.comparisonReportId
                  ? truncateRunId(draft.comparisonReportId)
                  : draft.runId
                    ? truncateRunId(draft.runId)
                    : "—";
                return (
                  <tr
                    key={draft.datasetId}
                    className={cn(index < drafts.length - 1 && "border-b border-line-soft")}
                  >
                    <td className="max-w-[380px] break-all px-2 py-[9px] font-semibold">
                      {draft.datasetId}
                    </td>
                    <td className="px-2 py-[9px] text-right text-muted-ink">
                      {draft.caseCount}
                    </td>
                    <td className="px-2 py-[9px]">
                      {sourceHref ? (
                        <button
                          type="button"
                          onClick={() => navigate(sourceHref)}
                          className="cursor-pointer border-0 bg-transparent p-0 font-mono text-[12px] text-accent-text"
                        >
                          {sourceLabel}
                        </button>
                      ) : (
                        <span className="text-muted-ink">—</span>
                      )}
                      <span className="ml-1.5 text-[11px] text-muted-ink">
                        {draft.mode ?? ""}
                      </span>
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {draft.suggestedFamilyId ?? "—"}
                    </td>
                    <td className="px-2 py-[9px] text-muted-ink">
                      {draft.createdAt ? formatTimestamp(draft.createdAt) : "—"}
                    </td>
                    <td className="px-2 py-[9px]">
                      <StatusChip tone="neutral">{draft.lifecycle ?? "draft"}</StatusChip>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="font-mono text-[11px] text-muted-ink">
            promote: failure-lab dataset promote datasets/harvested/&lt;draft-id&gt;.json --dataset-id &lt;id&gt; ·
            records a content digest · promoting onto an existing version is refused
          </div>
        </>
      )}
    </div>
  );
}

export function DatasetsPage() {
  const context = useAppRouteContext();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";

  const families = useMemo(() => {
    const rows =
      context.datasetFamiliesState.status === "ready"
        ? context.datasetFamiliesState.data.families
        : [];
    return [...rows].sort((a, b) => a.familyId.localeCompare(b.familyId));
  }, [context.datasetFamiliesState]);

  const filtered = families.filter((family) => !q || family.familyId.includes(q));

  const isLoading =
    context.datasetFamiliesState.status === "loading" ||
    context.datasetFamiliesState.status === "idle";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <RouteHeader eyebrow="Inventory" title="Dataset families" />

      <div className="flex items-center gap-[9px] border-b border-line bg-panel px-7 py-[11px]">
        <ConsoleInput
          aria-label="Filter dataset families by id"
          placeholder="family id contains…"
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
          className="w-64"
        />
        <span className="ml-auto text-[12px] text-muted-ink">
          {filtered.length} {filtered.length === 1 ? "family" : "families"}
        </span>
      </div>

      <div className="flex-1 overflow-auto px-7 pb-[22px]">
        {isLoading ? (
          <div aria-label="Loading dataset families" className="mt-4 flex flex-col gap-2">
            {[0, 1, 2].map((row) => (
              <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
            ))}
          </div>
        ) : context.datasetFamiliesState.status === "incompatible" ? (
          <EmptyState
            title="Dataset families failed to load."
            detail={context.datasetFamiliesState.message}
            action={<ConsoleButton onClick={context.reloadDatasetFamilies}>Retry</ConsoleButton>}
          />
        ) : families.length === 0 ? (
          <EmptyState
            title="No dataset families."
            detail="read datasets/ · run: failure-lab harvest --comparison <comparison> --out datasets/harvested/<name>.json"
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No dataset families match the current filter."
            detail={`clear the family id filter "${q}"`}
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
                <TableHeadCell>Family id</TableHeadCell>
                <TableHeadCell align="right">Versions</TableHeadCell>
                <TableHeadCell>Latest version</TableHeadCell>
                <TableHeadCell align="right">Cases</TableHeadCell>
                <TableHeadCell>Primary failure type</TableHeadCell>
                <TableHeadCell>Health</TableHeadCell>
                <TableHeadCell align="right">Recent fail rate</TableHeadCell>
                <TableHeadCell />
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {filtered.map((family, index) => (
                <tr
                  key={family.familyId}
                  {...rowActivationProps(() =>
                    navigate(`/datasets/${encodeURIComponent(family.familyId)}`),
                  )}
                  className={cn(
                    "cursor-pointer hover:bg-accent-wash",
                    index < filtered.length - 1 && "border-b border-line-soft",
                  )}
                >
                  <td className="px-2 py-[9px] font-semibold">{family.familyId}</td>
                  <td className="px-2 py-[9px] text-right text-muted-ink">
                    {family.versionCount}
                  </td>
                  <td className="px-2 py-[9px] text-muted-ink">
                    {family.latestVersionTag ?? "—"}
                  </td>
                  <td className="px-2 py-[9px] text-right text-muted-ink">{family.caseCount}</td>
                  <td className="px-2 py-[9px] text-muted-ink">
                    {family.primaryFailureType ?? "—"}
                  </td>
                  <td className="px-2 py-[9px]">
                    <StatusChip tone={healthTone(family.healthLabel)}>
                      {family.healthLabel}
                    </StatusChip>
                  </td>
                  <td className="px-2 py-[9px] text-right text-muted-ink">
                    {formatPercent(family.recentFailRate)}
                  </td>
                  <td className="px-2 py-[9px] text-right font-body text-[12.5px] text-accent-text">
                    open →
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <DraftsSection navigate={navigate} />
      </div>
    </div>
  );
}
