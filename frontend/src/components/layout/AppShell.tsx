import { FileSearch, GitBranch, Radar, Scale, ScrollText } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { EvidenceDrawer } from "@/components/evidence/EvidenceDrawer";
import { LineageBreadcrumb } from "@/components/layout/LineageBreadcrumb";
import { PersistentStateStrip } from "@/components/layout/PersistentStateStrip";
import { ScopeChip } from "@/components/layout/ScopeChip";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NAVIGATION_ITEMS } from "@/app/router";
import { formatComparisonMode, formatLabel } from "@/lib/formatters";
import { artifactPathToPublicUrl } from "@/lib/manifest/load";
import {
  buildEvidenceDrawerModel,
  buildOverviewSnapshot,
  buildVerdictWorkspaceModel,
} from "@/lib/manifest/selectors";
import { cn } from "@/lib/utils";

type AppShellProps = {
  includeExploratory: boolean;
  onToggleExploratory: (next: boolean) => void;
  manifestPath: string;
  routeContext: AppRouteContext;
};

const ICONS = [Scale, Radar, GitBranch, FileSearch, ScrollText];

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
  const verdictWorkspace =
    routeContext.index && routeContext.finalRobustnessBundle
      ? buildVerdictWorkspaceModel(
          routeContext.index,
          routeContext.finalRobustnessBundle,
          includeExploratory,
        )
      : null;
  const currentRoute =
    NAVIGATION_ITEMS.find((item) => item.path === location.pathname) ?? NAVIGATION_ITEMS[0];
  const manifestStatus = routeContext.index
    ? `${routeContext.index.schema_version}${routeContext.index.generated_at ? ` · ${routeContext.index.generated_at.slice(0, 10)}` : ""}`
    : "Loading manifest";

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
                {includeExploratory ? "Official only" : "Include exploratory"}
              </Button>
              <p className="text-xs leading-5 text-muted-foreground">
                Official evidence stays canonical. Broaden scope only when you intentionally want
                exploratory scouts in the same lineage view.
              </p>
              {includeExploratory ? (
                <div className="rounded-[14px] border border-dashed border-amber-700/40 bg-amber-950/20 px-3 py-3 text-xs leading-5 text-amber-100">
                  Exploratory evidence is enabled because you explicitly broadened scope. Keep it
                  distinct from the official verdict path.
                </div>
              ) : null}
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
                  Trace the current failure story from verdicts into lanes, runs, artifacts, and
                  manifest provenance without switching truth models.
                </p>
              </div>
              <div className="rounded-[16px] border border-border/70 bg-background/55 px-4 py-3 text-sm leading-6 text-muted-foreground">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                  Current route
                </p>
                <p className="mt-1 font-medium text-foreground">
                  {currentRoute.label}
                </p>
                <p className="mt-1">{currentRoute.description}</p>
              </div>
            </div>
          </div>

          <LineageBreadcrumb
            selection={routeContext.selection}
            fallbackVerdict={verdictWorkspace?.finalVerdict ?? overviewSnapshot?.finalRobustnessVerdict}
          />

          <PersistentStateStrip
            includeExploratory={includeExploratory}
            selectedVerdict={routeContext.selectedVerdict ?? verdictWorkspace?.finalVerdict}
            selectedLane={routeContext.selectedLane}
            selectedMethod={routeContext.selectedMethod}
            selectedRunId={routeContext.selectedRunId}
            manifestStatus={manifestStatus}
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
                      Selected lineage
                    </p>
                    <div className="mt-3 space-y-2 text-sm leading-6">
                      <p className="text-foreground">
                        Verdict: {formatLabel(routeContext.selectedVerdict ?? verdictWorkspace?.finalVerdict)}
                      </p>
                      <p className="text-foreground">
                        Lane: {formatLabel(routeContext.selectedLane ?? verdictWorkspace?.dominantLaneKey)}
                      </p>
                      <p className="text-foreground">
                        Method: {routeContext.selectedMethod ? formatLabel(routeContext.selectedMethod) : "No active method"}
                      </p>
                      <p className="text-muted-foreground">
                        Run: {routeContext.selectedRunId ?? "No selected run"}
                      </p>
                    </div>
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
                      Official evidence stays default. Exploratory entities appear only because the
                      global scope state says they should be visible.
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
