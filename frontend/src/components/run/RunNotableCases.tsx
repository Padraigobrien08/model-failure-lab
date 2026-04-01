import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RunCaseRecord } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";
import { cn } from "@/lib/utils";

type RunNotableCasesProps = {
  cases: RunCaseRecord[];
  selectedCaseId?: string | null;
  onSelectCase?: (caseId: string) => void;
};

function summarizeFailure(caseRow: RunCaseRecord): string {
  if (caseRow.classification === null) {
    return "No classification";
  }

  const { failureType, failureSubtype } = caseRow.classification.failure;
  return failureSubtype ? `${formatLabel(failureType)} / ${formatLabel(failureSubtype)}` : formatLabel(failureType);
}

export function RunNotableCases({
  cases,
  selectedCaseId = null,
  onSelectCase,
}: RunNotableCasesProps) {
  return (
    <section className="space-y-4" aria-label="Notable cases">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Stage 4 · Notable cases
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Notable cases worth opening first
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground">
          These are the fastest entry points into the run. Open one to jump straight into the
          evidence panel without losing the broader context.
        </p>
      </div>

      {cases.length > 0 ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {cases.map((caseRow) => (
            <Card
              key={caseRow.caseId}
              className={cn(
                "rounded-[24px] bg-card/75 transition-colors",
                selectedCaseId === caseRow.caseId ? "border-primary/35 bg-primary/5" : "",
              )}
            >
              <button
                type="button"
                aria-label={`Inspect notable case ${caseRow.caseId}`}
                className="block w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                onClick={() => onSelectCase?.(caseRow.caseId)}
              >
                <CardHeader className="space-y-3 pb-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="accent">{caseRow.caseId}</Badge>
                    {caseRow.expectation.verdict ? (
                      <Badge tone="default">{formatLabel(caseRow.expectation.verdict)}</Badge>
                    ) : null}
                  </div>
                  <CardTitle className="text-base leading-6">{caseRow.prompt}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  <p>
                    <span className="font-semibold text-foreground">Observed:</span>{" "}
                    {summarizeFailure(caseRow)}
                  </p>
                  {caseRow.classification?.explanation ? (
                    <p>{caseRow.classification.explanation}</p>
                  ) : null}
                  {caseRow.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {caseRow.tags.map((tag) => (
                        <Badge key={`${caseRow.caseId}-${tag}`} tone="muted">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    {selectedCaseId === caseRow.caseId
                      ? "Currently open in the evidence panel"
                      : "Open in the evidence panel"}
                  </p>
                </CardContent>
              </button>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="px-6 py-5 text-sm text-muted-foreground">
            No notable cases were flagged for this run.
          </CardContent>
        </Card>
      )}
    </section>
  );
}
