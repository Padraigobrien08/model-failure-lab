import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import { HarvestDialog } from "@/components/console/HarvestDialog";
import {
  ConsoleButton,
  EmptyState,
  SectionLabel,
  SegmentedControl,
  StatusChip,
  TableHeadCell,
  formatPercent,
  formatScore,
  formatSignedPts,
  formatSignedScore,
  truncateRunId,
} from "@/components/console/primitives";
import { gateRowTone } from "@/lib/artifacts/gateTone";
import { loadComparisonDetail } from "@/lib/artifacts/load";
import {
  IMPROVEMENT_TRANSITIONS,
  REGRESSION_TRANSITIONS,
  TRANSITION_ORDER,
  type TransitionTone,
  transitionTone,
} from "@/lib/artifacts/transitions";
import type {
  ComparisonCaseDeltaRecord,
  ComparisonDetail,
} from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

type DetailState =
  | { status: "loading"; detail: null; message: null }
  | { status: "ready"; detail: ComparisonDetail; message: null }
  | { status: "incompatible"; detail: null; message: string };

export function transitionGroupTone(transitionType: string): TransitionTone {
  return transitionTone(transitionType);
}

export function caseSideLabel(
  failureType: string | null,
  errorStage: string | null,
): string {
  if (errorStage) return `error:${errorStage}`;
  return failureType ?? "no_failure";
}

