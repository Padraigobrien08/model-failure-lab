import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { RankedComparisonCanvas } from "@/components/comparisons/RankedComparisonCanvas";
import { buildComparisonCards, buildFailureDomainModels } from "@/lib/manifest/selectors";
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

  return (
    <section className="space-y-8">
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Comparisons</Badge>
          {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
          {selectedMethod ? <Badge tone="default">Focused lane: {selectedMethod}</Badge> : null}
        </div>
        <div className="space-y-3">
          <h2 className="text-[2.75rem] font-semibold tracking-[-0.06em] text-foreground">
            Ranked comparison canvas
          </h2>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Start with the ordered method story, then move into the exact failure domain that
            explains the ranking. The canvas stays official-first and reads straight from the saved
            report payloads.
          </p>
          <p className="max-w-3xl text-sm leading-6 text-foreground">
            {finalRobustnessBundle.summary.key_takeaway}
          </p>
        </div>
      </header>

      <RankedComparisonCanvas
        items={comparisonCards}
        domains={failureDomains}
        selectedMethod={selectedMethod}
        selectedDomain={selectedDomain}
        onSelectMethod={setSelectedMethod}
        onSelectDomain={setSelectedDomain}
      />
    </section>
  );
}
