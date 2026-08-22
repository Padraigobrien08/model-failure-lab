import { useNavigate } from "react-router-dom";

import { useAppRouteContext } from "@/app/router";
import {
  ConsoleButton,
  EmptyState,
  RouteHeader,
  SectionLabel,
  StatusChip,
  TableHeadCell,
  formatScore,
  rowActivationProps,
} from "@/components/console/primitives";
import type { GateResponse } from "@/lib/artifacts/extended";
import { cn } from "@/lib/utils";

const GATE_COMMAND = "run: failure-lab regressions gate";

function policyEntries(policy: GateResponse["policy"]): [string, string][] {
  return Object.entries(policy)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => [key, value == null ? "—" : String(value)]);
}

function GateBanner({ gate }: { gate: GateResponse }) {
  if (gate.rows.length === 0) {
    return (
      <div className="rounded-tok border border-line bg-panel p-[20px_22px]">
        <div className="font-body text-[13.5px] text-ink">No comparisons evaluated.</div>
        <div className="mt-1.5 font-mono text-[11.5px] text-muted-ink">{GATE_COMMAND}</div>
      </div>
    );
  }
  const blockingCount = gate.rows.filter((row) => row.blocked).length;
  const policyRule = gate.rows.find((row) => row.blocked)?.policyRule ?? gate.rows[0].policyRule;
  if (gate.blocked) {
    return (
      <div className="rounded-tok border border-bad-line border-l-[3px] border-l-bad bg-bad-panel p-[20px_22px]">
        <StatusChip tone="bad-strong" uppercase>
          FAIL
        </StatusChip>
        <div className="mt-2 font-heading text-[26px] font-semibold leading-[1.15] text-bad-head">
          {blockingCount} {blockingCount === 1 ? "comparison blocks" : "comparisons block"} the
          gate.
        </div>
        <div className="mt-1.5 font-mono text-[11.5px] text-muted-ink">{policyRule}</div>
        <div className="mt-2.5 font-mono text-[11.5px] text-ink">
          harvest the regression: failure-lab regressions apply · or waive it: failure-lab
          regressions gate --waivers waivers.yml
        </div>
      </div>
    );
  }
  return (
    <div className="rounded-tok border border-line border-l-[3px] border-l-good bg-good-bg p-[20px_22px]">
      <StatusChip tone="good" uppercase>
        PASS
      </StatusChip>
      <div className="mt-2 font-heading text-[26px] font-semibold leading-[1.15] text-good">
        All recent comparisons pass the gate.
      </div>
      <div className="mt-1.5 font-mono text-[11.5px] text-muted-ink">{policyRule}</div>
    </div>
  );
}

export function GatePage() {
  const context = useAppRouteContext();
  const navigate = useNavigate();
  const gateState = context.gateState;
  const isLoading = gateState.status === "loading" || gateState.status === "idle";
  const gate = gateState.status === "ready" ? gateState.data : null;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <RouteHeader eyebrow="Governance" title="Regression gate" />

      <div className="flex-1 overflow-auto px-7 pb-[22px] pt-[18px]">
        {isLoading ? (
          <div role="status" aria-label="Loading gate" className="flex flex-col gap-2">
            {[0, 1, 2, 3].map((row) => (
              <div key={row} className="h-9 animate-pulse rounded-tok bg-panel" />
            ))}
          </div>
        ) : gateState.status === "incompatible" ? (
          <EmptyState
            title="Regression gate failed to load."
            detail={gateState.message}
            action={<ConsoleButton onClick={context.reloadGate}>Retry</ConsoleButton>}
          />
        ) : gate ? (
          <div className="flex flex-col gap-[22px]">
            <GateBanner gate={gate} />

            <div className="flex flex-col gap-2">
              <SectionLabel>Decisions</SectionLabel>
              <span className="text-[12px] text-muted-ink">
                {gate.rows.length} {gate.rows.length === 1 ? "decision" : "decisions"}
              </span>
              {gate.rows.length === 0 ? (
                <EmptyState title="No comparisons evaluated." detail={GATE_COMMAND} />
              ) : (
                <table className="w-full border-collapse text-[13.5px]">
                  <thead>
                    <tr className="border-b border-line">
                      <TableHeadCell>Comparison id</TableHeadCell>
                      <TableHeadCell>Action</TableHeadCell>
                      <TableHeadCell align="right">Severity</TableHeadCell>
                      <TableHeadCell>Policy rule</TableHeadCell>
                      <TableHeadCell>Blocked</TableHeadCell>
                      <TableHeadCell>Waiver</TableHeadCell>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-[12.5px]">
                    {gate.rows.map((row, index) => (
                      <tr
                        key={row.comparisonId}
                        {...rowActivationProps(() =>
                          navigate(`/comparisons/${encodeURIComponent(row.comparisonId)}`),
                        )}
                        className={cn(
                          "cursor-pointer hover:bg-accent-wash",
                          index < gate.rows.length - 1 && "border-b border-line-soft",
                        )}
                      >
                        <td className="px-2 py-[9px] font-semibold">{row.comparisonId}</td>
                        <td className="px-2 py-[9px] text-muted-ink">{row.action}</td>
                        <td
                          className={cn(
                            "px-2 py-[9px] text-right",
                            row.blocked ? "font-semibold text-bad" : "text-muted-ink",
                          )}
                        >
                          {formatScore(row.severity)}
                        </td>
                        <td className="px-2 py-[9px] text-[11.5px] text-muted-ink">
                          {row.policyRule}
                        </td>
                        <td className="px-2 py-[9px]">
                          <StatusChip tone={row.blocked ? "bad" : "good"}>
                            {row.blocked ? "blocked" : "clear"}
                          </StatusChip>
                        </td>
                        <td className="px-2 py-[9px]">
                          {row.waiver ? (
                            <span className="inline-flex items-center gap-2">
                              <span className="text-[11px] text-muted-ink">
                                {row.waiver.owner ?? "—"} · expires {row.waiver.expiresAt ?? "—"}
                              </span>
                              {row.waived ? (
                                <StatusChip tone="warn">waived</StatusChip>
                              ) : (
                                <StatusChip tone="neutral">inactive</StatusChip>
                              )}
                            </span>
                          ) : (
                            <span className="text-muted-ink">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <SectionLabel>Policy</SectionLabel>
              <div className="rounded-tok border border-line bg-panel px-4 py-3">
                {policyEntries(gate.policy).map(([key, value], index, entries) => (
                  <div
                    key={key}
                    className={cn(
                      "flex items-center justify-between gap-6 py-[6px] font-mono text-[11.5px]",
                      index < entries.length - 1 && "border-b border-line-soft",
                    )}
                  >
                    <span className="text-muted-ink">{key}</span>
                    <span className="text-ink">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