function useComparisonDetail(reportId: string | undefined): [DetailState, () => void] {
  const [state, setState] = useState<DetailState>({
    status: "loading",
    detail: null,
    message: null,
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!reportId) return;
    let cancelled = false;
    setState({ status: "loading", detail: null, message: null });
    void loadComparisonDetail(reportId)
      .then((detail) => {
        if (!cancelled) setState({ status: "ready", detail, message: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "incompatible",
            detail: null,
            message: error instanceof Error ? error.message : "comparison detail failed",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [reportId, attempt]);

  return [state, () => setAttempt((n) => n + 1)];
}

function headlineSentence(detail: ComparisonDetail): string {
  if (!detail.comparison.compatible) {
    return `Comparison incompatible: ${detail.comparison.reason ?? "runs do not share a dataset"}.`;
  }
  const deltaRate = detail.metrics.delta.failureRate;
  const shared = detail.coverage.sharedCaseCount;
  if (deltaRate == null) {
    return `Candidate compared on ${shared} shared cases; failure-rate delta unavailable.`;
  }
  const pts = Math.abs(deltaRate * 100).toFixed(1);
  if (deltaRate > 0) return `Candidate raised failure rate ${pts} pts on ${shared} shared cases.`;
  if (deltaRate < 0) return `Candidate lowered failure rate ${pts} pts on ${shared} shared cases.`;
  return `Candidate held failure rate flat on ${shared} shared cases.`;
}

function DeltaCard({
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
    <div className="rounded-tok border border-line bg-panel px-4 py-[14px]">
      <SectionLabel className="text-[9.5px] tracking-[0.16em]">{label}</SectionLabel>
      <div
        className={cn(
          "mt-2.5 font-heading text-[26px] font-semibold leading-none",
          valueClassName,
        )}
      >
        {value}
      </div>
      <div className="mt-2 font-mono text-[11.5px] text-muted-ink">{sub}</div>
    </div>
  );
}

type MatrixCell = { baseline: string; candidate: string; cases: ComparisonCaseDeltaRecord[] };

function buildMatrix(caseDeltas: ComparisonCaseDeltaRecord[]) {
  const cells = new Map<string, MatrixCell>();
  const baselineLabels = new Set<string>();
  const candidateLabels = new Set<string>();
  for (const delta of caseDeltas) {
    const baseline = caseSideLabel(delta.baselineFailureType, delta.baselineErrorStage);
    const candidate = caseSideLabel(delta.candidateFailureType, delta.candidateErrorStage);
    baselineLabels.add(baseline);
    candidateLabels.add(candidate);
    const key = `${baseline}→${candidate}`;
    const cell = cells.get(key) ?? { baseline, candidate, cases: [] };
    cell.cases.push(delta);
    cells.set(key, cell);
  }
  const order = (labels: Set<string>) =>
    [...labels].sort((a, b) => {
      if (a === "no_failure") return -1;
      if (b === "no_failure") return 1;
      return a.localeCompare(b);
    });
  return {
    cells,
    baselineLabels: order(baselineLabels),
    candidateLabels: order(candidateLabels),
  };
}

export function ComparisonDetailPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const context = useAppRouteContext();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, retry] = useComparisonDetail(reportId);
  const [showRawJson, setShowRawJson] = useState(false);
  const [harvestOpen, setHarvestOpen] = useState(false);
  const [selectedCellKey, setSelectedCellKey] = useState<string | null>(null);

  const section = searchParams.get("section") === "matrix" ? "matrix" : "transitions";
  const detail = state.detail;

  const groups = useMemo(() => {
    if (!detail) return [];
    const byType = new Map<string, ComparisonCaseDeltaRecord[]>();
    for (const delta of detail.caseDeltas) {
      const list = byType.get(delta.transitionType) ?? [];
      list.push(delta);
      byType.set(delta.transitionType, list);
    }
    const orderIndex = (type: string) => {
      const index = TRANSITION_ORDER.indexOf(type);
      return index === -1 ? TRANSITION_ORDER.length : index;
    };
    return [...byType.entries()].sort(
      (a, b) => orderIndex(a[0]) - orderIndex(b[0]) || a[0].localeCompare(b[0]),
    );
  }, [detail]);

  const matrix = useMemo(() => (detail ? buildMatrix(detail.caseDeltas) : null), [detail]);

  if (!reportId) return null;

  const gateRow = context.gateState.status === "ready"
    ? context.gateState.data.rows.find((row) => row.comparisonId === reportId) ?? null
    : null;
  const recommendation = detail?.governanceRecommendation ?? null;

  const evidenceHref = (caseId?: string, transition?: string) => {
    const params = new URLSearchParams();
    if (caseId) params.set("caseId", caseId);
    if (transition) params.set("transition", transition);
    const query = params.toString();
    return `/comparisons/${encodeURIComponent(reportId)}/evidence${query ? `?${query}` : ""}`;
  };

  const changedCount = detail?.caseDeltas.length ?? 0;
  const verdict = detail?.signal.verdict ?? "neutral";
  const bannerTone =
    verdict === "regression" ? "bad" : verdict === "improvement" ? "good" : "neutral";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-end justify-between gap-5 border-b border-line px-7 pb-[14px] pt-[18px]">
        <div className="min-w-0">
          <Link
            to="/comparisons"
            className="font-mono text-[11px] text-accent-text"
          >
            ← comparisons / {reportId}
          </Link>
          {/* The two runs, not the words "Baseline → candidate".
              frontend/README.md: the console "never invents data: every number on screen
              traces to a JSON artifact". This heading was a constant, so a comparison
              between two timestamped runs was titled as though one were named `baseline`
              -- it only ever looked right because the bundled demo's runs happen to carry
              those names. Truncated per DESIGN.md (`truncateRunId`); the full ids are on
              the provenance line at the foot of the page. */}
          <h1 className="mt-2 break-all font-mono text-[22px] font-semibold leading-[1.15] text-ink">
            {detail
              ? `${truncateRunId(detail.comparison.baselineRunId)} → ${truncateRunId(
                  detail.comparison.candidateRunId,
                )}`
              : reportId}
          </h1>
        </div>
        <div className="flex flex-none gap-2">
          <ConsoleButton onClick={() => setShowRawJson((value) => !value)}>
            {showRawJson ? "Close report.json" : "Open report.json"}
          </ConsoleButton>
          <ConsoleButton
            variant="primary"
            onClick={() => setHarvestOpen(true)}
            disabled={!detail || verdict !== "regression"}
          >
            Harvest regressions
          </ConsoleButton>
        </div>
      </header>

      <div className="flex flex-1 flex-col gap-4 overflow-auto px-7 py-5">
        {state.status === "loading" ? (
          <div aria-label="Loading comparison" className="flex flex-col gap-3">
            <div className="h-28 animate-pulse rounded-tok bg-panel" />
            <div className="grid grid-cols-4 gap-3">
              {[0, 1, 2, 3].map((card) => (
                <div key={card} className="h-24 animate-pulse rounded-tok bg-panel" />
              ))}
            </div>
          </div>
        ) : state.status === "incompatible" ? (
          <EmptyState
            title="Comparison failed to load."
            detail={state.message}
            action={<ConsoleButton onClick={retry}>Retry</ConsoleButton>}
          />
        ) : detail ? (
          showRawJson ? (
            <pre className="flex-1 overflow-auto rounded-tok border border-line bg-panel p-4 font-mono text-[11.5px] leading-relaxed">
              {JSON.stringify(detail, null, 2)}
            </pre>
          ) : (
            <>
              <section
                className={cn(
                  "flex items-center gap-7 rounded-tok border p-[22px]",
                  bannerTone === "bad" &&
                    "border-bad-line border-l-[3px] border-l-bad bg-bad-panel",
                  bannerTone === "good" &&
                    "border-line border-l-[3px] border-l-good bg-good-bg",
                  bannerTone === "neutral" && "border-line bg-panel",
                )}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2.5">
                    <StatusChip
                      tone={
                        bannerTone === "bad"
                          ? "bad-strong"
                          : bannerTone === "good"
                            ? "good"
                            : "neutral"
                      }
                      uppercase
                      className="px-[11px] py-1"
                    >
                      {verdict === "regression"
                        ? "Regressed"
                        : verdict === "improvement"
                          ? "Improved"
                          : verdict}
                    </StatusChip>
                    <span className="font-mono text-[11.5px] text-muted-ink">
                      severity {formatScore(detail.signal.severity)}
                      {recommendation ? ` · gate rule ${recommendation.policyRule}` : ""}
                    </span>
                  </div>
                  <div
                    className={cn(
                      "mt-[11px] font-heading text-[26px] font-semibold leading-[1.2]",
                      bannerTone === "bad" && "text-bad-head",
                      bannerTone === "good" && "text-good",
                    )}
                  >
                    {headlineSentence(detail)}
                  </div>
                  <div className="mt-[9px] font-mono text-[12px] text-muted-ink">
                    {detail.transitions.summary.length > 0
                      ? detail.transitions.summary
                          .map((row) => `${row.count} ${row.transitionType}`)
                          .join(" · ")
                      : "no case transitions"}
                  </div>
                </div>
                <div className="w-px self-stretch bg-line" />
                <div className="flex w-[190px] flex-none flex-col gap-2">
                  <SectionLabel className="text-[9.5px] tracking-[0.16em]">CI gate</SectionLabel>
                  {/* An `incompatible` verdict used to short-circuit to "not evaluated"
                      here, before the gate row was ever read -- so a comparison that was
                      the sole reason CI failed reported, on its own page, that the gate
                      had not been evaluated on it. The gate row is the answer whenever
                      one exists; "not evaluated" means exactly one thing now, which is
                      that this comparison is not in the gate's window. */}
                  {gateRow ? (
                    <>
                      <div className="flex items-baseline gap-2">
                        <span
                          className={cn(
                            "font-heading text-[30px] font-semibold leading-none",
                            gateRowTone(gateRow) === "good"
                              ? "text-good"
                              : gateRowTone(gateRow) === "bad"
                                ? "text-bad"
                                : // Blocked without a regression verdict (not comparable,
                                  // coverage dropped, failing cases deleted) is degraded,
                                  // not a regression.
                                  "text-warn",
                          )}
                        >
                          {gateRow.blocked ? "FAIL" : "PASS"}
                        </span>
                        <span className="font-mono text-[11px] text-muted-ink">
                          {gateRow.blocked ? "blocked" : "clear"}
                        </span>
                      </div>
                      <div className="font-mono text-[10.5px] leading-normal text-muted-ink">
                        {/* The engine's block reason, verbatim. Without it a FAIL driven by
                            dropped failing cases or a coverage drop showed only a policy
                            rule that did not explain it. */}
                        {gateRow.blocked && gateRow.blockReason ? (
                          <>
                            {gateRow.blockReason}
                            <br />
                          </>
                        ) : null}
                        {verdict === "incompatible" ? (
                          <>
                            rerun on a shared dataset to gate
                            <br />
                          </>
                        ) : null}
                        policy: {gateRow.policyRule}
                        <br />
                        {gateRow.waiver
                          ? gateRow.waived
                            ? `waived by ${gateRow.waiver.owner}`
                            : "waiver inactive"
                          : "no active waiver"}
                      </div>
                    </>
                  ) : (
                    <div className="font-mono text-[10.5px] leading-normal text-muted-ink">
                      not evaluated
                      <br />
                      {verdict === "incompatible" ? (
                        <>
                          signal discarded · incompatible_signal
                          <br />
                        </>
                      ) : null}
                      run: failure-lab regressions gate
                    </div>
                  )}
                </div>
              </section>

              <div className="grid grid-cols-4 gap-3">
                <DeltaCard
                  label="Failure rate"
                  value={
                    detail.metrics.delta.failureRate != null
                      ? `${formatSignedPts(detail.metrics.delta.failureRate * 100)} pts`
                      : "—"
                  }
                  valueClassName={
                    detail.metrics.delta.failureRate == null
                      ? undefined
                      : detail.metrics.delta.failureRate > 0
                        ? "text-bad"
                        : detail.metrics.delta.failureRate < 0
                          ? "text-good"
                          : undefined
                  }
                  sub={`${formatPercent(detail.metrics.baseline.failureRate)} → ${formatPercent(
                    detail.metrics.candidate.failureRate,
                  )}`}
                />
                <DeltaCard
                  label="Classification coverage"
                  value={
                    detail.metrics.delta.classificationCoverage != null
                      ? `${formatSignedPts(detail.metrics.delta.classificationCoverage * 100)} pts`
                      : "—"
                  }
                  sub={`${formatPercent(
                    detail.metrics.baseline.classificationCoverage,
                  )} → ${formatPercent(detail.metrics.candidate.classificationCoverage)}`}
                />
                <DeltaCard
                  label="Execution success"
                  value={
                    detail.metrics.delta.executionSuccessRate != null
                      ? `${formatSignedPts(detail.metrics.delta.executionSuccessRate * 100)} pts`
                      : "—"
                  }
                  sub={`${formatPercent(
                    detail.metrics.baseline.executionSuccessRate,
                  )} → ${formatPercent(detail.metrics.candidate.executionSuccessRate)}`}
                />
                <DeltaCard
                  label="Shared scope"
                  value={`${detail.coverage.sharedCaseCount} / ${
                    detail.coverage.sharedCaseCount +
                    detail.coverage.baselineOnlyCaseCount +
                    detail.coverage.candidateOnlyCaseCount
                  }`}
                  sub={detail.comparison.dataset ?? "cross-dataset"}
                />
              </div>

              <div className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] gap-[18px]">
                <section className="flex flex-col gap-2.5">
                  <SectionLabel className="tracking-[0.2em]">Top drivers</SectionLabel>
                  {detail.signal.topDrivers.length === 0 ? (
                    <div className="rounded-tok border border-line bg-panel px-4 py-4 font-mono text-[11.5px] text-muted-ink">
                      no failure-type drivers · failure mix unchanged
                    </div>
                  ) : (
                    <table className="w-full border-collapse text-[13px]">
                      <thead>
                        <tr className="border-b border-line">
                          <TableHeadCell>Failure type</TableHeadCell>
                          <TableHeadCell align="right">Δ rate</TableHeadCell>
                          <TableHeadCell>Direction</TableHeadCell>
                          <TableHeadCell>Evidence</TableHeadCell>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.signal.topDrivers.map((driver) => {
                          const isRegression = driver.direction === "regression";
                          return (
                            <tr key={driver.failureType} className="border-b border-line-soft">
                              <td className="px-2 py-[9px] font-mono text-[12.5px] font-semibold">
                                {driver.failureType}
                              </td>
                              <td
                                className={cn(
                                  "px-2 py-[9px] text-right font-mono font-semibold",
                                  isRegression ? "text-bad" : "text-good",
                                )}
                              >
                                {formatSignedPts(driver.delta * 100)}%
                              </td>
                              <td className="px-2 py-[9px]">
                                <StatusChip tone={isRegression ? "bad" : "good"}>
                                  {driver.direction}
                                </StatusChip>
                              </td>
                              <td className="px-2 py-[9px]">
                                <span className="flex flex-wrap gap-1.5">
                                  {driver.caseIds.slice(0, 3).map((caseId) => (
                                    <button
                                      key={caseId}
                                      type="button"
                                      onClick={() => navigate(evidenceHref(caseId))}
                                      className="cursor-pointer rounded-tok-sm border border-line bg-transparent px-[7px] py-[2px] font-mono text-[11px] text-ink hover:bg-accent-wash"
                                    >
                                      {caseId}
                                    </button>
                                  ))}
                                  {driver.caseIds.length > 3 ? (
                                    <span className="font-mono text-[11px] text-muted-ink">
                                      +{driver.caseIds.length - 3}
                                    </span>
                                  ) : null}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  )}
                  <div className="font-mono text-[11px] text-muted-ink">
                    regression {formatScore(detail.signal.regressionScore)} · improvement{" "}
                    {formatScore(detail.signal.improvementScore)} · net{" "}
                    {formatSignedScore(detail.signal.netScore)}
                  </div>
                </section>

                <section className="flex flex-col gap-2.5">
                  <div className="flex items-baseline justify-between gap-3">
                    <SectionLabel className="tracking-[0.2em]">
                      Case transitions · {changedCount} changed
                    </SectionLabel>
                    <div className="flex items-center gap-3">
                      <SegmentedControl
                        aria-label="Transition view"
                        options={[
                          { value: "transitions", label: "Grouped" },
                          { value: "matrix", label: "Matrix" },
                        ]}
                        value={section}
                        onChange={(value) => {
                          const next = new URLSearchParams(searchParams);
                          if (value === "matrix") {
                            next.set("section", "matrix");
                          } else {
                            next.delete("section");
                          }
                          setSearchParams(next, { replace: true });
                        }}
                      />
                      <Link
                        to={evidenceHref()}
                        className="font-mono text-[11px] text-accent-text"
                      >
                        open evidence →
                      </Link>
                    </div>
                  </div>

                  {changedCount === 0 ? (
                    <div className="rounded-tok border border-line bg-panel px-4 py-4 font-mono text-[11.5px] text-muted-ink">
                      no changed cases between the two runs
                    </div>
                  ) : section === "transitions" ? (
                    <div className="overflow-hidden rounded-tok border border-line">
                      {groups.map(([transitionType, cases]) => {
                        const tone = transitionGroupTone(transitionType);
                        return (
                          <div key={transitionType}>
                            <div
                              className={cn(
                                "flex items-center justify-between border-b border-line px-3 py-2",
                                tone === "bad" && "bg-bad-bg",
                                tone === "good" && "bg-good-bg",
                                tone === "neutral" && "bg-panel",
                              )}
                            >
                              <span
                                className={cn(
                                  "font-heading text-[11.5px] font-semibold uppercase tracking-[0.08em]",
                                  tone === "bad" && "text-bad",
                                  tone === "good" && "text-good",
                                )}
                              >
                                {transitionType}
                              </span>
                              <span
                                className={cn(
                                  "font-mono text-[11px]",
                                  tone === "bad"
                                    ? "text-bad"
                                    : tone === "good"
                                      ? "text-good"
                                      : "text-muted-ink",
                                )}
                              >
                                {cases.length} {cases.length === 1 ? "case" : "cases"} ·{" "}
                                {Math.round((cases.length / changedCount) * 100)}%
                              </span>
                            </div>
                            {cases.map((delta, index) => (
                              <button
                                key={delta.caseId}
                                type="button"
                                onClick={() => navigate(evidenceHref(delta.caseId))}
                                className={cn(
                                  "block w-full cursor-pointer bg-transparent px-3 py-2.5 text-left font-body text-ink hover:bg-accent-wash",
                                  index < cases.length - 1 && "border-b border-line-soft",
                                )}
                              >
                                <span className="flex items-center gap-2">
                                  <span className="font-mono text-[12px] font-semibold">
                                    {delta.caseId}
                                  </span>
                                  <span className="font-mono text-[11px] text-muted-ink">
                                    {caseSideLabel(
                                      delta.baselineFailureType,
                                      delta.baselineErrorStage,
                                    )}{" "}
                                    →{" "}
                                    {caseSideLabel(
                                      delta.candidateFailureType,
                                      delta.candidateErrorStage,
                                    )}
                                  </span>
                                </span>
                                <span className="mt-1 block overflow-hidden text-ellipsis whitespace-nowrap text-[12.5px] text-muted-ink">
                                  {delta.prompt}
                                </span>
                              </button>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  ) : matrix ? (
                    <div className="flex flex-col gap-2.5">
                      <div className="overflow-x-auto rounded-tok border border-line">
                        <table className="w-full border-collapse text-[12px]">
                          <thead>
                            <tr className="border-b border-line">
                              <TableHeadCell className="w-[150px]">
                                baseline ↓ / cand →
                              </TableHeadCell>
                              {matrix.candidateLabels.map((label) => (
                                <TableHeadCell key={label} align="center">
                                  {label.replace("instruction_following", "instruction")}
                                </TableHeadCell>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="font-mono">
                            {matrix.baselineLabels.map((baseline) => (
                              <tr key={baseline} className="border-b border-line-soft">
                                <td className="px-2 py-[7px] font-semibold">{baseline}</td>
                                {matrix.candidateLabels.map((candidate) => {
                                  const key = `${baseline}→${candidate}`;
                                  const cell = matrix.cells.get(key);
                                  if (!cell) {
                                    return (
                                      <td
                                        key={candidate}
                                        className="px-2 py-[7px] text-center text-muted-ink"
                                      >
                                        ·
                                      </td>
                                    );
                                  }
                                  const tone =
                                    candidate === "no_failure"
                                      ? "good"
                                      : baseline === "no_failure"
                                        ? "bad"
                                        : "neutral";
                                  return (
                                    <td key={candidate} className="p-0 text-center">
                                      <button
                                        type="button"
                                        onClick={() =>
                                          setSelectedCellKey(
                                            selectedCellKey === key ? null : key,
                                          )
                                        }
                                        className={cn(
                                          "w-full cursor-pointer border-0 px-2 py-[7px] font-mono text-[12px] font-semibold",
                                          tone === "bad" && "bg-bad-bg text-bad",
                                          tone === "good" && "bg-good-bg text-good",
                                          tone === "neutral" && "bg-panel text-ink",
                                          selectedCellKey === key &&
                                            "outline outline-2 outline-[var(--accent)]",
                                        )}
                                      >
                                        {cell.cases.length}
                                      </button>
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="font-mono text-[11px] text-muted-ink">
                        matrix covers the {changedCount} changed cases · unchanged cases are not
                        broken out per type · click a cell to list its cases
                      </div>
                      {selectedCellKey && matrix.cells.get(selectedCellKey) ? (
                        <div className="rounded-tok border border-line bg-panel p-3">
                          <SectionLabel className="text-[9.5px] tracking-[0.16em]">
                            Cell · {selectedCellKey}
                          </SectionLabel>
                          <div className="mt-2 flex flex-col gap-1">
                            {matrix.cells.get(selectedCellKey)!.cases.map((delta) => (
                              <button
                                key={delta.caseId}
                                type="button"
                                onClick={() => navigate(evidenceHref(delta.caseId))}
                                className="cursor-pointer rounded-tok border border-line bg-ground px-2.5 py-2 text-left font-mono text-[12px] text-ink hover:bg-accent-wash"
                              >
                                {delta.caseId}
                                <span className="ml-2 text-[11px] text-muted-ink">
                                  {delta.transitionType}
                                </span>
                              </button>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </section>
              </div>

              {recommendation ? (
                <details className="rounded-tok border border-line bg-panel">
                  <summary className="cursor-pointer px-4 py-3 font-heading text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-ink">
                    Governance · {recommendation.action} · {recommendation.policyRule}
                  </summary>
                  <div className="flex flex-col gap-3 border-t border-line px-4 py-4">
                    <div className="text-[13px] leading-relaxed">
                      {recommendation.rationale}
                    </div>
                    <div className="grid grid-cols-2 gap-4 font-mono text-[11.5px] text-muted-ink">
                      <div>
                        family {recommendation.matchedFamily.familyId} ·{" "}
                        {recommendation.matchedFamily.exists
                          ? `${recommendation.matchedFamily.versionCount} versions · ${recommendation.matchedFamily.currentCaseCount} cases`
                          : "new family"}
                        <br />
                        proposed +{recommendation.matchedFamily.proposedAdditionCount} →{" "}
                        {recommendation.matchedFamily.projectedCaseCount} cases
                        {recommendation.matchedFamily.duplicateCaseCount > 0
                          ? ` · ${recommendation.matchedFamily.duplicateCaseCount} duplicates`
                          : ""}
                      </div>
                      <div>
                        {recommendation.escalation
                          ? `escalation ${recommendation.escalation.status} · score ${formatScore(
                              recommendation.escalation.score,
                            )} · ${recommendation.escalation.severityBand}`
                          : "no escalation context"}
                        <br />
                        {recommendation.lifecycleRecommendation
                          ? `lifecycle ${recommendation.lifecycleRecommendation.action} · ${recommendation.lifecycleRecommendation.healthCondition}`
                          : "no lifecycle action recommended"}
                      </div>
                    </div>
                  </div>
                </details>
              ) : null}

              <div className="font-mono text-[10.5px] text-muted-ink">
                {truncateRunId(detail.comparison.baselineRunId)} →{" "}
                {truncateRunId(detail.comparison.candidateRunId)} · reports/
                {detail.comparison.reportId}/report.json
              </div>
            </>
          )
        ) : null}
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
