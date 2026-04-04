import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ArtifactShellState } from "@/lib/artifacts/types";

type ArtifactStatePanelProps = {
  area: "Runs" | "Comparisons" | "Analysis";
  state: ArtifactShellState;
};

const EMPTY_GUIDANCE = [
  "Run `failure-lab demo` for a bundled end-to-end sample.",
  "Or generate fresh artifacts with `failure-lab run` and `failure-lab compare`.",
];

export function ArtifactStatePanel({ area, state }: ArtifactStatePanelProps) {
  if (state.status === "loading") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">{area}</Badge>
        <Card>
          <CardHeader>
            <CardTitle>Loading saved engine artifacts.</CardTitle>
            <CardDescription>
              The debugger is scanning the active artifact root before it mounts
              the runs-first shell.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  if (state.status === "empty") {
    return (
      <section className="space-y-4">
        <Badge tone="accent">{area}</Badge>
        <Card>
          <CardHeader>
            <CardTitle>No saved engine artifacts were found.</CardTitle>
            <CardDescription>
              This UI now reads the real `failure-lab` run and comparison
              directories. There is nothing usable in the active root yet.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p className="font-mono text-foreground">{state.overview.source.path}</p>
            <ul className="space-y-2 pl-5">
              {EMPTY_GUIDANCE.map((item) => (
                <li key={item} className="list-disc">
                  {item}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (state.status === "incompatible") {
    return (
      <section className="space-y-4">
        <Badge tone="default">{area}</Badge>
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle>The saved artifacts do not match the supported shell contract.</CardTitle>
            <CardDescription>
              Phase 57 only supports engine-native `runs/` and `reports/`
              artifacts. The shell will not fall back to legacy manifest data.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            {state.overview.message ? (
              <p>{state.overview.message}</p>
            ) : null}
            {state.overview.issues.length > 0 ? (
              <ul className="space-y-2 pl-5">
                {state.overview.issues.map((issue) => (
                  <li key={issue} className="list-disc">
                    {issue}
                  </li>
                ))}
              </ul>
            ) : null}
            <p className="font-mono text-foreground">{state.overview.source.path}</p>
          </CardContent>
        </Card>
      </section>
    );
  }

  return null;
}
