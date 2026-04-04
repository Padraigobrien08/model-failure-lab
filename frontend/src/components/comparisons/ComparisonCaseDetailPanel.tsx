import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ComparisonCaseDeltaRecord } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonCaseDrillthroughAction = {
  label: string;
  ariaLabel: string;
  href: string | null;
  runId: string;
  state?: unknown;
  disabledReason?: string | null;
};

type ComparisonCaseExportAction = {
  label: string;
  status: "idle" | "loading" | "ready" | "error";
  onExport: () => void;
  message?: string | null;
  disabled?: boolean;
};

type ComparisonCaseDetailPanelProps = {
  caseDelta: ComparisonCaseDeltaRecord | null;
  baselineAction?: ComparisonCaseDrillthroughAction | null;
  candidateAction?: ComparisonCaseDrillthroughAction | null;
  exportAction?: ComparisonCaseExportAction | null;
  artifactContext?: {
    reportId: string;
    baselineRunId: string;
    candidateRunId: string;
    sourcePath: string;
  } | null;
};

function formatValue(value: string | null): string {
  if (!value) {
    return "None";
  }
  return formatLabel(value);
}

export function ComparisonCaseDetailPanel({
  caseDelta,
  baselineAction = null,
  candidateAction = null,
  exportAction = null,
  artifactContext = null,
}: ComparisonCaseDetailPanelProps) {
  if (!caseDelta) {
    return (
      <Card className="rounded-[24px] border border-border/70 bg-card/70 shadow-panel">
        <CardHeader className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Stage 4 · Selected evidence
          </p>
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
    <Card
      data-active-case="true"
      className="rounded-[24px] border border-primary/15 bg-primary/[0.04] shadow-panel"
    >
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">Stage 4</Badge>
          <Badge tone="default">Selected transition evidence</Badge>
          <Badge tone="accent">Active case</Badge>
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
          <p className="text-sm leading-6 text-muted-foreground">
            Compare the saved baseline and candidate explanations, verdicts, and failure labels in
            one place before you move to the next transition.
          </p>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {baselineAction || candidateAction ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Open matching evidence
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              {[baselineAction, candidateAction]
                .filter((action): action is ComparisonCaseDrillthroughAction => action !== null)
                .map((action) =>
                  action.href ? (
                    <Link
                      key={action.label}
                      aria-label={action.ariaLabel}
                      className="rounded-[18px] border border-border/70 bg-background/70 p-4 text-inherit no-underline transition-colors hover:bg-background"
                      state={action.state}
                      to={action.href}
                    >
                      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                        {action.label}
                      </p>
                      <p className="mt-2 break-all text-sm font-semibold text-foreground">
                        {action.runId}
                      </p>
                    </Link>
                  ) : (
                    <div
                      key={action.label}
                      aria-disabled="true"
                      className="rounded-[18px] border border-border/60 bg-background/55 p-4 text-muted-foreground"
                    >
                      <p className="text-xs font-semibold uppercase tracking-[0.16em]">
                        {action.label}
                      </p>
                      <p className="mt-2 break-all text-sm font-semibold text-foreground/75">
                        {action.runId}
                      </p>
                      {action.disabledReason ? (
                        <p className="mt-2 text-sm leading-6">{action.disabledReason}</p>
                      ) : null}
                    </div>
                  ),
                )}
            </div>
          </section>
        ) : null}

        {exportAction ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Export transition slice
            </p>
            <button
              type="button"
              className="rounded-[18px] border border-primary/30 bg-primary/12 px-4 py-3 text-sm font-semibold text-primary transition-colors hover:bg-primary/18 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={exportAction.disabled || exportAction.status === "loading"}
              onClick={exportAction.onExport}
            >
              {exportAction.status === "loading" ? "Exporting draft..." : exportAction.label}
            </button>
            {exportAction.message ? (
              <p className="text-sm leading-6 text-muted-foreground">{exportAction.message}</p>
            ) : null}
          </section>
        ) : null}

        {artifactContext ? (
          <section aria-label="Artifact context" className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Artifact context
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Report ID
                </p>
                <p className="mt-2 break-all font-mono text-xs text-foreground">
                  {artifactContext.reportId}
                </p>
              </div>
              <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Case ID
                </p>
                <p className="mt-2 break-all font-mono text-xs text-foreground">
                  {caseDelta.caseId}
                </p>
              </div>
              <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Prompt ID
                </p>
                <p className="mt-2 break-all font-mono text-xs text-foreground">
                  {caseDelta.promptId}
                </p>
              </div>
              <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Baseline / Candidate
                </p>
                <p className="mt-2 break-all font-mono text-xs text-foreground">
                  {artifactContext.baselineRunId} / {artifactContext.candidateRunId}
                </p>
              </div>
            </div>
            <div className="rounded-[18px] border border-border/70 bg-background/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Source root
              </p>
              <p className="mt-2 break-all font-mono text-xs text-foreground">
                {artifactContext.sourcePath}
              </p>
            </div>
          </section>
        ) : null}

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
