import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { RankedComparisonCanvas } from "@/components/comparisons/RankedComparisonCanvas";
import {
  buildComparisonCards,
  buildFailureDomainModels,
  getRepresentativeRunIdForMethod,
} from "@/lib/manifest/selectors";
import { useAppRouteContext } from "@/app/router";

export function ComparisonsPage() {
  const {
    index,
    isLoading,
    error,
    includeExploratory,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selectedMethod,
    selectedDomain,
    setSelectedMethod,
    setSelectedDomain,
    openEvidenceDrawer,
  } = useAppRouteContext();

  if (isLoading || isFinalRobustnessBundleLoading) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Comparisons</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading ranked comparison canvas.
        </h2>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Comparisons</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The comparison package is unavailable.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Missing saved comparison payload."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const comparisonCards = buildComparisonCards(index, finalRobustnessBundle, includeExploratory);
  const failureDomains = buildFailureDomainModels(index, finalRobustnessBundle, includeExploratory);

  function handleInspectMethod(methodName: string) {
    setSelectedMethod(methodName);

    const runId = getRepresentativeRunIdForMethod(index!, methodName, true);
    if (runId) {
      openEvidenceDrawer(runId);
    }
  }

  return (
    <section className="space-y-8">
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Comparisons</Badge>
            {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
            {selectedMethod ? <Badge tone="default">Focused lane: {selectedMethod}</Badge> : null}
          </>
        }
        title="Compare official lanes, then trace the domain that explains the ranking."
        description="Start with the ordered method story, then move into the exact failure domain that explains the ranking. The comparison route stays official-first and keeps the saved report package as the reference frame."
        supportingText={finalRobustnessBundle.summary.key_takeaway}
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active lane
              </p>
              <p className="mt-1 text-foreground">
                {selectedMethod ? selectedMethod : "No focused lane"}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active domain
              </p>
              <p className="mt-1 text-foreground">
                {selectedDomain ? selectedDomain : "No domain focus"}
              </p>
            </div>
          </div>
        }
      />

      <RankedComparisonCanvas
        items={comparisonCards}
        domains={failureDomains}
        selectedMethod={selectedMethod}
        selectedDomain={selectedDomain}
        onSelectMethod={setSelectedMethod}
        onSelectDomain={setSelectedDomain}
        onInspectMethod={handleInspectMethod}
      />
    </section>
  );
}
