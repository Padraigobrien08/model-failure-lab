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

export function RunsPage() {
  const { artifactState, artifactOverview } = useAppRouteContext();

  if (artifactState.status !== "ready" || artifactOverview === null) {
    return <ArtifactStatePanel area="Runs" state={artifactState} />;
  }

  const readyOverview = artifactOverview;

  if (readyOverview.runs.count === 0) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Runs</Badge>
        <Card>
          <CardHeader>
            <CardTitle>No saved runs are available yet.</CardTitle>
            <CardDescription>
              The shell is reading the right artifact root, but there are no
              `runs/&lt;run_id&gt;` directories to index yet.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p className="font-mono text-foreground">{readyOverview.source.runsPath}</p>
            <p>
              Generate a run with `failure-lab demo` or `failure-lab run`. Phase 58
              will replace this placeholder with the full sortable inventory.
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
          <Badge tone="accent">Runs</Badge>
          <Badge tone="muted">{readyOverview.runs.count} detected</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Saved runs are now the home route.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          Phase 57 cuts the mounted app over to the real engine artifact root.
          The detailed sortable inventory lands in Phase 58, but this shell is
          already reading saved run directories instead of the old manifest copy.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active run source</CardTitle>
          <CardDescription>
            The shell is indexing deterministic `run.json` and `results.json`
            artifacts from the local engine root.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="font-mono text-sm text-foreground">{readyOverview.source.runsPath}</p>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Detected run ids
            </p>
            <ul className="space-y-2">
              {readyOverview.runs.ids.slice(0, 6).map((runId) => (
                <li key={runId} className="font-mono text-sm text-foreground">
                  {runId}
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
