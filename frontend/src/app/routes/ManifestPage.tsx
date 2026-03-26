import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import { useAppRouteContext } from "@/app/router";

export function ManifestPage() {
  const { index, isLoading, error, includeExploratory, manifestPath } = useAppRouteContext();

  if (isLoading) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Manifest</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading manifest provenance.
        </h2>
      </section>
    );
  }

  if (error || index === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Manifest</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The provenance console could not load the current artifact contract.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {error ?? "Manifest missing."}
          </CardContent>
        </Card>
      </section>
    );
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
        title="Contract provenance and visibility state."
        description="Read the manifest as the contract of record for verdict, lane, run, and artifact visibility. This route stays human-readable first and becomes the deeper relationship ledger in the next execution wave."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Schema version
              </p>
              <p className="mt-1 text-foreground">{index.schema_version}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Generated at
              </p>
              <p className="mt-1 text-foreground">{index.generated_at ?? "Unknown"}</p>
            </div>
          </div>
        }
      />

      <WorkbenchSection
        eyebrow="Contract origin"
        title="Manifest source"
        description="The React workbench stays bound to this bridged contract path and its visibility rules."
      >
        <div className="rounded-[18px] border border-border/70 bg-card/45 px-4 py-4 font-mono text-sm text-foreground">
          {manifestPath}
        </div>
      </WorkbenchSection>

      <WorkbenchSection
        eyebrow="Entity inventory"
        title="Current contract counts"
        description="Official/default-visible counts still come from the artifact index itself. No client-side lineage is inferred outside that contract."
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[18px] border border-border/70 bg-card/45 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Runs
            </p>
            <p className="mt-2 text-3xl font-semibold text-foreground">
              {index.entities.runs.length}
            </p>
          </div>
          <div className="rounded-[18px] border border-border/70 bg-card/45 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Evaluations
            </p>
            <p className="mt-2 text-3xl font-semibold text-foreground">
              {index.entities.evaluations.length}
            </p>
          </div>
          <div className="rounded-[18px] border border-border/70 bg-card/45 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Reports
            </p>
            <p className="mt-2 text-3xl font-semibold text-foreground">
              {index.entities.reports.length}
            </p>
          </div>
        </div>
      </WorkbenchSection>
    </section>
  );
}
