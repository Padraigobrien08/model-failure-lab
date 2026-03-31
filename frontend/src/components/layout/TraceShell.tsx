import { NavLink, Outlet, useLocation } from "react-router-dom";

import { NAVIGATION_ITEMS, type AppRouteContext } from "@/app/router";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type TraceShellProps = {
  routeContext: AppRouteContext;
};

type RouteMeta = {
  eyebrow: string;
  title: string;
  description: string;
  focusTitle: string;
  focusDescription: string;
  pathway: string[];
};

function resolveRouteMeta(pathname: string): RouteMeta {
  if (pathname.startsWith("/comparisons/")) {
    return {
      eyebrow: "Comparison debugger",
      title: "Orient first, then compare hard.",
      description:
        "Keep baseline and candidate context in view, lock the shared scope, and then work through grouped transition evidence.",
      focusTitle: "Comparison evidence path",
      focusDescription:
        "Directional delta up top, shared-case scope next, then grouped transitions and selected case evidence.",
      pathway: [
        "Saved comparisons",
        "Comparison framing",
        "Coverage scope",
        "Transition evidence",
      ],
    };
  }

  if (pathname.startsWith("/comparisons")) {
    return {
      eyebrow: "Comparison debugger",
      title: "Scan saved reports before opening one.",
      description:
        "Use the comparison inventory to find the right baseline-versus-candidate report, then step into the delta that matters.",
      focusTitle: "Inventory focus",
      focusDescription:
        "Newest reports first, compatibility visible, and one click into saved directional evidence.",
      pathway: [
        "Saved comparisons",
        "Compatibility status",
        "Baseline vs candidate",
        "Open report",
      ],
    };
  }

  if (pathname.startsWith("/runs/")) {
    return {
      eyebrow: "Run debugger",
      title: "Follow the run from identity to evidence.",
      description:
        "Recover the debugger pathway: lock the run identity, read the overall failure shape, isolate why it broke, then inspect the saved case evidence.",
      focusTitle: "Run investigation path",
      focusDescription:
        "Run identity, overall failure shape, why it failed, notable cases, and selected case evidence stay visible as one route.",
      pathway: [
        "Saved runs",
        "Run identity",
        "Failure shape",
        "Why it failed",
        "Selected evidence",
      ],
    };
  }

  return {
    eyebrow: "Run debugger",
    title: "Start from saved runs, not abstract reports.",
    description:
      "The main debugger surface is the run inventory. Find the latest run, narrow it by model or dataset, and move directly into saved evidence.",
    focusTitle: "Inventory focus",
    focusDescription:
      "Newest runs first, active artifact root visible, and direct handoff into a structured run investigation route.",
    pathway: [
      "Saved runs",
      "Filter inventory",
      "Open run",
      "Inspect evidence",
    ],
  };
}

export function TraceShell({ routeContext }: TraceShellProps) {
  const location = useLocation();
  const artifactOverview = routeContext.artifactOverview;
  const sourceLabel = artifactOverview?.source.label ?? "Local artifact root";
  const sourcePath = artifactOverview?.source.path ?? "Scanning repo-root runs/ and reports/…";
  const routeMeta = resolveRouteMeta(location.pathname);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 border-b border-border/60 bg-background/92 backdrop-blur">
        <div className="mx-auto flex w-full max-w-[92rem] flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-3">
              <NavLink
                to="/"
                className="text-lg font-semibold tracking-[-0.04em] text-foreground no-underline"
              >
                Failure Lab
              </NavLink>
              <Badge tone="accent">Engine artifacts</Badge>
              <Badge tone="muted">
                Runs {artifactOverview?.runs.count ?? 0}
              </Badge>
              <Badge tone="muted">
                Comparisons {artifactOverview?.comparisons.count ?? 0}
              </Badge>
            </div>

            <nav
              aria-label="Primary navigation"
              className="flex flex-wrap items-center gap-2"
            >
              {NAVIGATION_ITEMS.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  className={({ isActive }) =>
                    cn(
                      "rounded-full border px-4 py-2 text-sm font-semibold no-underline transition-colors",
                      isActive
                        ? "border-primary/30 bg-primary/12 text-primary"
                        : "border-border/70 bg-card/70 text-muted-foreground hover:text-foreground",
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <section className="border-b border-border/50 bg-[linear-gradient(180deg,rgba(255,255,255,0.84),rgba(255,255,255,0.58))]">
        <div className="mx-auto flex w-full max-w-[92rem] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
          <div className="space-y-2">
            <p className="text-sm leading-6 text-muted-foreground">
              The React debugger now opens on saved run artifacts and comparison reports from the
              real `failure-lab` contract.
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(18rem,0.75fr)]">
            <div className="rounded-[28px] border border-border/60 bg-card/75 px-5 py-5 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
              <div className="space-y-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                  {routeMeta.eyebrow}
                </p>
                <div className="space-y-2">
                  <h2 className="text-2xl font-semibold tracking-[-0.05em] text-foreground sm:text-[2rem]">
                    {routeMeta.title}
                  </h2>
                  <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                    {routeMeta.description}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {routeMeta.pathway.map((step, index) => (
                    <span
                      key={`${routeMeta.title}-${step}`}
                      className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground"
                    >
                      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/12 text-[10px] text-primary">
                        {index + 1}
                      </span>
                      {step}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-[28px] border border-border/60 bg-card/75 px-5 py-5 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
              <div className="space-y-1">
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Artifact source
                  </p>
                  <p className="text-sm font-medium text-foreground">{sourceLabel}</p>
                  <p className="break-all font-mono text-xs text-muted-foreground">
                    {sourcePath}
                  </p>
                </div>
              </div>

              <div className="mt-4 rounded-[22px] border border-border/60 bg-background/70 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Focus now
                </p>
                <p className="mt-2 text-sm font-semibold text-foreground">
                  {routeMeta.focusTitle}
                </p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {routeMeta.focusDescription}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <main className="mx-auto w-full max-w-[92rem] px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_15rem] xl:items-start">
          <div className="min-w-0">
            <Outlet context={routeContext} />
          </div>
          <aside className="hidden xl:block">
            <div className="sticky top-24 space-y-4">
              <div className="rounded-[24px] border border-border/60 bg-card/75 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Pathway checkpoints
                </p>
                <div className="mt-3 space-y-3">
                  {routeMeta.pathway.map((step, index) => (
                    <div
                      key={`${routeMeta.focusTitle}-${step}`}
                      className="flex gap-3 rounded-[18px] border border-border/60 bg-background/70 px-3 py-3"
                    >
                      <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/12 text-[11px] font-semibold text-primary">
                        {index + 1}
                      </span>
                      <p className="text-sm leading-5 text-foreground">{step}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[24px] border border-border/60 bg-card/75 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Artifact graph
                </p>
                <div className="mt-3 space-y-3 text-sm text-muted-foreground">
                  <div className="rounded-[18px] border border-border/60 bg-background/70 px-3 py-3">
                    <p className="font-semibold text-foreground">
                      {artifactOverview?.runs.count ?? 0} saved runs
                    </p>
                    <p className="mt-1">Primary debugging route through engine-native artifacts.</p>
                  </div>
                  <div className="rounded-[18px] border border-border/60 bg-background/70 px-3 py-3">
                    <p className="font-semibold text-foreground">
                      {artifactOverview?.comparisons.count ?? 0} comparison reports
                    </p>
                    <p className="mt-1">
                      Baseline-versus-candidate evidence stays linked back to runs.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
