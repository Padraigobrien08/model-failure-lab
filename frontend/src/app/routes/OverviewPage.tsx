import { OverviewCanvas } from "@/components/overview/OverviewCanvas";
import { StatusStrip } from "@/components/overview/StatusStrip";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatLabel, formatMetric } from "@/lib/formatters";
import { buildOverviewSnapshot } from "@/lib/manifest/selectors";
import { useAppRouteContext } from "@/app/router";

export function OverviewPage() {
  const { index, isLoading, error, includeExploratory } = useAppRouteContext();

  if (isLoading) {
    return (
      <section className="space-y-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-primary">
            Loading manifest
          </p>
          <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
            Preparing the React failure debugger.
          </h2>
        </header>
      </section>
    );
  }

  if (error || index === null) {
    return (
      <section className="space-y-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-destructive">
            Manifest unavailable
          </p>
          <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
            The React shell could not read the artifact index.
          </h2>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground">
            Confirm the bridged manifest exists under the frontend public path, then relaunch the
            app.
          </p>
        </header>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {error ?? "Artifact index missing."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const snapshot = buildOverviewSnapshot(index, includeExploratory);
  const distilbertBaseline = snapshot.seededCohorts.find(
    (cohort) => cohort.cohort_id === "distilbert_baseline",
  );

  return (
    <section className="space-y-8">
      <header className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Overview</Badge>
          {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
        </div>
        <div className="space-y-3">
          <h2 className="text-[2.75rem] font-semibold tracking-[-0.06em] text-foreground">
            Final evidence, turned into an explorable debugging surface.
          </h2>
          <p className="max-w-3xl text-base leading-7 text-muted-foreground">
            The official evidence package still points to the same closeout: calibration is solved
            more cleanly than robustness, the best robustness lane remains mixed, and dataset
            expansion stays deferred under explicit reopen conditions.
          </p>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            This is the primary UI. Streamlit remains available as a fallback.
          </p>
        </div>
      </header>

      <StatusStrip snapshot={snapshot} />
      <OverviewCanvas snapshot={snapshot} />

      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="bg-background/55">
          <CardHeader>
            <CardDescription>Primary baseline checkpoint</CardDescription>
            <CardTitle>
              {distilbertBaseline?.display_name ?? "DistilBERT Baseline"}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                ID Macro F1
              </p>
              <p className="mt-2 text-2xl font-semibold text-foreground">
                {formatMetric(distilbertBaseline?.aggregate_metrics?.mean?.id_macro_f1)}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Worst-group F1
              </p>
              <p className="mt-2 text-2xl font-semibold text-foreground">
                {formatMetric(distilbertBaseline?.aggregate_metrics?.mean?.worst_group_f1)}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Lane count
              </p>
              <p className="mt-2 text-2xl font-semibold text-foreground">
                {snapshot.seededCohorts.length}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-background/55">
          <CardHeader>
            <CardDescription>Evidence scope</CardDescription>
            <CardTitle>{formatLabel(snapshot.datasetExpansionRecommendation)}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
            <p>{snapshot.recommendationReason}</p>
            {snapshot.nextStep ? <p className="text-foreground">{snapshot.nextStep}</p> : null}
          </CardContent>
        </Card>
      </section>
    </section>
  );
}
