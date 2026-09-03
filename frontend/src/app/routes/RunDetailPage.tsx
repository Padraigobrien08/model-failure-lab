import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  ConsoleButton,
  ConsoleInput,
  EmptyState,
  SectionLabel,
  SegmentedControl,
  StatusChip,
  TableHeadCell,
  formatPercent,
  formatTimestamp,
  runStatusTone,
  rowActivationProps,
} from "@/components/console/primitives";
import type { ChipTone } from "@/components/console/primitives";
import { RunHarvestDialog } from "@/components/console/RunHarvestDialog";
import { ArtifactRequestError, loadRunDetail } from "@/lib/artifacts/load";
import type {
  RunCaseLensKey,
  RunCaseRecord,
  RunDetail,
  RunDetailState,
} from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

const LENS_KEYS: RunCaseLensKey[] = ["mismatches", "notable", "all", "errors"];

function lensCaseIds(detail: RunDetail, lens: RunCaseLensKey): string[] {
  switch (lens) {
    case "mismatches":
      return detail.lenses.mismatchCaseIds;
    case "notable":
      return detail.lenses.notableCaseIds;
    case "errors":
      return detail.lenses.errorCaseIds;
    default:
      return detail.lenses.allCaseIds;
  }
}

/**
 * Tone for one expectation verdict.
 *
 * The values come from `schemas/taxonomy.py:EXPECTATION_VERDICTS` --
 * `matched_expected`, `unexpected_failure`, `missed_expected`, `no_failure_as_expected`.
 * This function used to test for "match"/"mismatch", which the engine has never emitted, so
 * every chip fell through to neutral and an `unexpected_failure` looked exactly like a
 * `no_failure_as_expected`.
 *
 * A run detail has no baseline, so nothing on this screen can be a regression: an unmet
 * expectation is `warn` (degraded), never `bad`. Red is reserved for regression.
 */
function expectationVerdictTone(verdict: string | null): ChipTone {
  if (verdict === "matched_expected" || verdict === "no_failure_as_expected") return "good";
  if (verdict === "unexpected_failure" || verdict === "missed_expected") return "warn";
  return "neutral";
}

function MetricCard({
  label,
  value,
  sub,
  valueClassName,
}: {
  label: string;
  value: string;
  sub: string;
  valueClassName?: string;
}) {
  return (
    <div className="rounded-tok border border-line bg-panel p-[14px_16px]">
      <SectionLabel>{label}</SectionLabel>
      <div className={cn("mt-1 font-heading text-[26px] font-semibold text-ink", valueClassName)}>
        {value}
      </div>
      <div className="mt-0.5 font-mono text-[11.5px] text-muted-ink">{sub}</div>
    </div>
  );
}

