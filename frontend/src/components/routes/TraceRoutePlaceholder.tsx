import { Link, useParams } from "react-router-dom";

import { useTraceScope } from "@/app/scope";

type TraceStepLink = {
  label: string;
  path: string;
};

type TraceRoutePlaceholderProps = {
  routeLabel: string;
  routePattern: string;
  question: string;
  previousStep: TraceStepLink;
  nextStep: TraceStepLink;
};

function buildScopedPath(path: string, scope: "official" | "all") {
  return `${path}?scope=${scope}`;
}

export function TraceRoutePlaceholder({
  routeLabel,
  routePattern,
  question,
  previousStep,
  nextStep,
}: TraceRoutePlaceholderProps) {
  const params = useParams();
  const { scope } = useTraceScope();
  const routeParams = Object.entries(params).filter(([, value]) => value !== undefined);
  const scopeLabel = scope === "all" ? "All" : "Official";

  return (
    <article className="space-y-4">
      <section className="rounded-[20px] border border-border/70 bg-card/60 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Route label
        </p>
        <p className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-foreground">{routeLabel}</p>
        <p className="mt-3 font-mono text-sm text-muted-foreground">{routePattern}</p>
        <p className="mt-3 text-sm text-foreground">
          <span className="font-medium">Current scope</span>: {scopeLabel}
        </p>
      </section>

      <section className="rounded-[20px] border border-border/70 bg-background/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Current question
        </p>
        <h1 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-foreground">{question}</h1>
      </section>

      <section className="rounded-[20px] border border-border/70 bg-background/70 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Current params
        </p>
        {routeParams.length > 0 ? (
          <dl className="mt-3 space-y-2">
            {routeParams.map(([key, value]) => (
              <div key={key} className="flex items-center justify-between gap-3 text-sm">
                <dt className="font-medium text-foreground">{key}</dt>
                <dd className="font-mono text-muted-foreground">{value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">No dynamic params for this route.</p>
        )}
      </section>

      <nav
        aria-label={`${routeLabel} scaffold navigation`}
        className="grid gap-3 rounded-[20px] border border-border/70 bg-background/70 p-4 sm:grid-cols-2"
      >
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Previous step
          </p>
          <Link
            className="text-sm font-medium text-foreground underline underline-offset-4"
            to={buildScopedPath(previousStep.path, scope)}
          >
            {previousStep.label}
          </Link>
        </div>
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Next step
          </p>
          <Link
            className="text-sm font-medium text-foreground underline underline-offset-4"
            to={buildScopedPath(nextStep.path, scope)}
          >
            {nextStep.label}
          </Link>
        </div>
      </nav>
    </article>
  );
}
