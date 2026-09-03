import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { caseSideLabel } from "@/app/routes/ComparisonDetailPage";
import { HarvestDialog } from "@/components/console/HarvestDialog";
import {
  ConsoleButton,
  EmptyState,
  SectionLabel,
  SegmentedControl,
  StatusChip,
  truncateRunId,
} from "@/components/console/primitives";
import {
  IMPROVEMENT_TRANSITIONS,
  REGRESSION_TRANSITIONS,
} from "@/lib/artifacts/transitions";
import { loadComparisonDetail, loadRunDetail } from "@/lib/artifacts/load";
import type {
  ComparisonCaseDeltaRecord,
  ComparisonDetail,
  RunCaseRecord,
  RunDetail,
} from "@/lib/artifacts/types";
import { useAppRouteContext } from "@/app/router";
import { cn } from "@/lib/utils";

type Remote<T> =
  | { status: "loading"; data: null; message: null }
  | { status: "ready"; data: T; message: null }
  | { status: "incompatible"; data: null; message: string };

function useRemoteResource<T>(
  key: string | null,
  load: (key: string) => Promise<T>,
): [Remote<T>, () => void] {
  const [state, setState] = useState<Remote<T>>({
    status: "loading",
    data: null,
    message: null,
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    setState({ status: "loading", data: null, message: null });
    void load(key)
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data, message: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "incompatible",
            data: null,
            message: error instanceof Error ? error.message : "load failed",
          });
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt]);

  return [state, () => setAttempt((n) => n + 1)];
}

function transitionTextTone(transitionType: string): string {
  if (REGRESSION_TRANSITIONS.has(transitionType)) return "text-bad";
  if (IMPROVEMENT_TRANSITIONS.has(transitionType)) return "text-good";
  return "text-muted-ink";
}

function orderDeltas(deltas: ComparisonCaseDeltaRecord[]): ComparisonCaseDeltaRecord[] {
  const rank = (delta: ComparisonCaseDeltaRecord) =>
    REGRESSION_TRANSITIONS.has(delta.transitionType)
      ? 0
      : IMPROVEMENT_TRANSITIONS.has(delta.transitionType)
        ? 2
        : 1;
  return [...deltas].sort(
    (a, b) => rank(a) - rank(b) || a.caseId.localeCompare(b.caseId),
  );
}

