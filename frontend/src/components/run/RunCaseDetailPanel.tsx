import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RunCaseRecord } from "@/lib/artifacts/types";
import { formatCount, formatLabel, formatMetric } from "@/lib/formatters";

type RunCaseDetailPanelProps = {
  caseRow: RunCaseRecord | null;
};

function formatFailureLabel(
  failure:
    | {
        failureType: string;
        failureSubtype: string | null;
      }
    | null
    | undefined,
) {
  if (!failure) {
    return "None";
  }

  if (failure.failureSubtype) {
    return `${formatLabel(failure.failureType)} / ${formatLabel(failure.failureSubtype)}`;
  }

  return formatLabel(failure.failureType);
}

export function RunCaseDetailPanel({ caseRow }: RunCaseDetailPanelProps) {
  if (!caseRow) {
    return (
      <Card className="rounded-[24px] border border-border/70 bg-card/70 shadow-panel">
        <CardHeader>
          <CardTitle>Select a case</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Pick a case from the table to inspect its prompt, output, and saved classification
          detail without leaving this run.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="rounded-[24px] border border-border/70 bg-card/70 shadow-panel">
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Selected case</Badge>
          <Badge tone="muted">{caseRow.caseId}</Badge>
          {caseRow.tags.map((tag) => (
            <Badge key={`${caseRow.caseId}-${tag}`} tone="muted">
              {tag}
            </Badge>
          ))}
        </div>
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Prompt
          </p>
          <CardTitle className="text-xl leading-8">{caseRow.prompt}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Expectation
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Expected
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatFailureLabel(caseRow.expectation.expectedFailure)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Observed
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatFailureLabel(caseRow.expectation.observedFailure)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Verdict
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatLabel(caseRow.expectation.verdict ?? "unknown")}
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Output
          </p>
          <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
            <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">
              {caseRow.outputText ?? "No output was captured for this case."}
            </p>
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Classification
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Failure label
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatFailureLabel(caseRow.classification?.failure)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Confidence
              </p>
              <p className="mt-2 text-sm text-foreground">
                {caseRow.classification?.confidence === null ||
                caseRow.classification?.confidence === undefined
                  ? "n/a"
                  : formatMetric(caseRow.classification.confidence)}
              </p>
            </div>
          </div>
          <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Explanation
            </p>
            <p className="mt-2 text-sm leading-6 text-foreground">
              {caseRow.classification?.explanation ?? "No classifier explanation was saved."}
            </p>
          </div>
        </section>

        {caseRow.error ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Execution issue
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-destructive/20 bg-destructive/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Stage
                </p>
                <p className="mt-2 text-sm text-foreground">
                  {formatLabel(caseRow.error.stage)}
                </p>
              </div>
              <div className="rounded-[18px] border border-destructive/20 bg-destructive/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Error type
                </p>
                <p className="mt-2 text-sm text-foreground">{caseRow.error.type}</p>
              </div>
            </div>
            <div className="rounded-[18px] border border-destructive/20 bg-destructive/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Message
              </p>
              <p className="mt-2 text-sm leading-6 text-foreground">{caseRow.error.message}</p>
            </div>
          </section>
        ) : null}

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Saved identifiers
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge tone="muted">Prompt ID {caseRow.promptId}</Badge>
            <Badge tone="muted">Tags {formatCount(caseRow.tags.length)}</Badge>
          </div>
        </section>
      </CardContent>
    </Card>
  );
}
