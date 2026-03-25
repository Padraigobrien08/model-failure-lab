import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EvidenceEntitySection } from "@/components/evidence/EvidenceEntitySection";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { useAppRouteContext } from "@/app/router";
import { buildEvidenceSections } from "@/lib/manifest/selectors";

export function EvidencePage() {
  const {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
  } = useAppRouteContext();

  if (isLoading || isFinalRobustnessBundleLoading) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Evidence</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading evidence controls.
        </h2>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Evidence</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The evidence browser could not load its saved artifact references.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Missing saved evidence artifacts."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const sections = buildEvidenceSections(index, finalRobustnessBundle, includeExploratory);

  return (
    <section className="space-y-8">
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Evidence</Badge>
          {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
        </div>
        <div className="space-y-3">
          <h2 className="text-[2.75rem] font-semibold tracking-[-0.06em] text-foreground">
            Official-first artifact browser.
          </h2>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            Reports, evaluations, and runs stay grouped by evidence type so you can jump directly
            to the saved artifact that backs a claim without losing scope boundaries.
          </p>
        </div>
      </header>

      <ScopeStateBanner
        includeExploratory={includeExploratory}
        onChange={setIncludeExploratory}
      />

      <div className="space-y-8">
        {sections.map((section) => (
          <EvidenceEntitySection key={section.key} section={section} />
        ))}
      </div>
    </section>
  );
}
