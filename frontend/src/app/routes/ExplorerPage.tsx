import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  ConsoleButton,
  EmptyState,
  RouteHeader,
  SegmentedControl,
  StatusChip,
  TableHeadCell,
  formatScore,
  formatTimestamp,
  truncateRunId,
  rowActivationProps,
} from "@/components/console/primitives";
import type { ChipTone } from "@/components/console/primitives";
import type { ArtifactClusterDetailResponse } from "@/lib/artifacts/extended";
import { loadClusterDetail } from "@/lib/artifacts/extended";
import { loadArtifactQuery } from "@/lib/artifacts/load";
import type {
  ArtifactFailureClusterOccurrence,
  ArtifactInsightEvidenceRef,
  ArtifactQueryMode,
  ArtifactQueryResponse,
} from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

const QUERY_LIMIT = 200;

const MODE_OPTIONS: { value: ArtifactQueryMode; label: string }[] = [
  { value: "cases", label: "Cases" },
  { value: "deltas", label: "Deltas" },
  { value: "aggregates", label: "Aggregates" },
  { value: "signals", label: "Signals" },
  { value: "clusters", label: "Clusters" },
];

const MODE_VALUES = new Set<string>(MODE_OPTIONS.map((option) => option.value));

type QueryState =
  | { status: "loading"; response: null; message: null }
  | { status: "ready"; response: ArtifactQueryResponse; message: null }
  | { status: "incompatible"; response: null; message: string };

type ClusterDetailState =
  | { status: "loading"; detail: null; message: null }
  | { status: "ready"; detail: ArtifactClusterDetailResponse; message: null }
  | { status: "incompatible"; detail: null; message: string };

