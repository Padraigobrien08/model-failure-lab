import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EvidenceEntitySection } from "@/components/evidence/EvidenceEntitySection";
import { ArtifactPreviewPanel } from "@/components/evidence/ArtifactPreviewPanel";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import { useAppRouteContext } from "@/app/router";
import { buildEvidenceSections, buildInspectorModel } from "@/lib/manifest/selectors";

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
    selection,
    selectedArtifact,
    setSelectedArtifact,
    setSelectedRunId,
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
  const inspectorModel = buildInspectorModel(
    index,
    finalRobustnessBundle,
    selection,
    includeExploratory,
  );

  function handleInspectItem(
    id: string,
    entityType: "report" | "evaluation" | "run",
    relatedRunId?: string | null,
  ) {
    setSelectedArtifact(id);
    setSelectedRunId(entityType === "run" ? relatedRunId ?? null : relatedRunId ?? null);
  }

  return (
    <section className="space-y-8">
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Evidence</Badge>
            {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
          </>
        }
        title="Artifact browser with live provenance handoff."
        description="Reports, eval bundles, and run artifacts stay grouped by entity type. Every card can hand focus into the live inspector without breaking the current route context."
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
                Focused artifact
              </p>
              <p className="mt-1 break-all text-foreground">
                {selectedArtifact ?? "No artifact selected"}
              </p>
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
        description="Choose an entity family first, then pivot the shared inspector into the exact report, eval bundle, or run that backs a claim."
      >
        <div className="space-y-8">
          {sections.map((section) => (
            <EvidenceEntitySection
              key={section.key}
              section={section}
              selectedItemId={selectedArtifact}
              onInspectItem={handleInspectItem}
            />
          ))}
        </div>
      </WorkbenchSection>

      {selectedArtifact && inspectorModel.kind === "artifact" ? (
        <WorkbenchSection
          eyebrow="Selected artifact"
          title="Preview the currently focused manifest entity"
          description="The center canvas mirrors the current artifact selection while the right inspector keeps the full provenance stack visible."
        >
          <ArtifactPreviewPanel preview={inspectorModel.preview} />
        </WorkbenchSection>
      ) : null}
    </section>
  );
}
