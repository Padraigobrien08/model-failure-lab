import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { healthTone } from "@/app/routes/DatasetsPage";
import { verdictTone } from "@/app/routes/ComparisonsPage";
import {
  ConsoleButton,
  EmptyState,
  SectionLabel,
  StatusChip,
  TableHeadCell,
  formatPercent,
  formatScore,
  formatTimestamp,
} from "@/components/console/primitives";
import { loadArtifactDatasetVersions } from "@/lib/artifacts/load";
import type { ArtifactDatasetVersionsResponse } from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

type FamilyState =
  | { status: "loading"; data: null; message: null }
  | { status: "ready"; data: ArtifactDatasetVersionsResponse; message: null }
  | { status: "incompatible"; data: null; message: string };

function StatCard({
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
      <SectionLabel>{label}</SectionLabel>
      <div
        className={cn(
          "mt-1.5 font-heading text-[26px] font-semibold leading-none text-ink",
          valueClassName,
        )}
      >
        {value}
      </div>
      <div className="mt-1.5 font-mono text-[10.5px] text-muted-ink">{sub}</div>
    </div>
  );
}

function DetailsPanel({
  title,
  count,
  children,
}: {
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <details className="rounded-tok border border-line bg-panel">
      <summary className="flex cursor-pointer items-center justify-between px-4 py-3 font-heading text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-ink">
        {title}
        <span className="font-mono text-[11px] font-normal normal-case tracking-normal">
          {count}
        </span>
      </summary>
      <div className="border-t border-line-soft px-4 py-3">{children}</div>
    </details>
  );
}

function NoneRecorded() {
  return <div className="font-mono text-[11px] text-muted-ink">none recorded</div>;
}

function ComparisonLink({ comparisonId }: { comparisonId: string }) {
  return (
    <Link
      to={`/comparisons/${encodeURIComponent(comparisonId)}`}
      className="font-mono text-[11px] text-accent-text hover:underline"
    >
      {comparisonId}
    </Link>
  );
}