function CasePane({
  side,
  runId,
  runDetail,
  record,
  delta,
  tinted,
}: {
  side: "Baseline" | "Candidate";
  runId: string;
  runDetail: Remote<RunDetail>;
  record: RunCaseRecord | null;
  delta: ComparisonCaseDeltaRecord;
  tinted: boolean;
}) {
  const failureLabel =
    side === "Baseline"
      ? caseSideLabel(delta.baselineFailureType, delta.baselineErrorStage)
      : caseSideLabel(delta.candidateFailureType, delta.candidateErrorStage);
  const explanation =
    side === "Baseline" ? delta.baselineExplanation : delta.candidateExplanation;
  const regressed =
    side === "Candidate" && REGRESSION_TRANSITIONS.has(delta.transitionType);
  const clean = failureLabel === "no_failure";
  const classifierId = runDetail.data?.run.classifierId ?? null;
  const confidence = record?.classification?.confidence ?? null;

  return (
    <section
      className={cn(
        "flex flex-col overflow-hidden",
        side === "Baseline" && "border-r border-line",
        tinted && "bg-cand-panel",
      )}
    >
      <div className="flex items-center gap-[9px] border-b border-line px-[22px] py-[11px]">
        <span
          className={cn(
            "font-heading text-[11px] font-semibold uppercase tracking-[0.14em]",
            tinted && side === "Candidate" ? "text-cand-head" : "text-muted-ink",
          )}
        >
          {side}
        </span>
        <span className="font-mono text-[11px] text-muted-ink">{truncateRunId(runId)}</span>
        <StatusChip
          tone={clean ? "good" : regressed ? "bad-strong" : "warn"}
          className="ml-auto"
        >
          {failureLabel}
        </StatusChip>
      </div>
      <div className="flex-1 overflow-auto px-[22px] py-[18px] text-[13.5px] leading-[1.7]">
        {runDetail.status === "loading" ? (
          <div className="flex flex-col gap-2" aria-label={`Loading ${side.toLowerCase()} output`}>
            <div className="h-4 w-4/5 animate-pulse rounded-tok bg-panel" />
            <div className="h-4 w-3/5 animate-pulse rounded-tok bg-panel" />
          </div>
        ) : runDetail.status === "incompatible" ? (
          <div className="font-mono text-[11.5px] text-muted-ink">
            output unavailable · {runDetail.message}
          </div>
        ) : record?.outputText ? (
          <div className="whitespace-pre-wrap">{record.outputText}</div>
        ) : record?.error ? (
          <div className="rounded-tok border border-line bg-warn-bg px-3 py-2.5 font-mono text-[12px] text-warn">
            {record.error.stage} error · {record.error.type}
            <br />
            {record.error.message}
          </div>
        ) : (
          <div className="font-mono text-[11.5px] text-muted-ink">no output captured</div>
        )}

        {explanation ? (
          <div
            className={cn(
              "mt-4 rounded-tok border px-[13px] py-[11px]",
              regressed ? "border-bad-line bg-bad-panel" : "border-line bg-panel",
            )}
          >
            <SectionLabel
              className={cn("text-[9.5px] tracking-[0.16em]", regressed && "text-bad")}
            >
              {regressed
                ? "Why it failed"
                : clean
                  ? "Classifier note"
                  : "Why it was flagged"}
            </SectionLabel>
            <div className="mt-1.5 text-[12.5px] leading-[1.6] text-ink">{explanation}</div>
          </div>
        ) : null}
      </div>
      <div className={cn("border-t border-line px-[22px] py-3", !tinted && "bg-panel")}>
        <div className="font-mono text-[10.5px] text-muted-ink">
          classifier {classifierId ?? "—"} · {failureLabel}
          {confidence != null ? ` · conf ${confidence.toFixed(2)}` : ""}
        </div>
      </div>
    </section>
  );
}

