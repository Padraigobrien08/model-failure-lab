import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ComparisonCaseDeltaRecord } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonCaseDetailPanelProps = {
  caseDelta: ComparisonCaseDeltaRecord | null;
};

function formatValue(value: string | null): string {
  if (!value) {
    return "None";
  }
  return formatLabel(value);
}

export function ComparisonCaseDetailPanel({
  caseDelta,
}: ComparisonCaseDetailPanelProps) {
  if (!caseDelta) {
    return (
      <Card className="rounded-[24px] border border-border/70 bg-card/70 shadow-panel">
        <CardHeader>
          <CardTitle>Select a changed case</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Pick one case from a grouped transition section to inspect the directional difference
          between baseline and candidate.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="rounded-[24px] border border-border/70 bg-card/70 shadow-panel">
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Selected transition</Badge>
          <Badge tone="muted">{caseDelta.caseId}</Badge>
          {caseDelta.tags.map((tag) => (
            <Badge key={`${caseDelta.caseId}-${tag}`} tone="muted">
              {tag}
            </Badge>
          ))}
        </div>
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Prompt
          </p>
          <CardTitle className="text-xl leading-8">{caseDelta.prompt}</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Transition
          </p>
          <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
            <p className="text-sm text-foreground">{caseDelta.transitionLabel}</p>
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Failure context
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Baseline failure
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatValue(caseDelta.baselineFailureType)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Candidate failure
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatValue(caseDelta.candidateFailureType)}
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Expectation verdicts
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Baseline verdict
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatValue(caseDelta.baselineExpectationVerdict)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Candidate verdict
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatValue(caseDelta.candidateExpectationVerdict)}
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Explanations
          </p>
          <div className="grid gap-3">
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Baseline explanation
              </p>
              <p className="mt-2 text-sm leading-6 text-foreground">
                {caseDelta.baselineExplanation ?? "No baseline explanation was saved."}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Candidate explanation
              </p>
              <p className="mt-2 text-sm leading-6 text-foreground">
                {caseDelta.candidateExplanation ?? "No candidate explanation was saved."}
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Error stages
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Baseline error stage
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatValue(caseDelta.baselineErrorStage)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Candidate error stage
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatValue(caseDelta.candidateErrorStage)}
              </p>
            </div>
          </div>
        </section>
      </CardContent>
    </Card>
  );
}
