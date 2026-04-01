import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  ComparisonCaseDeltaRecord,
  ComparisonTransitionSummaryRow,
} from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

type ComparisonTransitionGroupsProps = {
  summary: ComparisonTransitionSummaryRow[];
  caseDeltas: ComparisonCaseDeltaRecord[];
  selectedCaseId: string | null;
  highlightedTransitionType?: string | null;
  setGroupRef?: (transitionType: string) => (element: HTMLDivElement | null) => void;
  onSelectCase: (caseId: string) => void;
};

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function ComparisonTransitionGroups({
  summary,
  caseDeltas,
  selectedCaseId,
  highlightedTransitionType = null,
  setGroupRef,
  onSelectCase,
}: ComparisonTransitionGroupsProps) {
  const caseMap = new Map(caseDeltas.map((caseRow) => [caseRow.caseId, caseRow]));
  const totalChangedCases = summary.reduce((total, row) => total + row.count, 0);

  if (summary.length === 0) {
    return (
      <Card className="rounded-[24px] border border-border/70 bg-card/70 shadow-panel">
        <CardHeader>
          <CardTitle>No grouped transition changes are available.</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          This saved comparison has no changed shared-case transitions to inspect.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {summary.map((group) => {
        const cases = group.caseIds
          .map((caseId) => caseMap.get(caseId))
          .filter((caseRow): caseRow is ComparisonCaseDeltaRecord => caseRow !== undefined);

        return (
          <Card
            key={group.transitionType}
            ref={setGroupRef?.(group.transitionType)}
            id={`comparison-transition-${group.transitionType}`}
            data-transition-group={group.transitionType}
            className={cn(
              "rounded-[24px] border border-border/70 bg-card/70 shadow-panel transition-colors duration-300",
              highlightedTransitionType === group.transitionType
                ? "border-primary/35 bg-primary/[0.05]"
                : "",
            )}
          >
            <CardHeader className="space-y-3 pb-4">
              <div className="flex flex-wrap items-center gap-3">
                <Badge tone="accent">{group.label}</Badge>
                <Badge tone="muted">{group.count} changed</Badge>
                <Badge tone="default">
                  {totalChangedCases > 0 ? formatPercent(group.count / totalChangedCases) : "0.0%"}
                </Badge>
              </div>
              <CardTitle className="text-lg">{group.label}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {cases.map((caseRow) => {
                const isSelected = caseRow.caseId === selectedCaseId;
                return (
                  <button
                    key={caseRow.caseId}
                    type="button"
                    aria-label={`Inspect transition case ${caseRow.caseId}`}
                    className={cn(
                      "flex w-full flex-col gap-2 rounded-[18px] border border-border/60 bg-background/60 px-4 py-3 text-left transition-colors hover:bg-background focus-visible:bg-background focus-visible:outline-none",
                      isSelected ? "border-primary/40 bg-background" : "",
                    )}
                    onClick={() => onSelectCase(caseRow.caseId)}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <span className="font-mono text-xs text-foreground">{caseRow.caseId}</span>
                      <div className="flex flex-wrap gap-2">
                        {caseRow.tags.map((tag) => (
                          <Badge key={`${caseRow.caseId}-${tag}`} tone="muted">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <p className="text-sm leading-6 text-foreground">{caseRow.prompt}</p>
                  </button>
                );
              })}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
