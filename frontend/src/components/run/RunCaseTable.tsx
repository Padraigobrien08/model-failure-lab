import { Badge } from "@/components/ui/badge";
import type { RunCaseRecord } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";
import { cn } from "@/lib/utils";

type RunCaseTableProps = {
  cases: RunCaseRecord[];
  selectedCaseId: string | null;
  onSelectCase: (caseId: string) => void;
};

function MobileLabel({ children }: { children: string }) {
  return (
    <span className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground md:hidden">
      {children}
    </span>
  );
}

function describeObservedFailure(caseRow: RunCaseRecord) {
  if (caseRow.error) {
    return formatLabel(caseRow.error.stage);
  }

  const observedFailure =
    caseRow.expectation.observedFailure ?? caseRow.classification?.failure ?? null;
  if (!observedFailure) {
    return "No classification";
  }

  if (observedFailure.failureSubtype) {
    return `${formatLabel(observedFailure.failureType)} / ${formatLabel(
      observedFailure.failureSubtype,
    )}`;
  }

  return formatLabel(observedFailure.failureType);
}

function verdictTone(caseRow: RunCaseRecord): "default" | "accent" | "muted" {
  if (caseRow.error) {
    return "default";
  }

  if (
    caseRow.expectation.verdict === "matched_expected" ||
    caseRow.expectation.verdict === "no_failure_as_expected"
  ) {
    return "accent";
  }

  return "muted";
}

export function RunCaseTable({
  cases,
  selectedCaseId,
  onSelectCase,
}: RunCaseTableProps) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-border/70 bg-card/75 shadow-panel">
      <div className="md:overflow-x-auto">
        <table
          aria-label="Run cases"
          className="block min-w-full border-collapse text-sm md:table"
        >
          <thead className="hidden bg-background/55 md:table-header-group">
            <tr className="border-b border-border/70 text-left">
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Case
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Verdict
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Observed
              </th>
              <th className="px-4 py-3 font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Tags
              </th>
            </tr>
          </thead>
          <tbody className="block md:table-row-group">
            {cases.map((caseRow) => {
              const isSelected = caseRow.caseId === selectedCaseId;

              return (
                <tr
                  key={caseRow.caseId}
                  tabIndex={0}
                  role="button"
                  data-active-case={isSelected ? "true" : undefined}
                  aria-label={`Inspect case ${caseRow.caseId}`}
                  aria-pressed={isSelected}
                  className={cn(
                    "mb-3 block cursor-pointer rounded-[20px] border border-border/55 bg-background/25 p-4 align-top transition-colors last:mb-0 hover:bg-background/50 focus-visible:bg-background/50 focus-visible:outline-none md:mb-0 md:table-row md:rounded-none md:border-x-0 md:border-b md:border-t-0 md:bg-transparent md:p-0",
                    isSelected ? "border-primary/45 bg-primary/[0.08] md:bg-primary/[0.05]" : "",
                  )}
                  onClick={() => onSelectCase(caseRow.caseId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelectCase(caseRow.caseId);
                    }
                  }}
                >
                  <td className="block px-0 py-2 md:table-cell md:px-4 md:py-3">
                    <MobileLabel>Case</MobileLabel>
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-mono text-[11px] text-foreground">{caseRow.caseId}</p>
                        {isSelected ? (
                          <>
                            <span
                              aria-hidden="true"
                              className="h-1.5 w-8 rounded-full bg-primary/80"
                            />
                            <Badge tone="accent">Active case</Badge>
                          </>
                        ) : null}
                      </div>
                      <p className="max-w-[24rem] text-sm text-muted-foreground">
                        {caseRow.prompt}
                      </p>
                    </div>
                  </td>
                  <td className="block px-0 py-2 md:table-cell md:px-4 md:py-3">
                    <MobileLabel>Verdict</MobileLabel>
                    <Badge tone={verdictTone(caseRow)}>
                      {caseRow.error
                        ? "Execution Error"
                        : formatLabel(caseRow.expectation.verdict ?? "unknown")}
                    </Badge>
                  </td>
                  <td className="block px-0 py-2 text-foreground md:table-cell md:px-4 md:py-3">
                    <MobileLabel>Observed</MobileLabel>
                    {describeObservedFailure(caseRow)}
                  </td>
                  <td className="block px-0 py-2 md:table-cell md:px-4 md:py-3">
                    <MobileLabel>Tags</MobileLabel>
                    <div className="flex flex-wrap gap-2">
                      {caseRow.tags.length > 0 ? (
                        caseRow.tags.map((tag) => (
                          <Badge key={`${caseRow.caseId}-${tag}`} tone="muted">
                            {tag}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-sm text-muted-foreground">No tags</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