export function RunDetailPage() {
  const { runId = "" } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, setState] = useState<RunDetailState>({
    status: "idle",
    detail: null,
    message: null,
  });
  const [showRawJson, setShowRawJson] = useState(false);
  const [harvestOpen, setHarvestOpen] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading", detail: null, message: null });
    loadRunDetail(runId)
      .then((detail) => {
        if (!cancelled) setState({ status: "ready", detail, message: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "incompatible",
            detail: null,
            message: error instanceof Error ? error.message : String(error),
            artifactPath:
              error instanceof ArtifactRequestError ? error.artifactPath : undefined,
            remedy: error instanceof ArtifactRequestError ? error.remedy : undefined,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [runId, reloadToken]);

  const lensParam = searchParams.get("lens") ?? "all";
  const lens: RunCaseLensKey = (LENS_KEYS as string[]).includes(lensParam)
    ? (lensParam as RunCaseLensKey)
    : "all";
  const q = searchParams.get("q") ?? "";
  const failureTypeFilter = searchParams.get("failureType") ?? "";
  const selectedCaseId = searchParams.get("caseId") ?? "";

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next, { replace: true });
  };

  const detail = state.status === "ready" ? state.detail : null;

  const casesById = useMemo(() => {
    const map = new Map<string, RunCaseRecord>();
    for (const record of detail?.cases ?? []) {
      map.set(record.caseId, record);
    }
    return map;
  }, [detail]);

  const lensCases = useMemo(() => {
    if (!detail) return [];
    return lensCaseIds(detail, lens)
      .map((caseId) => casesById.get(caseId))
      .filter((record): record is RunCaseRecord => Boolean(record));
  }, [detail, lens, casesById]);

  const filtered = lensCases.filter(
    (record) =>
      (!q || record.caseId.includes(q) || record.prompt.includes(q)) &&
      (!failureTypeFilter ||
        record.classification?.failure.failureType === failureTypeFilter),
  );

  const selectedCase = selectedCaseId ? (casesById.get(selectedCaseId) ?? null) : null;

  if (state.status === "loading" || state.status === "idle") {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <header className="border-b border-line px-7 pb-[15px] pt-[22px]">
          <button
            type="button"
            onClick={() => navigate("/")}
            className="cursor-pointer border-0 bg-transparent p-0 font-mono text-[11px] text-accent-text"
          >
            ← runs
          </button>
          <h1 className="mt-1.5 font-mono text-[22px] font-semibold leading-[1.1] text-ink">
            {runId}
          </h1>
        </header>
        <div aria-label="Loading run detail" className="mt-4 flex flex-col gap-2 px-7">
          {[0, 1, 2, 3].map((row) => (
            <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
          ))}
        </div>
      </div>
    );
  }

  if (state.status === "incompatible" || !detail) {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <header className="border-b border-line px-7 pb-[15px] pt-[22px]">
          <button
            type="button"
            onClick={() => navigate("/")}
            className="cursor-pointer border-0 bg-transparent p-0 font-mono text-[11px] text-accent-text"
          >
            ← runs
          </button>
          <h1 className="mt-1.5 font-mono text-[22px] font-semibold leading-[1.1] text-ink">
            {runId}
          </h1>
        </header>
        <div className="flex-1 overflow-auto px-7 pb-[22px]">
          <EmptyState
            title={
              state.status === "incompatible" ? state.message : "Run detail failed to load."
            }
            detail={
              <>
                {state.status === "incompatible" && state.artifactPath ? (
                  <div>{state.artifactPath}</div>
                ) : null}
                {state.status === "incompatible" && state.remedy ? (
                  <div className="mt-1 text-ink">run: {state.remedy}</div>
                ) : (
                  <div>{runId}</div>
                )}
              </>
            }
            action={
              <ConsoleButton onClick={() => setReloadToken((token) => token + 1)}>
                Retry
              </ConsoleButton>
            }
          />
        </div>
      </div>
    );
  }

  const { run, metrics } = detail;
  const countLabel = `${filtered.length} ${filtered.length === 1 ? "case" : "cases"} · dataset order`;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-end justify-between gap-6 border-b border-line px-7 pb-[15px] pt-[22px]">
        <div className="min-w-0">
          <button
            type="button"
            onClick={() => navigate("/")}
            className="cursor-pointer border-0 bg-transparent p-0 font-mono text-[11px] text-accent-text"
          >
            ← runs
          </button>
          {/* Run ids are long, unbreakable monospace strings. Without `break-all` the H1
              overflowed its flex box and painted underneath the header actions on every real
              run id. DESIGN.md keeps run ids in their raw form in a primary position, so wrap
              rather than truncate. */}
          <h1 className="mt-1.5 break-all font-mono text-[22px] font-semibold leading-[1.1] text-ink">
            {run.runId}
          </h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-2 font-mono text-[11px] text-muted-ink">
            <span>
              dataset {run.dataset} · model {run.model} · adapter {run.adapterId ?? "—"} ·
              classifier {run.classifierId ?? "—"} · seed{" "}
              {run.runSeed != null ? String(run.runSeed) : "—"}
            </span>
            <StatusChip tone={runStatusTone(run.status)}>{run.status}</StatusChip>
            <span>{formatTimestamp(run.createdAt)}</span>
          </div>
        </div>
        <div className="flex flex-none gap-2">
          <ConsoleButton variant="secondary" onClick={() => setShowRawJson((value) => !value)}>
            Open run.json
          </ConsoleButton>
          <ConsoleButton
            variant="primary"
            onClick={() => setHarvestOpen(true)}
            disabled={metrics.failureCaseCount === 0}
          >
            Harvest failures
          </ConsoleButton>
        </div>
      </header>

      <div className="border-b border-line px-7 py-[14px]">
        <div className="grid grid-cols-4 gap-[10px]">
          <MetricCard
            label="Failure rate"
            value={formatPercent(metrics.failureRate)}
            sub={`${metrics.failureCaseCount} of ${metrics.classifiedCaseCount} classified`}
          />
          <MetricCard
            label="Classification coverage"
            value={formatPercent(metrics.classificationCoverage)}
            sub={`${metrics.classifiedCaseCount} / ${metrics.attemptedCaseCount}`}
          />
          <MetricCard
            label="Execution success"
            value={formatPercent(metrics.executionSuccessRate)}
            sub={`${metrics.executionErrorCount} ${metrics.executionErrorCount === 1 ? "error" : "errors"}`}
          />
          <MetricCard
            label="Cases"
            value={String(metrics.attemptedCaseCount)}
            sub={run.dataset}
          />
        </div>
      </div>

      {showRawJson ? (
        <div className="flex-1 overflow-auto px-7 py-[14px]">
          <pre className="rounded-tok border border-line bg-panel p-4 font-mono text-[11.5px] leading-relaxed text-ink">
            {JSON.stringify(detail, null, 2)}
          </pre>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-[9px] border-b border-line bg-panel px-7 py-[11px]">
            <SegmentedControl
              aria-label="Case lens"
              options={LENS_KEYS.map((key) => ({
                value: key,
                label: `${key} (${lensCaseIds(detail, key).length})`,
              }))}
              value={lens}
              onChange={(value) => setParam("lens", value === "all" ? "" : value)}
            />
            <ConsoleInput
              aria-label="Filter cases"
              placeholder="case id or prompt contains…"
              value={q}
              onChange={(event) => setParam("q", event.target.value)}
              className="w-64"
            />
            {failureTypeFilter ? (
              <button
                type="button"
                onClick={() => setParam("failureType", "")}
                className="inline-flex cursor-pointer items-center gap-2 rounded-tok border border-line bg-transparent px-[11px] py-[5px] font-body text-[12px] font-medium text-ink"
              >
                failure type: <span className="font-mono">{failureTypeFilter}</span>
                <span aria-hidden="true" className="text-muted-ink">
                  <X size={12} strokeWidth={1.5} aria-hidden="true" />
                </span>
              </button>
            ) : null}
            <span className="ml-auto text-[12px] text-muted-ink">{countLabel}</span>
          </div>

          {detail.summary.failureTypes.length > 0 ? (
            <div className="flex flex-wrap items-center gap-2 border-b border-line px-7 py-[10px]">
              {detail.summary.failureTypes.map((row) => (
                <button
                  key={row.label}
                  type="button"
                  onClick={() =>
                    setParam("failureType", failureTypeFilter === row.label ? "" : row.label)
                  }
                  className={cn(
                    "cursor-pointer rounded-tok border border-line bg-transparent px-3 py-2 text-left hover:bg-accent-wash",
                    failureTypeFilter === row.label && "bg-accent-wash",
                  )}
                >
                  <div className="font-mono text-[11px] text-ink">{row.label}</div>
                  <div
                    className={cn(
                      "font-mono text-[11.5px]",
                      row.label !== "no_failure" ? "font-semibold text-ink" : "text-muted-ink",
                    )}
                  >
                    {row.count} · {formatPercent(row.share)}
                  </div>
                </button>
              ))}
            </div>
          ) : null}

          <div className="flex min-h-0 flex-1">
            <div className="flex-1 overflow-auto px-7 pb-[22px]">
              {detail.cases.length === 0 ? (
                <EmptyState
                  title="No cases in this run."
                  detail={
                    `read runs/${run.runId}/results.json · ` +
                    `run: failure-lab run --dataset ${run.dataset} --model <model>`
                  }
                />
              ) : filtered.length === 0 ? (
                <EmptyState
                  title="No cases match the current filters."
                  detail={
                    q
                      ? `clear the case filter "${q}"`
                      : failureTypeFilter
                        ? `clear the failure type filter "${failureTypeFilter}"`
                        : `clear the "${lens}" lens`
                  }
                  action={
                    <ConsoleButton
                      onClick={() => {
                        const next = new URLSearchParams(searchParams);
                        next.delete("lens");
                        next.delete("q");
                        next.delete("failureType");
                        setSearchParams(next, { replace: true });
                      }}
                    >
                      Clear filters
                    </ConsoleButton>
                  }
                />
              ) : (
                <table className="w-full border-collapse text-[13.5px]">
                  <thead>
                    <tr className="border-b border-line">
                      <TableHeadCell>Case id</TableHeadCell>
                      <TableHeadCell>Failure type</TableHeadCell>
                      <TableHeadCell>Subtype</TableHeadCell>
                      <TableHeadCell>Verdict</TableHeadCell>
                      <TableHeadCell align="right">Conf</TableHeadCell>
                      <TableHeadCell>Tags</TableHeadCell>
                      <TableHeadCell>Error</TableHeadCell>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-[12.5px]">
                    {filtered.map((record, index) => (
                      <tr
                        key={record.caseId}
                        {...rowActivationProps(() => setParam("caseId", record.caseId))}
                        className={cn(
                          "cursor-pointer hover:bg-accent-wash",
                          index < filtered.length - 1 && "border-b border-line-soft",
                          record.caseId === selectedCaseId && "bg-accent-wash",
                        )}
                      >
                        <td className="px-2 py-[9px] font-semibold">{record.caseId}</td>
                        <td className="px-2 py-[9px] text-muted-ink">
                          {record.classification?.failure.failureType ?? "—"}
                        </td>
                        <td className="px-2 py-[9px] text-muted-ink">
                          {record.classification?.failure.failureSubtype ?? "—"}
                        </td>
                        <td className="px-2 py-[9px]">
                          <StatusChip tone={expectationVerdictTone(record.expectation.verdict)}>
                            {record.expectation.verdict ?? "—"}
                          </StatusChip>
                        </td>
                        <td className="px-2 py-[9px] text-right text-muted-ink">
                          {record.classification?.confidence != null
                            ? record.classification.confidence.toFixed(2)
                            : "—"}
                        </td>
                        <td className="px-2 py-[9px]">
                          <span className="flex flex-wrap gap-1">
                            {record.tags.map((tag) => (
                              <span
                                key={tag}
                                className="rounded-full bg-raised px-2 py-[1px] text-[10.5px] text-muted-ink"
                              >
                                {tag}
                              </span>
                            ))}
                          </span>
                        </td>
                        <td className="px-2 py-[9px] text-muted-ink">
                          {record.error?.stage ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {selectedCase ? (
              <aside className="w-[360px] flex-none overflow-auto border-l border-line bg-panel p-5">
                <div className="flex items-start justify-between gap-2">
                  <SectionLabel>Case</SectionLabel>
                  <button
                    type="button"
                    aria-label="Close case panel"
                    onClick={() => setParam("caseId", "")}
                    className="cursor-pointer border-0 bg-transparent p-0 text-[12px] text-muted-ink hover:text-ink"
                  >
                    <X size={12} strokeWidth={1.5} aria-hidden="true" />
                  </button>
                </div>
                <div className="mt-1 font-mono text-[12.5px] font-semibold text-ink">
                  {selectedCase.caseId}
                </div>
                <div className="font-mono text-[11px] text-muted-ink">
                  {selectedCase.promptId}
                </div>

                <SectionLabel className="mt-4">Prompt</SectionLabel>
                <div className="mt-1 font-body text-[13.5px] leading-relaxed text-ink">
                  {selectedCase.prompt}
                </div>

                <SectionLabel className="mt-4">Output</SectionLabel>
                {selectedCase.outputText != null ? (
                  <div className="mt-1 whitespace-pre-wrap font-body text-[13px] leading-relaxed text-ink">
                    {selectedCase.outputText}
                  </div>
                ) : (
                  <div className="mt-1 font-mono text-[11.5px] text-muted-ink">
                    no output captured
                  </div>
                )}

                {selectedCase.classification ? (
                  <>
                    <SectionLabel className="mt-4">Classification</SectionLabel>
                    <div className="mt-1 font-mono text-[12px] text-ink">
                      {selectedCase.classification.failure.failureType}
                      {selectedCase.classification.failure.failureSubtype
                        ? ` / ${selectedCase.classification.failure.failureSubtype}`
                        : ""}
                    </div>
                    <div className="font-mono text-[11px] text-muted-ink">
                      conf{" "}
                      {selectedCase.classification.confidence != null
                        ? selectedCase.classification.confidence.toFixed(2)
                        : "—"}
                    </div>
                    {selectedCase.classification.explanation ? (
                      <div className="mt-1 font-body text-[12.5px] leading-relaxed text-ink">
                        {selectedCase.classification.explanation}
                      </div>
                    ) : null}
                  </>
                ) : null}

                <SectionLabel className="mt-4">Expectation</SectionLabel>
                <div className="mt-1 flex flex-wrap items-center gap-2 font-mono text-[11.5px] text-muted-ink">
                  <span>
                    expected{" "}
                    {selectedCase.expectation.expectedFailure?.failureType ?? "—"} · observed{" "}
                    {selectedCase.expectation.observedFailure?.failureType ?? "—"}
                  </span>
                  <StatusChip tone={expectationVerdictTone(selectedCase.expectation.verdict)}>
                    {selectedCase.expectation.verdict ?? "—"}
                  </StatusChip>
                </div>

                {selectedCase.error ? (
                  <>
                    <SectionLabel className="mt-4">Error</SectionLabel>
                    <div className="mt-1 rounded-tok border border-line bg-warn-bg p-3 font-mono text-[11.5px] leading-relaxed text-ink">
                      <div>stage {selectedCase.error.stage}</div>
                      <div>type {selectedCase.error.type}</div>
                      <div className="mt-1">{selectedCase.error.message}</div>
                    </div>
                  </>
                ) : null}

                <div className="mt-5 font-mono text-[10.5px] text-muted-ink">
                  runs/{run.runId}/results.json#{selectedCase.caseId}
                </div>
              </aside>
            ) : null}
          </div>
        </>
      )}

      <RunHarvestDialog
        open={harvestOpen}
        onClose={() => setHarvestOpen(false)}
        runId={run.runId}
        dataset={run.dataset}
        failureTypes={detail.summary.failureTypes}
        initialFailureType={failureTypeFilter}
      />
    </div>
  );
}
