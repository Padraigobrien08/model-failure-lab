import { NavLink, Outlet } from "react-router-dom";

import { NAVIGATION_ITEMS, type AppRouteContext } from "@/app/router";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type TraceShellProps = {
  routeContext: AppRouteContext;
};

export function TraceShell({ routeContext }: TraceShellProps) {
  const artifactOverview = routeContext.artifactOverview;
  const sourceLabel = artifactOverview?.source.label ?? "Local artifact root";
  const sourcePath = artifactOverview?.source.path ?? "Scanning repo-root runs/ and reports/…";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border/60 bg-background/85 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <NavLink
                  to="/"
                  className="text-lg font-semibold tracking-[-0.04em] text-foreground no-underline"
                >
                  Failure Lab
                </NavLink>
                <Badge tone="accent">Engine artifacts</Badge>
              </div>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                The React debugger now opens on saved run artifacts and comparison
                reports from the real `failure-lab` contract.
              </p>
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

          <div className="flex flex-col gap-2 rounded-[24px] border border-border/60 bg-card/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Artifact source
              </p>
              <p className="text-sm font-medium text-foreground">{sourceLabel}</p>
              <p className="break-all font-mono text-xs text-muted-foreground">{sourcePath}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge tone="muted">
                Runs {artifactOverview?.runs.count ?? 0}
              </Badge>
              <Badge tone="muted">
                Comparisons {artifactOverview?.comparisons.count ?? 0}
              </Badge>
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6 lg:px-8">
        <Outlet context={routeContext} />
      </main>
    </div>
  );
}
