import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import { ManifestRelationshipLedger } from "@/components/manifest/ManifestRelationshipLedger";
import { useAppRouteContext } from "@/app/router";
import { buildManifestRelationshipLedgerModel } from "@/lib/manifest/selectors";

export function ManifestPage() {
  const {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory,
    manifestPath,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selection,
    setSelectedArtifact,
    setSelectedRunId,
  } = useAppRouteContext();

  if (isLoading || isFinalRobustnessBundleLoading) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Manifest</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading manifest provenance.
        </h2>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Manifest</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The provenance console could not load the current artifact contract.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Manifest missing."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const manifestIndex = index;
  const ledger = buildManifestRelationshipLedgerModel(
    manifestIndex,
    finalRobustnessBundle,
    selection,
    includeExploratory,
  );

  function handleSelectEntity(id: string, entityType: "report" | "evaluation" | "run") {
    setSelectedArtifact(id);
    if (entityType === "run") {
      const runEntity = manifestIndex.entities.runs.find((candidate) => candidate.id === id) as
        | { run_id?: string }
        | undefined;
      setSelectedRunId(runEntity?.run_id ?? null);
      return;
    }

    if (entityType === "evaluation") {
      const evaluationEntity = manifestIndex.entities.evaluations.find((candidate) => candidate.id === id);
      const sourceRunId =
        evaluationEntity && "source_run_id" in evaluationEntity
          ? (evaluationEntity as { source_run_id?: string | null }).source_run_id ?? null
          : null;
      setSelectedRunId(sourceRunId);
      return;
    }

    setSelectedRunId(null);
  }

  return (
    <section className="space-y-8">
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Manifest</Badge>
            {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
            <Badge tone="muted">Provenance console</Badge>
          </>
        }
        title="Manifest console for provenance, visibility, and relationships."
        description="Read the contract as the system of record for what is official, what is default-visible, and which run or artifact path supports the active failure story."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Schema version
              </p>
              <p className="mt-1 text-foreground">{manifestIndex.schema_version}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Generated at
              </p>
              <p className="mt-1 text-foreground">{manifestIndex.generated_at ?? "Unknown"}</p>
            </div>
          </div>
        }
      />

      <ScopeStateBanner
        includeExploratory={includeExploratory}
        onChange={setIncludeExploratory}
      />

      <WorkbenchSection
        eyebrow="Contract origin"
        title="Manifest source"
        description="The React workbench stays bound to this manifest path and its saved visibility rules."
      >
        <div className="rounded-[18px] border border-border/70 bg-card/45 px-4 py-4 font-mono text-sm text-foreground">
          {manifestPath}
        </div>
      </WorkbenchSection>

      <WorkbenchSection
        eyebrow="Entity ledger"
        title="Selected manifest relationships"
        description="Choose a contract entity, then inspect its visibility flags, upstream relationships, and source paths without dropping current workbench context."
      >
        <ManifestRelationshipLedger
          model={ledger}
          onSelectEntity={handleSelectEntity}
        />
      </WorkbenchSection>
    </section>
  );
}
