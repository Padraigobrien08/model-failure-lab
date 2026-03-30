import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ComparisonDetail } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type ComparisonCoverageSummaryProps = {
  comparison: ComparisonDetail["comparison"];
  coverage: ComparisonDetail["coverage"];
};

function renderCaseIds(caseIds: string[]): string {
  if (caseIds.length === 0) {
    return "None";
  }

  const visible = caseIds.slice(0, 4);
  const suffix =
    caseIds.length > visible.length ? ` +${caseIds.length - visible.length} more` : "";
  return `${visible.join(", ")}${suffix}`;
}

export function ComparisonCoverageSummary({
  comparison,
  coverage,
}: ComparisonCoverageSummaryProps) {
  const compatibilityLabel = comparison.compatible
    ? "Compatible comparison"
    : `Incompatible comparison${comparison.reason ? `: ${formatLabel(comparison.reason)}` : ""}`;

  return (
    <section className="space-y-4" aria-label="Comparison coverage">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Coverage
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Compatibility and shared-case scope
        </h2>
      </div>

      <Card className="rounded-[24px] bg-card/75">
        <CardHeader className="space-y-3 pb-4">
          <div className="flex flex-wrap items-center gap-3">
            <Badge tone={comparison.compatible ? "accent" : "default"}>
              {compatibilityLabel}
            </Badge>
            {comparison.metricsComputedOn ? (
              <Badge tone="muted">
                {comparison.metricsComputedOn === "shared_cases_only"
                  ? "Shared-case analysis only"
                  : formatLabel(comparison.metricsComputedOn)}
              </Badge>
            ) : null}
          </div>
          <CardTitle className="text-lg">
            {comparison.compatible
              ? "Metrics and transitions are scoped explicitly."
              : "The comparison is still readable even though the datasets do not align."}
          </CardTitle>
        </CardHeader>

        <CardContent className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-[20px] border border-border/60 bg-background/60 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Shared cases
            </p>
            <p className="mt-3 text-2xl font-semibold text-foreground">
              {coverage.sharedCaseCount}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {renderCaseIds(coverage.sharedCaseIds)}
            </p>
          </div>

          <div className="rounded-[20px] border border-border/60 bg-background/60 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Baseline only
            </p>
            <p className="mt-3 text-2xl font-semibold text-foreground">
              {coverage.baselineOnlyCaseCount}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {renderCaseIds(coverage.baselineOnlyCaseIds)}
            </p>
          </div>

          <div className="rounded-[20px] border border-border/60 bg-background/60 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Candidate only
            </p>
            <p className="mt-3 text-2xl font-semibold text-foreground">
              {coverage.candidateOnlyCaseCount}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {renderCaseIds(coverage.candidateOnlyCaseIds)}
            </p>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
