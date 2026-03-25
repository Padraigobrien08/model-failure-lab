import { FileSearch, FlaskConical, Layers3, Radar, Rows3 } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { EvidenceDrawer } from "@/components/evidence/EvidenceDrawer";
import { PersistentStateStrip } from "@/components/layout/PersistentStateStrip";
import { ScopeChip } from "@/components/layout/ScopeChip";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NAVIGATION_ITEMS } from "@/app/router";
import { formatComparisonMode, formatLabel } from "@/lib/formatters";
import { artifactPathToPublicUrl } from "@/lib/manifest/load";
import { buildEvidenceDrawerModel, buildOverviewSnapshot } from "@/lib/manifest/selectors";
import { cn } from "@/lib/utils";

type AppShellProps = {
  includeExploratory: boolean;
  onToggleExploratory: (next: boolean) => void;
  manifestPath: string;
  routeContext: AppRouteContext;
};

const ICONS = [Rows3, Layers3, FlaskConical, Radar, FileSearch];

function getDirectRefPath(value: unknown) {
  return typeof value === "object" && value !== null && "path" in value
    ? String((value as { path: string }).path)
    : null;
}

export function AppShell({
  includeExploratory,
  onToggleExploratory,
  manifestPath,
  routeContext,
}: AppShellProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const focusMethod = routeContext.selectedMethod
    ? formatLabel(routeContext.selectedMethod)
    : "No focused lane";
  const focusDomain = routeContext.selectedDomain
    ? formatLabel(routeContext.selectedDomain)
    : "No domain focus";
  const finalReport = routeContext.finalRobustnessBundle?.report;
  const reportMarkdownPath = getDirectRefPath(finalReport?.artifact_refs?.report_markdown);
  const reportPayloadPath = getDirectRefPath(finalReport?.artifact_refs?.report_data_json);
  const overviewSnapshot = routeContext.index
    ? buildOverviewSnapshot(routeContext.index, includeExploratory)
    : null;
  const evidenceDrawerModel =
    routeContext.index && routeContext.finalRobustnessBundle
      ? buildEvidenceDrawerModel(
          routeContext.index,
          routeContext.finalRobustnessBundle,
          routeContext.selectedRunId,
        )
      : null;

  function handleOpenRunsView(runId: string) {
    routeContext.setSelectedRunId(runId);
    routeContext.closeEvidenceDrawer();
    navigate("/runs");
  }

  return (
    <div className="min-h-screen px-3 py-3 sm:px-4 lg:px-6">
      <div className="mx-auto grid min-h-[calc(100vh-1.5rem)] max-w-[1680px] gap-3 lg:grid-cols-[240px_minmax(0,1fr)_308px]">
        <aside className="rounded-[24px] border border-border/70 bg-card/78 p-4 shadow-rail backdrop-blur-sm">
          <div className="space-y-6">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-primary">
                Model Failure Lab
              </p>
              <div className="space-y-2">
                <h1 className="text-[1.85rem] font-semibold tracking-[-0.05em] text-foreground">
                  Failure Debugger
                </h1>
                <p className="text-sm leading-6 text-muted-foreground">
                  Dense manifest-backed workbench for verdicts, lanes, runs, and evidence.
                </p>
              </div>
            </div>

            <div className="space-y-3 rounded-[18px] border border-border/70 bg-background/45 p-3">
              <ScopeChip includeExploratory={includeExploratory} />
              <Button
                variant={includeExploratory ? "outline" : "default"}
                className="w-full justify-center"
                onClick={() => onToggleExploratory(!includeExploratory)}
              >
                {includeExploratory ? "Hide exploratory evidence" : "Show exploratory evidence"}
              </Button>
              <p className="text-xs leading-5 text-muted-foreground">
                Default scope stays official. Expand only when you intentionally want the scout
                lanes in the same workspace.
              </p>
            </div>

            <nav className="space-y-2" aria-label="Primary">
              {NAVIGATION_ITEMS.map((item, index) => {
                const Icon = ICONS[index];

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      cn(
                        "flex items-start gap-3 rounded-[18px] border border-transparent px-3 py-3 transition-colors",
                        isActive
                          ? "border-primary/20 bg-primary/10 text-foreground"
                          : "text-muted-foreground hover:border-border/80 hover:bg-card hover:text-foreground",
                      )
                    }
                  >
                    <Icon className="mt-0.5 h-4 w-4 flex-none" aria-hidden="true" />
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold">{item.label}</span>
                      <span className="block text-xs leading-5 opacity-80">
                        {item.description}
                      </span>
                    </span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </aside>

        <main className="overflow-hidden rounded-[24px] border border-border/70 bg-card/72 shadow-panel backdrop-blur-sm">
          <div className="border-b border-border/70 px-4 py-4 lg:px-6">
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_260px]">
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-primary">
                  Analytical Workbench
                </p>
                <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                  Trace the current failure story from official verdicts into comparisons, runs,
                  and artifact paths without switching truth models.
                </p>
              </div>
              <div className="rounded-[16px] border border-border/70 bg-background/55 px-4 py-3 text-sm leading-6 text-muted-foreground">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                  Current route
                </p>
                <p className="mt-1 font-medium text-foreground">
                  {NAVIGATION_ITEMS.find((item) => item.path === location.pathname)?.label ??
                    "Overview"}
                </p>
                <p className="mt-1">
                  {NAVIGATION_ITEMS.find((item) => item.path === location.pathname)?.description ??
                    "Final verdicts and official evidence launchpad"}
                </p>
              </div>
            </div>
          </div>

          <PersistentStateStrip
            includeExploratory={includeExploratory}
            finalRobustnessVerdict={overviewSnapshot?.finalRobustnessVerdict}
            datasetExpansionRecommendation={overviewSnapshot?.datasetExpansionRecommendation}
            selectedMethod={routeContext.selectedMethod}
            selectedDomain={routeContext.selectedDomain}
            selectedRunId={routeContext.selectedRunId}
          />

          <div className="px-4 py-5 lg:px-6">
            <Outlet context={routeContext} />
          </div>
        </main>

        <aside className="hidden rounded-[24px] border border-border/70 bg-card/78 p-4 shadow-rail backdrop-blur-sm lg:block">
          <Card className="border-none bg-transparent shadow-none">
            <CardHeader className="px-0 pb-4 pt-0">
              <CardDescription>Inspector Dock</CardDescription>
              <CardTitle>
                {routeContext.isEvidenceDrawerOpen && evidenceDrawerModel
                  ? "Quick drillthrough"
                  : "Provenance and route state"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 px-0 pb-0">
              {routeContext.isEvidenceDrawerOpen && evidenceDrawerModel ? (
                <EvidenceDrawer
                  model={evidenceDrawerModel}
                  onClose={routeContext.closeEvidenceDrawer}
                  onOpenRunsView={handleOpenRunsView}
                />
              ) : (
                <>
                  <div className="rounded-[18px] border border-border/80 bg-background/55 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Contract path
                    </p>
                    <p className="mt-2 break-all font-mono text-xs leading-6 text-foreground">
                      {manifestPath}
                    </p>
                  </div>

                  <div className="rounded-[18px] border border-border/80 bg-background/55 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Workbench posture
                    </p>
                    <p className="mt-2 text-sm leading-6 text-foreground">
                      The left rail sets mode, the center pane carries the active analysis, and the
                      dock stays reserved for provenance and drillthrough. Keep route-local reading
                      inside that frame.
                    </p>
                  </div>

                  <div className="rounded-[18px] border border-border/80 bg-background/55 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Active focus
                    </p>
                    <p className="mt-2 text-sm leading-6 text-foreground">{focusMethod}</p>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {location.pathname === "/failure-explorer"
                        ? `${focusDomain} tab`
                        : focusDomain}
                    </p>
                  </div>

                  {finalReport ? (
                    <div className="rounded-[18px] border border-border/80 bg-background/55 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                        Comparison package
                      </p>
                      <p className="mt-2 text-sm leading-6 text-foreground">
                        {formatComparisonMode(routeContext.finalRobustnessBundle?.summary.official_methods[0]?.comparison_mode)}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        {reportMarkdownPath ? (
                          <a
                            className="rounded-full border border-border px-3 py-1.5 text-foreground transition-colors hover:border-primary/30 hover:text-primary"
                            href={artifactPathToPublicUrl(reportMarkdownPath)}
                            target="_blank"
                            rel="noreferrer"
                          >
                            View report
                          </a>
                        ) : null}
                        {reportPayloadPath ? (
                          <a
                            className="rounded-full border border-border px-3 py-1.5 text-foreground transition-colors hover:border-primary/30 hover:text-primary"
                            href={artifactPathToPublicUrl(reportPayloadPath)}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open payload
                          </a>
                        ) : null}
                      </div>
                    </div>
                  ) : null}

                  <div className="rounded-[18px] border border-border/80 bg-background/55 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Scope rule
                    </p>
                    <p className="mt-2 text-sm leading-6 text-foreground">
                      Official evidence stays default. Exploratory methods only appear when the user
                      explicitly broadens scope.
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