function verdictTone(verdict: string): ChipTone {
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

function transitionToneClass(transitionType: string): string {
  if (transitionType === "no_failure_to_failure" || transitionType === "new_error") {
    return "text-bad";
  }
  if (transitionType === "failure_to_no_failure" || transitionType === "error_cleared") {
    return "text-good";
  }
  return "text-muted-ink";
}

function evidencePath(ref: {
  kind: string;
  runId: string | null;
  reportId: string | null;
  caseId: string | null;
}): string | null {
  const caseId = ref.caseId ?? "";
  if (ref.kind === "run_case" && ref.runId) {
    return `/runs/${encodeURIComponent(ref.runId)}?caseId=${encodeURIComponent(caseId)}`;
  }
  if (ref.reportId) {
    return `/comparisons/${encodeURIComponent(ref.reportId)}/evidence?caseId=${encodeURIComponent(caseId)}`;
  }
  return null;
}

function occurrencePath(occurrence: ArtifactFailureClusterOccurrence): string | null {
  if (occurrence.clusterKind === "run_case" && occurrence.runId) {
    return `/runs/${encodeURIComponent(occurrence.runId)}?caseId=${encodeURIComponent(
      occurrence.caseId,
    )}`;
  }
  if (occurrence.reportId) {
    return `/comparisons/${encodeURIComponent(occurrence.reportId)}/evidence?caseId=${encodeURIComponent(occurrence.caseId)}`;
  }
  return null;
}

const FACET_SELECT_CLASS =
  "cursor-pointer rounded-tok border border-line bg-raised px-[10px] py-[7px] font-mono text-[12px] text-ink focus:border-accent focus:outline-none";

function FacetSelect({
  label,
  allLabel,
  options,
  value,
  onChange,
}: {
  label: string;
  allLabel: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <select
      aria-label={label}
      value={options.includes(value) ? value : ""}
      onChange={(event) => onChange(event.target.value)}
      className={FACET_SELECT_CLASS}
    >
      <option value="">{allLabel}</option>
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}

function InsightEvidenceChip({ evidenceRef }: { evidenceRef: ArtifactInsightEvidenceRef }) {
  const navigate = useNavigate();
  const path = evidencePath(evidenceRef);
  return (
    <button
      type="button"
      disabled={!path}
      onClick={() => {
        if (path) navigate(path);
      }}
      className={cn(
        "rounded-tok border border-line bg-raised px-[7px] py-[3px] font-mono text-[10.5px]",
        path ? "cursor-pointer text-accent-text hover:bg-accent-wash" : "text-muted-ink",
      )}
    >
      {evidenceRef.label}
    </button>
  );
}

function ClusterDetailPanel({
  clusterId,
  onClose,
}: {
  clusterId: string;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const [state, setState] = useState<ClusterDetailState>({
    status: "loading",
    detail: null,
    message: null,
  });

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading", detail: null, message: null });
    loadClusterDetail(clusterId)
      .then((detail) => {
        if (!cancelled) setState({ status: "ready", detail, message: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "incompatible",
            detail: null,
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [clusterId]);

  return (
    <aside className="w-[380px] flex-none overflow-auto border-l border-line bg-panel p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="font-heading text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-ink">
          Cluster
        </div>
        <button
          type="button"
          aria-label="Close cluster panel"
          onClick={onClose}
          className="cursor-pointer rounded-tok border border-transparent px-1 text-[13px] text-muted-ink hover:bg-raised"
        >
          <X size={12} strokeWidth={1.5} aria-hidden="true" />
        </button>
      </div>
      {state.status === "loading" ? (
        <div aria-label="Loading cluster detail" className="mt-4 flex flex-col gap-2">
          {[0, 1, 2].map((row) => (
            <div key={row} className="h-9 animate-pulse rounded-tok bg-raised" />
          ))}
        </div>
      ) : state.status === "incompatible" ? (
        <div className="mt-4 font-mono text-[11.5px] leading-relaxed text-muted-ink">
          {state.message}
        </div>
      ) : (
        <>
          <div className="mt-2 font-body text-[13.5px] font-medium text-ink">
            {state.detail.summary.label}
          </div>
          <div className="mt-1.5 font-body text-[13px] leading-relaxed text-muted-ink">
            {state.detail.summary.summary}
          </div>
          <div className="mt-3 flex flex-col gap-1 font-mono text-[11px] text-muted-ink">
            <span>{state.detail.summary.occurrenceCount} occurrences</span>
            <span>
              {formatTimestamp(state.detail.summary.firstSeenAt)} →{" "}
              {formatTimestamp(state.detail.summary.lastSeenAt)}
            </span>
            <span>{state.detail.summary.datasets.join(" · ") || "—"}</span>
            <span>{state.detail.summary.models.join(" · ") || "—"}</span>
            <span>{state.detail.summary.failureTypes.join(" · ") || "—"}</span>
          </div>
          <div className="mt-5 font-heading text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-ink">
            Occurrences
          </div>
          <div className="mt-2 flex flex-col">
            {state.detail.occurrences.slice(0, 20).map((occurrence, index, sliced) => {
              const path = occurrencePath(occurrence);
              return (
                <button
                  key={`${occurrence.caseId}-${index}`}
                  type="button"
                  disabled={!path}
                  onClick={() => {
                    if (path) navigate(path);
                  }}
                  className={cn(
                    "flex items-center justify-between gap-3 px-1 py-[7px] text-left font-mono text-[11.5px]",
                    index < sliced.length - 1 && "border-b border-line-soft",
                    path ? "cursor-pointer hover:bg-accent-wash" : "cursor-default",
                  )}
                >
                  <span className="truncate font-semibold text-ink">{occurrence.caseId}</span>
                  <span className="flex-none text-muted-ink">
                    {occurrence.clusterKind === "run_case"
                      ? occurrence.failureType ?? "—"
                      : occurrence.transitionType ?? "—"}
                  </span>
                </button>
              );
            })}
          </div>
        </>
      )}
    </aside>
  );
}

export function ExplorerPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, setState] = useState<QueryState>({
    status: "loading",
    response: null,
    message: null,
  });
  const [reloadKey, setReloadKey] = useState(0);

  const modeParam = searchParams.get("mode") ?? "";
  const mode: ArtifactQueryMode = MODE_VALUES.has(modeParam)
    ? (modeParam as ArtifactQueryMode)
    : "deltas";
  const datasetFilter = searchParams.get("dataset") ?? "";
  const modelFilter = searchParams.get("model") ?? "";
  const failureTypeFilter = searchParams.get("failureType") ?? "";
  const clusterId = searchParams.get("clusterId") ?? "";

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    params.set("mode", mode);
    if (datasetFilter) params.set("dataset", datasetFilter);
    if (modelFilter) params.set("model", modelFilter);
    if (failureTypeFilter) params.set("failureType", failureTypeFilter);
    params.set("limit", String(QUERY_LIMIT));
    return params.toString();
  }, [mode, datasetFilter, modelFilter, failureTypeFilter]);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading", response: null, message: null });
    loadArtifactQuery(new URLSearchParams(queryString))
      .then((response) => {
        if (!cancelled) setState({ status: "ready", response, message: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "incompatible",
            response: null,
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [queryString, reloadKey]);

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next, { replace: true });
  };

  const response = state.status === "ready" ? state.response : null;
  const facets = response?.facets ?? null;
  const rowCount = response?.rows.length ?? 0;
  const hasFilters = Boolean(datasetFilter || modelFilter || failureTypeFilter);
  const insightReport = response?.insightReport ?? null;

  const renderTable = () => {
    if (!response) return null;
    if (response.mode === "cases") {
      return (
        <table className="w-full border-collapse text-[13.5px]">
          <thead>
            <tr className="border-b border-line">
              <TableHeadCell>Run</TableHeadCell>
              <TableHeadCell>Case id</TableHeadCell>
              <TableHeadCell>Failure type</TableHeadCell>
              <TableHeadCell>Verdict</TableHeadCell>
              <TableHeadCell align="right">Conf</TableHeadCell>
              <TableHeadCell>Prompt</TableHeadCell>
            </tr>
          </thead>
          <tbody className="font-mono text-[12.5px]">
            {response.rows.map((row, index) => (
              <tr
                key={`${row.runId}-${row.caseId}`}
                {...rowActivationProps(() =>
                  navigate(
                    `/runs/${encodeURIComponent(row.runId)}?caseId=${encodeURIComponent(row.caseId)}`,
                  ),
                )}
                className={cn(
                  "cursor-pointer hover:bg-accent-wash",
                  index < response.rows.length - 1 && "border-b border-line-soft",
                )}
              >
                <td className="whitespace-nowrap px-2 py-[9px] text-muted-ink">{truncateRunId(row.runId)}</td>
                <td className="px-2 py-[9px] font-semibold">{row.caseId}</td>
                <td className="px-2 py-[9px]">{row.failureType ?? "—"}</td>
                <td className="px-2 py-[9px] text-muted-ink">
                  {row.expectationVerdict ?? "—"}
                </td>
                <td className="px-2 py-[9px] text-right text-muted-ink">
                  {row.confidence != null ? row.confidence.toFixed(2) : "—"}
                </td>
                <td className="max-w-[60ch] truncate px-2 py-[9px] font-body text-[12.5px] text-muted-ink">
                  {row.prompt}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    if (response.mode === "deltas") {
      return (
        <table className="w-full border-collapse text-[13.5px]">
          <thead>
            <tr className="border-b border-line">
              <TableHeadCell>Report</TableHeadCell>
              <TableHeadCell>Case id</TableHeadCell>
              <TableHeadCell>Transition</TableHeadCell>
              <TableHeadCell>Baseline → candidate</TableHeadCell>
              <TableHeadCell>Prompt</TableHeadCell>
            </tr>
          </thead>
          <tbody className="font-mono text-[12.5px]">
            {response.rows.map((row, index) => (
              <tr
                key={`${row.reportId}-${row.caseId}`}
                {...rowActivationProps(() =>
                  navigate(
                    `/comparisons/${encodeURIComponent(row.reportId)}/evidence?caseId=${encodeURIComponent(row.caseId)}`,
                  ),
                )}
                className={cn(
                  "cursor-pointer hover:bg-accent-wash",
                  index < response.rows.length - 1 && "border-b border-line-soft",
                )}
              >
                <td className="whitespace-nowrap px-2 py-[9px] text-muted-ink">
                  {truncateRunId(row.reportId)}
                </td>
                <td className="px-2 py-[9px] font-semibold">{row.caseId}</td>
                <td
                  className={cn(
                    "px-2 py-[9px] text-[11.5px]",
                    transitionToneClass(row.transitionType),
                  )}
                >
                  {row.transitionType}
                </td>
                <td className="px-2 py-[9px] text-muted-ink">
                  {row.baselineFailureType ?? "—"} → {row.candidateFailureType ?? "—"}
                </td>
                <td className="max-w-[60ch] truncate px-2 py-[9px] font-body text-[12.5px] text-muted-ink">
                  {row.prompt}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    if (response.mode === "aggregates") {
      const maxCount = Math.max(1, ...response.rows.map((row) => row.caseCount));
      return (
        <table className="w-full border-collapse text-[13.5px]">
          <thead>
            <tr className="border-b border-line">
              <TableHeadCell>Group</TableHeadCell>
              <TableHeadCell align="right">Cases</TableHeadCell>
              <TableHeadCell className="w-[40%]" />
            </tr>
          </thead>
          <tbody className="font-mono text-[12.5px]">
            {response.rows.map((row, index) => (
              <tr
                key={row.groupKey}
                className={cn(
                  index < response.rows.length - 1 && "border-b border-line-soft",
                )}
              >
                <td className="px-2 py-[9px] font-semibold">{row.groupLabel}</td>
                <td className="px-2 py-[9px] text-right text-muted-ink">{row.caseCount}</td>
                <td className="px-2 py-[9px]">
                  <div className="h-[18px] w-full bg-raised">
                    <div
                      className="h-full bg-accent"
                      style={{ width: `${(row.caseCount / maxCount) * 100}%` }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    if (response.mode === "signals") {
      return (
        <table className="w-full border-collapse text-[13.5px]">
          <thead>
            <tr className="border-b border-line">
              <TableHeadCell>Report id</TableHeadCell>
              <TableHeadCell>Dataset</TableHeadCell>
              <TableHeadCell>Verdict</TableHeadCell>
              <TableHeadCell align="right">Severity</TableHeadCell>
              <TableHeadCell align="right">Net</TableHeadCell>
              <TableHeadCell>Top driver</TableHeadCell>
            </tr>
          </thead>
          <tbody className="font-mono text-[12.5px]">
            {response.rows.map((row, index) => (
              <tr
                key={row.reportId}
                {...rowActivationProps(() => navigate(`/comparisons/${encodeURIComponent(row.reportId)}`))}
                className={cn(
                  "cursor-pointer hover:bg-accent-wash",
                  index < response.rows.length - 1 && "border-b border-line-soft",
                )}
              >
                <td className="px-2 py-[9px] font-semibold">{row.reportId}</td>
                <td className="px-2 py-[9px] text-muted-ink">{row.dataset ?? "—"}</td>
                <td className="px-2 py-[9px]">
                  <StatusChip tone={verdictTone(row.signalVerdict)}>
                    {row.signalVerdict}
                  </StatusChip>
                </td>
                <td
                  className={cn(
                    "px-2 py-[9px] text-right",
                    row.signalVerdict === "regression"
                      ? "font-semibold text-bad"
                      : "text-muted-ink",
                  )}
                >
                  {formatScore(row.severity)}
                </td>
                <td className="px-2 py-[9px] text-right text-muted-ink">
                  {formatScore(row.netScore).replace("-", "−")}
                </td>
                <td className="px-2 py-[9px] text-muted-ink">
                  {row.topDrivers[0]?.failureType ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    return (
      <table className="w-full border-collapse text-[13.5px]">
        <thead>
          <tr className="border-b border-line">
            <TableHeadCell>Cluster id</TableHeadCell>
            <TableHeadCell>Label</TableHeadCell>
            <TableHeadCell>Kind</TableHeadCell>
            <TableHeadCell align="right">Occurrences</TableHeadCell>
            <TableHeadCell align="right">Scopes</TableHeadCell>
            <TableHeadCell>Failure types</TableHeadCell>
            <TableHeadCell>Last seen</TableHeadCell>
          </tr>
        </thead>
        <tbody className="font-mono text-[12.5px]">
          {response.rows.map((row, index) => (
            <tr
              key={row.clusterId}
              {...rowActivationProps(() => setParam("clusterId", row.clusterId))}
              className={cn(
                "cursor-pointer hover:bg-accent-wash",
                index < response.rows.length - 1 && "border-b border-line-soft",
                clusterId === row.clusterId && "bg-accent-wash",
              )}
            >
              <td className="px-2 py-[9px] font-semibold">{row.clusterId}</td>
              <td className="px-2 py-[9px] font-body text-[12.5px]">{row.label}</td>
              <td className="px-2 py-[9px] text-[11px] text-muted-ink">{row.clusterKind}</td>
              <td className="px-2 py-[9px] text-right text-muted-ink">
                {row.occurrenceCount}
              </td>
              <td className="px-2 py-[9px] text-right text-muted-ink">{row.scopeCount}</td>
              <td className="px-2 py-[9px] text-[11px] text-muted-ink">
                {row.failureTypes.join(" · ") || "—"}
              </td>
              <td className="px-2 py-[9px] text-muted-ink">
                {formatTimestamp(row.lastSeenAt)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <RouteHeader eyebrow="Derived index" title="Evidence" />

      <div className="flex flex-wrap items-center gap-[9px] border-b border-line bg-panel px-7 py-[11px]">
        <SegmentedControl
          aria-label="Query mode"
          options={MODE_OPTIONS}
          value={mode}
          onChange={(value) => {
            const next = new URLSearchParams(searchParams);
            next.set("mode", value);
            next.delete("clusterId");
            setSearchParams(next, { replace: true });
          }}
        />
        <FacetSelect
          label="Filter by dataset"
          allLabel="all datasets"
          options={facets?.datasets ?? (datasetFilter ? [datasetFilter] : [])}
          value={datasetFilter}
          onChange={(value) => setParam("dataset", value)}
        />
        <FacetSelect
          label="Filter by model"
          allLabel="all models"
          options={facets?.models ?? (modelFilter ? [modelFilter] : [])}
          value={modelFilter}
          onChange={(value) => setParam("model", value)}
        />
        <FacetSelect
          label="Filter by failure type"
          allLabel="all types"
          options={facets?.failureTypes ?? (failureTypeFilter ? [failureTypeFilter] : [])}
          value={failureTypeFilter}
          onChange={(value) => setParam("failureType", value)}
        />
        <span className="ml-auto text-[12px] text-muted-ink">
          {rowCount} {rowCount === 1 ? "row" : "rows"} · limit {QUERY_LIMIT}
        </span>
      </div>

      <div className="flex min-h-0 flex-1">
        <div className="min-w-0 flex-1 overflow-auto px-7 pb-[22px]">
          {state.status === "loading" ? (
            <div aria-label="Loading evidence" className="mt-4 flex flex-col gap-2">
              {[0, 1, 2, 3].map((row) => (
                <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
              ))}
            </div>
          ) : state.status === "incompatible" ? (
            <EmptyState
              title="Evidence query failed."
              detail={state.message}
              action={
                <ConsoleButton onClick={() => setReloadKey((key) => key + 1)}>
                  Retry
                </ConsoleButton>
              }
            />
          ) : rowCount === 0 && !hasFilters ? (
            mode === "clusters" ? (
              <EmptyState
                title="No recurring failure clusters."
                detail="clusters need the same failure to recur across artifacts · run: failure-lab clusters"
              />
            ) : (
              <EmptyState
                title="No indexed evidence."
                detail=".failure_lab/query_index.sqlite3 · run: failure-lab index rebuild"
              />
            )
          ) : rowCount === 0 ? (
            <EmptyState
              title="No rows match the current filters."
              detail={
                datasetFilter
                  ? `clear the dataset filter "${datasetFilter}"`
                  : modelFilter
                    ? `clear the model filter "${modelFilter}"`
                    : `clear the failure type filter "${failureTypeFilter}"`
              }
              action={
                <ConsoleButton
                  onClick={() => setSearchParams({ mode }, { replace: true })}
                >
                  Clear filters
                </ConsoleButton>
              }
            />
          ) : (
            <>
              {renderTable()}
              {insightReport ? (
                <details className="mt-[22px] rounded-tok border border-line bg-panel px-4 py-3">
                  <summary className="cursor-pointer font-body text-[13px] text-ink">
                    {insightReport.title}
                  </summary>
                  <div className="mt-2 font-body text-[13px] leading-relaxed text-muted-ink">
                    {insightReport.summary}
                  </div>
                  <div className="mt-3 flex flex-col gap-2">
                    {insightReport.patterns.map((pattern) => (
                      <div
                        key={`${pattern.kind}-${pattern.label}`}
                        className="flex flex-wrap items-center gap-2"
                      >
                        <span className="font-body text-[12.5px] text-ink">
                          {pattern.label}
                        </span>
                        <span className="font-mono text-[11px] text-muted-ink">
                          {pattern.count}
                          {pattern.share != null
                            ? ` · ${(pattern.share * 100).toFixed(1)}%`
                            : ""}
                        </span>
                        {pattern.evidenceRefs.map((evidenceRef, refIndex) => (
                          <InsightEvidenceChip
                            key={`${evidenceRef.label}-${refIndex}`}
                            evidenceRef={evidenceRef}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </details>
              ) : null}
            </>
          )}
        </div>
        {mode === "clusters" && clusterId ? (
          <ClusterDetailPanel
            clusterId={clusterId}
            onClose={() => setParam("clusterId", "")}
          />
        ) : null}
      </div>
    </div>
  );
}