export function DatasetFamilyPage() {
  const { familyId = "" } = useParams<{ familyId: string }>();
  const [state, setState] = useState<FamilyState>({
    status: "loading",
    data: null,
    message: null,
  });

  const load = useCallback(() => {
    let cancelled = false;
    setState({ status: "loading", data: null, message: null });
    loadArtifactDatasetVersions(familyId)
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data, message: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "incompatible",
            data: null,
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [familyId]);

  useEffect(() => load(), [load]);

  const data = state.status === "ready" ? state.data : null;

  const versions = useMemo(() => {
    if (!data) return [];
    return [...data.versions].sort(
      (a, b) => b.versionNumber - a.versionNumber || a.datasetId.localeCompare(b.datasetId),
    );
  }, [data]);

  const lifecycleActions = useMemo(() => {
    if (!data) return [];
    return [...data.lifecycleActions].sort(
      (a, b) => b.appliedAt.localeCompare(a.appliedAt) || a.actionId.localeCompare(b.actionId),
    );
  }, [data]);

  const portfolioPlans = useMemo(() => {
    if (!data) return [];
    return [...data.portfolioPlans].sort(
      (a, b) => b.createdAt.localeCompare(a.createdAt) || a.planId.localeCompare(b.planId),
    );
  }, [data]);

  const planExecutions = useMemo(() => {
    if (!data) return [];
    return [...data.planExecutions].sort(
      (a, b) =>
        b.createdAt.localeCompare(a.createdAt) || a.executionId.localeCompare(b.executionId),
    );
  }, [data]);

  const outcomes = useMemo(() => {
    if (!data) return [];
    return [...data.outcomes].sort(
      (a, b) =>
        b.recordedAt.localeCompare(a.recordedAt) ||
        a.attestation.attestationId.localeCompare(b.attestation.attestationId),
    );
  }, [data]);

  const latest = versions[0] ?? null;
  const health = data?.history.datasetHealth ?? null;
  const portfolioItem = data?.portfolioItem ?? null;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="border-b border-line px-7 pb-[15px] pt-[22px]">
        <Link to="/datasets" className="font-mono text-[11px] text-accent-text hover:underline">
          ← datasets
        </Link>
        <h1 className="mt-1.5 font-mono text-[22px] font-semibold leading-[1.1] text-ink">
          {familyId}
        </h1>
      </header>

      {state.status === "loading" ? (
        <div
          aria-label="Loading dataset family"
          className="flex-1 overflow-auto px-7 pb-[22px] pt-5"
        >
          <div className="grid grid-cols-4 gap-3">
            {[0, 1, 2, 3].map((card) => (
              <div key={card} className="h-[92px] animate-pulse rounded-tok bg-panel" />
            ))}
          </div>
          <div className="mt-4 flex flex-col gap-2">
            {[0, 1, 2].map((row) => (
              <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
            ))}
          </div>
        </div>
      ) : state.status === "incompatible" ? (
        <div className="flex-1 overflow-auto px-7 pb-[22px]">
          <EmptyState
            title="Dataset family failed to load."
            detail={state.message}
            action={<ConsoleButton onClick={load}>Retry</ConsoleButton>}
          />
        </div>
      ) : (
        <div className="flex flex-1 flex-col gap-4 overflow-auto px-7 pb-[22px] pt-5">
          <div className="grid grid-cols-4 gap-3">
            <StatCard
              label="Versions"
              value={String(versions.length)}
              sub={`latest ${latest?.versionTag ?? "—"}`}
            />
            <StatCard
              label="Cases"
              value={latest ? String(latest.caseCount) : "—"}
              sub={latest?.datasetId ?? "—"}
            />
            <StatCard
              label="Health"
              value={health?.healthLabel ?? "—"}
              valueClassName="text-[20px]"
              sub={health?.trend.label ?? "—"}
            />
            <StatCard
              label="Recent fail rate"
              value={formatPercent(health?.recentFailRate ?? null)}
              sub={`previous ${formatPercent(health?.previousFailRate ?? null)}`}
            />
          </div>

          <div className="flex flex-col gap-2">
            <SectionLabel>Versions</SectionLabel>
            {versions.length === 0 ? (
              <div className="font-mono text-[11px] text-muted-ink">
                none recorded · read datasets/ · run: failure-lab dataset promote &lt;draft&gt;
              </div>
            ) : (
              <table className="w-full border-collapse text-[13.5px]">
                <thead>
                  <tr className="border-b border-line">
                    <TableHeadCell>Version</TableHeadCell>
                    <TableHeadCell>Dataset id</TableHeadCell>
                    <TableHeadCell align="right">Cases</TableHeadCell>
                    <TableHeadCell>Created</TableHeadCell>
                    <TableHeadCell>Source comparison</TableHeadCell>
                    <TableHeadCell>Verdict</TableHeadCell>
                    <TableHeadCell align="right">Severity</TableHeadCell>
                    <TableHeadCell>Path</TableHeadCell>
                  </tr>
                </thead>
                <tbody className="font-mono text-[12.5px]">
                  {versions.map((version, index) => (
                    <tr
                      key={version.datasetId}
                      className={cn(
                        index < versions.length - 1 && "border-b border-line-soft",
                      )}
                    >
                      <td className="px-2 py-[9px] font-semibold">{version.versionTag}</td>
                      <td className="px-2 py-[9px] text-muted-ink">{version.datasetId}</td>
                      <td className="px-2 py-[9px] text-right text-muted-ink">
                        {version.caseCount}
                      </td>
                      <td className="px-2 py-[9px] text-muted-ink">
                        {version.createdAt ? formatTimestamp(version.createdAt) : "—"}
                      </td>
                      <td className="px-2 py-[9px]">
                        {version.sourceComparisonId ? (
                          <Link
                            to={`/comparisons/${encodeURIComponent(version.sourceComparisonId)}`}
                            className="text-accent-text hover:underline"
                          >
                            {version.sourceComparisonId}
                          </Link>
                        ) : (
                          <span className="text-muted-ink">—</span>
                        )}
                      </td>
                      <td className="px-2 py-[9px]">
                        {version.signalVerdict ? (
                          <StatusChip tone={verdictTone(version.signalVerdict)}>
                            {version.signalVerdict}
                          </StatusChip>
                        ) : (
                          <span className="text-muted-ink">—</span>
                        )}
                      </td>
                      <td className="px-2 py-[9px] text-right text-muted-ink">
                        {version.severity != null ? formatScore(version.severity) : "—"}
                      </td>
                      <td className="px-2 py-[9px] font-mono text-[10.5px] text-muted-ink">
                        {version.path}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <SectionLabel>Lifecycle actions</SectionLabel>
            {lifecycleActions.length === 0 ? (
              <div className="font-mono text-[11px] text-muted-ink">
                none recorded · read governance/lifecycle_actions/{familyId}/
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {lifecycleActions.map((action) => (
                  <div
                    key={action.actionId}
                    className="rounded-tok border border-line-soft px-3 py-[10px]"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[12.5px] font-semibold">
                        {action.action}
                      </span>
                      <StatusChip tone="neutral" className="font-mono text-[10.5px]">
                        {action.healthCondition}
                      </StatusChip>
                    </div>
                    <div className="mt-1 font-body text-[12.5px] text-ink">
                      {action.rationale}
                    </div>
                    <div className="mt-1 font-mono text-[10.5px] text-muted-ink">
                      {formatTimestamp(action.appliedAt)} · {action.status} · {action.actionId}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <DetailsPanel title="Portfolio" count={portfolioItem ? 1 : 0}>
            {portfolioItem ? (
              <div className="flex flex-col gap-1.5">
                <div className="font-mono text-[11px] text-ink">
                  {portfolioItem.priorityBand} · rank {portfolioItem.priorityRank} · score{" "}
                  {formatScore(portfolioItem.priorityScore)}
                </div>
                <div className="font-mono text-[11px] text-muted-ink">
                  actionability {portfolioItem.actionability}
                </div>
                <div className="font-body text-[12.5px] text-ink">{portfolioItem.rationale}</div>
                <div className="flex items-center gap-2">
                  <StatusChip tone={healthTone(portfolioItem.healthLabel)}>
                    {portfolioItem.healthLabel}
                  </StatusChip>
                  <StatusChip tone="neutral">{portfolioItem.trendLabel}</StatusChip>
                </div>
                <div className="font-mono text-[10.5px] text-muted-ink">
                  {portfolioItem.recentRegressionCount} recent{" "}
                  {portfolioItem.recentRegressionCount === 1 ? "regression" : "regressions"}
                </div>
                {portfolioItem.comparisonRefs.length > 0 ? (
                  <div className="flex flex-col gap-1">
                    {[...portfolioItem.comparisonRefs]
                      .sort(
                        (a, b) =>
                          b.createdAt.localeCompare(a.createdAt) ||
                          a.comparisonId.localeCompare(b.comparisonId),
                      )
                      .map((ref) => (
                        <ComparisonLink key={ref.comparisonId} comparisonId={ref.comparisonId} />
                      ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <NoneRecorded />
            )}
          </DetailsPanel>

          <DetailsPanel title="Plans" count={portfolioPlans.length}>
            {portfolioPlans.length === 0 ? (
              <NoneRecorded />
            ) : (
              <div className="flex flex-col gap-2">
                {portfolioPlans.map((plan) => (
                  <div key={plan.planId} className="flex flex-col gap-0.5">
                    <div className="font-mono text-[11px] text-ink">
                      {plan.planId} · {plan.status}
                    </div>
                    <div className="font-body text-[12.5px] text-ink">{plan.rationale}</div>
                    <div className="font-mono text-[10.5px] text-muted-ink">
                      {plan.impact.actionCount}{" "}
                      {plan.impact.actionCount === 1 ? "action" : "actions"} ·{" "}
                      {plan.impact.projectedCaseCount} projected cases
                    </div>
                  </div>
                ))}
              </div>
            )}
          </DetailsPanel>

          <DetailsPanel title="Executions" count={planExecutions.length}>
            {planExecutions.length === 0 ? (
              <NoneRecorded />
            ) : (
              <div className="flex flex-col gap-2">
                {planExecutions.map((execution) => (
                  <div key={execution.executionId} className="flex flex-col gap-0.5">
                    <div className="font-mono text-[11px] text-ink">
                      {execution.executionId} · {execution.status}
                    </div>
                    <div className="font-mono text-[10.5px] text-muted-ink">
                      {execution.completedCheckpointCount}/{execution.totalActionCount}{" "}
                      checkpoints · mode {execution.mode}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </DetailsPanel>

          <DetailsPanel title="Outcomes" count={outcomes.length}>
            {outcomes.length === 0 ? (
              <NoneRecorded />
            ) : (
              <div className="flex flex-col gap-2">
                {outcomes.map((outcome) => (
                  <div
                    key={outcome.attestation.attestationId}
                    className="flex flex-col gap-0.5"
                  >
                    <div className="font-mono text-[11px] text-ink">
                      {outcome.attestation.attestationId} · attestation{" "}
                      {outcome.attestation.state}
                    </div>
                    {outcome.attestation.verdict ? (
                      <>
                        <div className="font-mono text-[10.5px] text-muted-ink">
                          verdict {outcome.attestation.verdict.status}
                        </div>
                        <div className="font-body text-[12.5px] text-ink">
                          {outcome.attestation.verdict.rationale}
                        </div>
                      </>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </DetailsPanel>
        </div>
      )}
    </div>
  );
}
