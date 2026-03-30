import { useAppRouteContext } from "@/app/router";
import { ArtifactStatePanel } from "@/components/layout/ArtifactStatePanel";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function ComparisonsPage() {
  const { artifactState, artifactOverview } = useAppRouteContext();

  if (artifactState.status !== "ready" || artifactOverview === null) {
    return <ArtifactStatePanel area="Comparisons" state={artifactState} />;
  }

  const readyOverview = artifactOverview;

  if (readyOverview.comparisons.count === 0) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Comparisons</Badge>
        <Card>
          <CardHeader>
            <CardTitle>No comparison reports are available yet.</CardTitle>
            <CardDescription>
              The shell has a valid artifact source, but there are no saved
              `report.json` + `report_details.json` pairs to open yet.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p className="font-mono text-foreground">{readyOverview.source.reportsPath}</p>
            <p>
              Generate a comparison with `failure-lab compare`. Phase 60 will turn
              this route into the real baseline-to-candidate explorer.
            </p>
          </CardContent>
        </Card>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Comparisons</Badge>
          <Badge tone="muted">{readyOverview.comparisons.count} detected</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Saved comparisons stay secondary to runs.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          The new shell now opens on runs and exposes baseline-to-candidate reports
          as the only other top-level destination. This route stays narrow until
          the dedicated comparison explorer lands in Phase 60.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active comparison source</CardTitle>
          <CardDescription>
            Comparison artifacts are read from the same local engine root as the
            runs inventory, with no fallback to legacy manifest summaries.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="font-mono text-sm text-foreground">
            {readyOverview.source.reportsPath}
          </p>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Detected comparison ids
            </p>
            <ul className="space-y-2">
              {readyOverview.comparisons.ids.slice(0, 6).map((reportId) => (
                <li key={reportId} className="font-mono text-sm text-foreground">
                  {reportId}
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
