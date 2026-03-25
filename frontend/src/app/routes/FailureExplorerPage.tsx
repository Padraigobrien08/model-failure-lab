import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { FailureExplorerTabs } from "@/components/failure/FailureExplorerTabs";
import { useAppRouteContext } from "@/app/router";
import { buildFailureDomainModels } from "@/lib/manifest/selectors";

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

  return (
    <section className="space-y-8">
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Failure Explorer</Badge>
          {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
          {selectedMethod ? <Badge tone="default">Focused lane: {selectedMethod}</Badge> : null}
        </div>
        <div className="space-y-3">
          <h2 className="text-[2.75rem] font-semibold tracking-[-0.06em] text-foreground">
            Failure domains, split into the four saved evidence families.
          </h2>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Move through subgroup floor, OOD, ID, and calibration without changing the contract or
            recomputing the story in the browser. The selected lane stays in view as you move
            between tabs.
          </p>
        </div>
      </header>

      <FailureExplorerTabs
        domains={domains}
        selectedDomain={activeDomain}
        selectedMethod={selectedMethod}
        onSelectDomain={setSelectedDomain}
        onSelectMethod={setSelectedMethod}
      />
    </section>
  );
}
