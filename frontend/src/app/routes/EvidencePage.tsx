import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EvidenceEntitySection } from "@/components/evidence/EvidenceEntitySection";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
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
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Evidence</Badge>
            {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
          </>
        }
        title="Official-first artifact browser."
        description="Reports, evaluations, and runs stay grouped by evidence type so you can jump directly to the saved artifact that backs a claim without losing scope boundaries."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active scope
              </p>
              <p className="mt-1 text-foreground">
                {includeExploratory ? "Official + exploratory" : "Official only"}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Entity groups
              </p>
              <p className="mt-1 text-foreground">{sections.length} sections</p>
            </div>
          </div>
        }
      />

      <ScopeStateBanner
        includeExploratory={includeExploratory}
        onChange={setIncludeExploratory}
      />

      <WorkbenchSection
        eyebrow="Artifact groups"
        title="Manifest-backed entity groups"
        description="Each section keeps the claim-backed artifact families together so you can trace from summary surfaces into report, eval, and run files without losing scope context."
      >
        <div className="space-y-8">
          {sections.map((section) => (
            <EvidenceEntitySection key={section.key} section={section} />
          ))}
        </div>
      </WorkbenchSection>
    </section>
  );
}
