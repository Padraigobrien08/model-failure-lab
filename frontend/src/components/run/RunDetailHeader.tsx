import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type RunDetailHeaderProps = {
  runId: string;
  dataset: string;
  model: string;
  status: string;
  createdAt: string;
  inventoryHref: string;
  reportId: string;
  adapterId: string | null;
  classifierId: string | null;
  runSeed: number | null;
};

function formatTimestamp(createdAt: string): string {
  const value = new Date(createdAt);
  if (Number.isNaN(value.getTime())) {
    return createdAt;
  }

  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(value);
}

function statusTone(status: string): "accent" | "default" | "muted" {
  if (status === "completed") {
    return "accent";
  }
  if (status === "completed_with_errors") {
    return "default";
  }
  return "muted";
}

function formatOptionalValue(value: string | number | null): string {
  if (value === null || value === "") {
    return "n/a";
  }

  return String(value);
}

export function RunDetailHeader({
  runId,
  dataset,
  model,
  status,
  createdAt,
  inventoryHref,
  reportId,
  adapterId,
  classifierId,
  runSeed,
}: RunDetailHeaderProps) {
  return (
    <header className="space-y-5 border-b border-border/60 pb-6">
      <nav
        aria-label="Run breadcrumb"
        className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
      >
        <Link className="font-semibold text-foreground no-underline" to={inventoryHref}>
          Runs
        </Link>
        <span aria-hidden="true">/</span>
        <span className="font-mono text-xs text-foreground">{runId}</span>
      </nav>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Badge tone="accent">Run detail</Badge>
            <Badge tone="muted">{dataset}</Badge>
            <Badge tone="muted">{model}</Badge>
            <Badge tone={statusTone(status)}>{status}</Badge>
          </div>
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Stage 1 · Run identity
            </p>
            <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground sm:text-4xl">
              {runId}
            </h1>
            <p className="max-w-3xl text-base leading-7 text-muted-foreground">
              Lock the run identity first, then move through the saved debugger path:
              overall failure shape, why it failed, notable cases, and selected evidence.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              "Run identity",
              "Overall failure shape",
              "Why it failed",
              "Notable cases",
              "Selected evidence",
            ].map((step, index) => (
              <span
                key={step}
                className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground"
              >
                <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/12 text-[10px] text-primary">
                  {index + 1}
                </span>
                {step}
              </span>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            Saved at{" "}
            <span className="font-medium text-foreground">{formatTimestamp(createdAt)}</span>
          </p>
        </div>

        <Card className="rounded-[24px] border border-border/70 bg-card/75">
          <CardHeader className="space-y-1 pb-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Saved lineage
            </p>
            <CardTitle className="text-lg">Keep the run context visible</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Report id
              </p>
              <p className="mt-2 break-all font-mono text-sm text-foreground">{reportId}</p>
            </div>
            <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Adapter
              </p>
              <p className="mt-2 text-sm text-foreground">{formatOptionalValue(adapterId)}</p>
            </div>
            <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Classifier
              </p>
              <p className="mt-2 text-sm text-foreground">
                {formatOptionalValue(classifierId)}
              </p>
            </div>
            <div className="rounded-[18px] border border-border/60 bg-background/70 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Seed
              </p>
              <p className="mt-2 text-sm text-foreground">{formatOptionalValue(runSeed)}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </header>
  );
}