export function EvidencePage() {
  const { reportId } = useParams<{ reportId: string }>();
  const context = useAppRouteContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const [harvestOpen, setHarvestOpen] = useState(false);

  const [detailState, retryDetail] = useRemoteResource<ComparisonDetail>(
    reportId ?? null,
    loadComparisonDetail,
  );
  const detail = detailState.data;

  // The inventory already knows the run pair, so both run details can start
  // in parallel with the comparison detail instead of waterfalling behind it.
  const inventoryItem =
    context.comparisonInventoryState.inventory?.comparisons.find(
      (comparison) => comparison.reportId === reportId,
    ) ?? null;
  const [baselineState] = useRemoteResource<RunDetail>(
    detail?.comparison.baselineRunId ?? inventoryItem?.baselineRunId ?? null,
    loadRunDetail,
  );
  const [candidateState] = useRemoteResource<RunDetail>(
    detail?.comparison.candidateRunId ?? inventoryItem?.candidateRunId ?? null,
    loadRunDetail,
  );

  const scope = searchParams.get("scope") === "all" ? "all" : "regressed";
  const transitionFilter = searchParams.get("transition") ?? "";
  const view = searchParams.get("view") === "json" ? "json" : "side";

  const orderedDeltas = useMemo(
    () => (detail ? orderDeltas(detail.caseDeltas) : []),
    [detail],
  );
  const visibleDeltas = orderedDeltas.filter(
    (delta) =>
      (scope === "all" || REGRESSION_TRANSITIONS.has(delta.transitionType)) &&
      (!transitionFilter || delta.transitionType === transitionFilter),
  );

  const caseIdParam = searchParams.get("caseId");
  const selected =
    visibleDeltas.find((delta) => delta.caseId === caseIdParam) ??
    orderedDeltas.find((delta) => delta.caseId === caseIdParam) ??
    visibleDeltas[0] ??
    null;
  const selectedIndex = selected
    ? visibleDeltas.findIndex((delta) => delta.caseId === selected.caseId)
    : -1;

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next, { replace: true });
  };

  const baselineRecord =
    selected && baselineState.data
      ? baselineState.data.cases.find((record) => record.caseId === selected.caseId) ?? null
      : null;
  const candidateRecord =
    selected && candidateState.data
      ? candidateState.data.cases.find((record) => record.caseId === selected.caseId) ?? null
      : null;

  if (!reportId) return null;

  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex w-[268px] flex-none flex-col overflow-hidden border-r border-line bg-panel">
        <div className="border-b border-line p-4">
          <Link
            to={`/comparisons/${encodeURIComponent(reportId)}`}
            className="font-mono text-[11px] text-accent-text"
          >
            ← {reportId}
          </Link>
          <SectionLabel className="mt-3 text-[9.5px] tracking-[0.16em]">
            Changed cases · {detail ? detail.caseDeltas.length : "…"}
          </SectionLabel>
          <SegmentedControl
            aria-label="Case scope"
            className="mt-2.5 w-full [&>button]:flex-1"
            options={[
              { value: "regressed", label: "Regressed" },
              { value: "all", label: "All" },
            ]}
            value={scope}
            onChange={(value) => setParam("scope", value === "all" ? "all" : "")}
          />
          {transitionFilter ? (
            <button
              type="button"
              onClick={() => setParam("transition", "")}
              className="mt-2 inline-flex cursor-pointer items-center gap-1.5 rounded-tok border border-line bg-transparent px-2 py-1 font-mono text-[10.5px] text-ink"
            >
              {transitionFilter} <span className="text-muted-ink"><X size={12} strokeWidth={1.5} aria-hidden="true" /></span>
            </button>
          ) : null}
        </div>
        <div className="flex-1 overflow-auto">
          {detailState.status === "loading" ? (
            <div className="flex flex-col gap-2 p-3" aria-label="Loading cases">
              {[0, 1, 2, 3].map((row) => (
                <div key={row} className="h-10 animate-pulse rounded-tok bg-raised" />
              ))}
            </div>
          ) : visibleDeltas.length === 0 ? (
            <div className="p-4 font-mono text-[11px] leading-relaxed text-muted-ink">
              {orderedDeltas.length === 0
                ? "no changed cases in this comparison"
                : scope === "regressed"
                  ? "no regressed cases · switch scope to All"
                  : `no cases for transition ${transitionFilter} · clear the filter`}
            </div>
          ) : (
            visibleDeltas.map((delta) => (
              <button
                key={delta.caseId}
                type="button"
                onClick={() => setParam("caseId", delta.caseId)}
                className={cn(
                  "block w-full cursor-pointer border-b border-line-soft bg-transparent px-3.5 py-[11px] text-left hover:bg-accent-wash",
                  selected?.caseId === delta.caseId && "bg-accent-wash",
                )}
              >
                <span className="block font-mono text-[12px] font-semibold text-ink">
                  {delta.caseId}
                </span>
                <span
                  className={cn(
                    "mt-1 block font-mono text-[10.5px]",
                    transitionTextTone(delta.transitionType),
                  )}
                >
                  {caseSideLabel(delta.baselineFailureType, delta.baselineErrorStage)} →{" "}
                  {caseSideLabel(delta.candidateFailureType, delta.candidateErrorStage)}
                </span>
              </button>
            ))
          )}
        </div>
        {visibleDeltas.length > 0 && selected ? (
          <div className="flex items-center gap-2 border-t border-line px-3.5 py-2.5">
            <span className="font-mono text-[10.5px] text-muted-ink">
              case {selectedIndex + 1} of {visibleDeltas.length}
            </span>
            <div className="ml-auto flex gap-1">
              <button
                type="button"
                aria-label="Previous case"
                disabled={selectedIndex <= 0}
                onClick={() => setParam("caseId", visibleDeltas[selectedIndex - 1].caseId)}
                className="h-7 w-7 cursor-pointer rounded-tok border border-line bg-transparent text-[12px] text-ink hover:bg-raised disabled:cursor-not-allowed disabled:opacity-40"
              >
                ←
              </button>
              <button
                type="button"
                aria-label="Next case"
                disabled={selectedIndex >= visibleDeltas.length - 1}
                onClick={() => setParam("caseId", visibleDeltas[selectedIndex + 1].caseId)}
                className="h-7 w-7 cursor-pointer rounded-tok border border-line bg-transparent text-[12px] text-ink hover:bg-raised disabled:cursor-not-allowed disabled:opacity-40"
              >
                →
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {detailState.status === "incompatible" ? (
          <div className="p-7">
            <EmptyState
              title="Comparison failed to load."
              detail={detailState.message}
              action={<ConsoleButton onClick={retryDetail}>Retry</ConsoleButton>}
            />
          </div>
        ) : !selected ? (
          <div className="p-7">
            {detailState.status === "ready" ? (
              <EmptyState
                title="No changed cases to inspect."
                detail={
                  `reports/${reportId}/report_details.json holds no case deltas · ` +
                  `run: failure-lab compare <baseline-run> <candidate-run>`
                }
              />
            ) : (
              <div className="h-24 animate-pulse rounded-tok bg-panel" aria-label="Loading" />
            )}
          </div>
        ) : (
          <>
            <header className="flex items-center gap-3.5 border-b border-line px-[26px] py-4">
              <div className="min-w-0">
                <div className="flex items-center gap-[9px]">
                  <span className="font-mono text-[15px] font-semibold">{selected.caseId}</span>
                  <StatusChip
                    tone={
                      REGRESSION_TRANSITIONS.has(selected.transitionType)
                        ? "bad"
                        : IMPROVEMENT_TRANSITIONS.has(selected.transitionType)
                          ? "good"
                          : "neutral"
                    }
                  >
                    {selected.transitionType}
                  </StatusChip>
                  {selected.tags.map((tag) => (
                    <StatusChip key={tag} tone="neutral" className="text-[10.5px]">
                      {tag}
                    </StatusChip>
                  ))}
                </div>
                <div className="mt-1.5 font-mono text-[11px] text-muted-ink">
                  dataset {detail?.comparison.dataset ?? "—"} · shared case ·{" "}
                  {selected.promptId}
                </div>
              </div>
              <div className="ml-auto flex flex-none gap-2">
                <SegmentedControl
                  aria-label="Case view"
                  options={[
                    { value: "side", label: "Side by side" },
                    { value: "json", label: "Raw JSON" },
                  ]}
                  value={view}
                  onChange={(value) => setParam("view", value === "json" ? "json" : "")}
                />
                <ConsoleButton variant="primary" onClick={() => setHarvestOpen(true)}>
                  Mark for harvest
                </ConsoleButton>
              </div>
            </header>

            <div className="border-b border-line bg-panel px-[26px] py-4">
              <SectionLabel className="text-[9.5px] tracking-[0.16em]">Prompt</SectionLabel>
              <div className="mt-1.5 max-w-[900px] text-[14px] leading-[1.55]">
                {selected.prompt}
              </div>
            </div>

            {view === "json" ? (
              <pre className="flex-1 overflow-auto px-[26px] py-4 font-mono text-[11.5px] leading-relaxed">
                {JSON.stringify(
                  {
                    caseDelta: selected,
                    baselineCase: baselineRecord,
                    candidateCase: candidateRecord,
                  },
                  null,
                  2,
                )}
              </pre>
            ) : (
              <div className="grid flex-1 grid-cols-2 overflow-hidden">
                <CasePane
                  side="Baseline"
                  runId={detail?.comparison.baselineRunId ?? ""}
                  runDetail={baselineState}
                  record={baselineRecord}
                  delta={selected}
                  tinted={false}
                />
                <CasePane
                  side="Candidate"
                  runId={detail?.comparison.candidateRunId ?? ""}
                  runDetail={candidateState}
                  record={candidateRecord}
                  delta={selected}
                  tinted={REGRESSION_TRANSITIONS.has(selected.transitionType)}
                />
              </div>
            )}
          </>
        )}
      </div>

      {detail ? (
        <HarvestDialog
          open={harvestOpen}
          onClose={() => setHarvestOpen(false)}
          reportId={detail.comparison.reportId}
          dataset={detail.comparison.dataset}
          signal={detail.signal}
          recommendation={detail.governanceRecommendation}
          onWritten={context.reloadDatasetFamilies}
        />
      ) : null}
    </div>
  );
}
