import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { FailureExplorerTabs } from "@/components/failure/FailureExplorerTabs";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { useAppRouteContext } from "@/app/router";
import { buildFailureDomainModels, getRepresentativeRunIdForMethod } from "@/lib/manifest/selectors";

export function FailureExplorerPage() {
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
        <Badge tone="accent">Failure Explorer</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading failure-domain evidence.
        </h2>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Failure Explorer</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The failure explorer could not load its saved evidence.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Missing saved failure payload."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const domains = buildFailureDomainModels(index, finalRobustnessBundle, includeExploratory);
  const activeDomain = selectedDomain ?? "worst_group";

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
            <Badge tone="accent">Failure Explorer</Badge>
            {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
            {selectedMethod ? <Badge tone="default">Focused lane: {selectedMethod}</Badge> : null}
          </>
        }
        title="Separate subgroup floor, OOD, ID, and calibration without losing lane focus."
        description="Failure Explorer stays bound to the saved four-domain comparison package. Move across domains without recomputing the story in the browser, and keep the current lane focus visible as the evidence changes."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active domain
              </p>
              <p className="mt-1 text-foreground">{activeDomain}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active lane
              </p>
              <p className="mt-1 text-foreground">
                {selectedMethod ? selectedMethod : "No focused lane"}
              </p>
            </div>
          </div>
        }
      />

      <FailureExplorerTabs
        domains={domains}
        selectedDomain={activeDomain}
        selectedMethod={selectedMethod}
        onSelectDomain={setSelectedDomain}
        onSelectMethod={setSelectedMethod}
        onInspectMethod={handleInspectMethod}
      />
    </section>
  );
}
