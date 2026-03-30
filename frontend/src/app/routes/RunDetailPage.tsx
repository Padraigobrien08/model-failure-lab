import { Link, useParams } from "react-router-dom";

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

export function RunDetailPage() {
  const { runId } = useParams();
  const { artifactState, runInventoryState } = useAppRouteContext();

  if (artifactState.status !== "ready") {
    return <ArtifactStatePanel area="Runs" state={artifactState} />;
  }

  if (runInventoryState.status === "idle" || runInventoryState.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Run detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading selected run.</CardTitle>
            <CardDescription>
              The inventory route is establishing the dedicated detail handoff.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (runInventoryState.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">Run detail</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The selected run could not be resolved.</CardTitle>
            <CardDescription>
              The runs inventory is not available under the supported artifact contract.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {runInventoryState.message}
          </CardContent>
        </Card>
      </section>
    );
  }

  const inventory = runInventoryState.inventory;
  if (inventory === null) {
    return null;
  }

  const run = inventory.runs.find((item) => item.runId === runId);
  if (!run) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Run detail</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Run not found.</CardTitle>
            <CardDescription>
              This route is reserved for the dedicated run detail surface. The requested
              run id is not present in the active inventory.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link className="text-sm font-semibold text-primary no-underline" to="/">
              Back to runs
            </Link>
          </CardContent>
        </Card>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <nav
        aria-label="Run breadcrumb"
        className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
      >
        <Link className="font-semibold text-foreground no-underline" to="/">
          Runs
        </Link>
        <span aria-hidden="true">/</span>
        <span className="font-mono text-xs text-foreground">{run.runId}</span>
      </nav>

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="accent">Run detail</Badge>
          <Badge tone="muted">{run.status}</Badge>
        </div>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          {run.runId}
        </h1>
        <p className="max-w-3xl text-base leading-7 text-muted-foreground">
          Phase 58 establishes the dedicated run route handoff. Phase 59 will replace this
          placeholder with the full report-backed detail and case drilldown surface.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Selected run summary</CardTitle>
          <CardDescription>
            Minimal route contract only. Full summaries and drilldown land in the next phase.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Dataset
            </p>
            <p className="mt-2 text-sm text-foreground">{run.dataset}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Model
            </p>
            <p className="mt-2 text-sm text-foreground">{run.model}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Saved at
            </p>
            <p className="mt-2 text-sm text-foreground">{run.createdAt}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Status
            </p>
            <p className="mt-2 text-sm text-foreground">{run.status}</p>
          </div>
        </CardContent>
      </Card>

      <Link className="text-sm font-semibold text-primary no-underline" to="/">
        Back to runs
      </Link>
    </section>
  );
}
