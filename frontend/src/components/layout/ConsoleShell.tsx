import { NavLink, Outlet } from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { NAVIGATION_ITEMS } from "@/app/router";
import { SectionLabel, StatusChip } from "@/components/console/primitives";
import type { ChipTone } from "@/components/console/primitives";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const APP_VERSION = "v0.9.0 · local";

function navCount(context: AppRouteContext, path: string): string | null {
  const overview = context.artifactOverview;
  switch (path) {
    case "/":
      return overview ? String(overview.runs.count) : null;
    case "/comparisons":
      return overview ? String(overview.comparisons.count) : null;
    case "/datasets":
      return context.datasetFamiliesState.status === "ready"
        ? String(context.datasetFamiliesState.data.families.length)
        : null;
    default:
      return null;
  }
}

function contractHealth(context: AppRouteContext): { tone: ChipTone; label: string } {
  switch (context.artifactState.status) {
    case "ready":
      return { tone: "good", label: "contract clean" };
    case "empty":
      return { tone: "warn", label: "no artifacts" };
    case "incompatible":
      return { tone: "bad", label: "contract issues" };
    default:
      return { tone: "neutral", label: "loading" };
  }
}

function GateNavRow({ context }: { context: AppRouteContext }) {
  const gate = context.gateState;
  let chip: { tone: ChipTone; label: string } | null = null;
  if (gate.status === "ready") {
    chip = gate.data.rows.length === 0
      ? { tone: "neutral", label: "NO DATA" }
      : gate.data.blocked
        ? { tone: "bad", label: "FAIL" }
        : { tone: "good", label: "PASS" };
  }
  return (
    <NavLink
      to="/gate"
      className={({ isActive }) =>
        cn(
          "flex items-center justify-between rounded-tok border px-[10px] py-2 text-[13.5px] text-ink hover:bg-raised",
          isActive ? "border-accent bg-accent-wash" : "border-transparent",
        )
      }
    >
      Gate
      {chip ? (
        <StatusChip tone={chip.tone} uppercase>
          {chip.label}
        </StatusChip>
      ) : (
        <span className="font-mono text-[11px] text-muted-ink">—</span>
      )}
    </NavLink>
  );
}

export function ConsoleShell({ routeContext }: { routeContext: AppRouteContext }) {
  const { theme, toggleTheme } = useTheme();
  const health = contractHealth(routeContext);
  const rootPath = routeContext.artifactOverview?.source.path ?? null;

  return (
    <div className="flex h-screen min-w-[1180px] overflow-hidden bg-ground font-body text-ink">
      <aside className="flex w-[216px] flex-none flex-col border-r border-line bg-panel py-[17px]">
        <div className="px-[15px] pb-[18px]">
          <div className="font-heading text-[15px] font-semibold uppercase leading-none tracking-[0.14em]">
            Failure Lab
          </div>
          <div className="mt-[5px] font-mono text-[10px] text-muted-ink">{APP_VERSION}</div>
        </div>

        <nav aria-label="Primary" className="flex flex-col gap-[2px] px-2">
          {NAVIGATION_ITEMS.map((item) => {
            const count = navCount(routeContext, item.path);
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center justify-between rounded-tok border px-[10px] py-2 text-[13.5px] text-ink hover:bg-raised",
                    isActive ? "border-accent bg-accent-wash" : "border-transparent",
                  )
                }
              >
                {item.label}
                {count !== null ? (
                  <span className="font-mono text-[11px] text-muted-ink">{count}</span>
                ) : null}
              </NavLink>
            );
          })}
          <GateNavRow context={routeContext} />
        </nav>

        <div className="mt-auto flex flex-col gap-2.5 border-t border-line p-[15px]">
          <SectionLabel className="text-[9.5px] tracking-[0.16em]">Artifact root</SectionLabel>
          <div className="break-all font-mono text-[10.5px] leading-normal">
            {rootPath ?? "resolving…"}
          </div>
          <StatusChip tone={health.tone} className="w-fit text-[10.5px]">
            <span
              aria-hidden="true"
              className="h-[5px] w-[5px] rounded-full bg-current"
            />
            {health.label}
          </StatusChip>
          <div className="flex items-center gap-2 border-t border-line pt-1.5">
            <span className="font-mono text-[10px] text-muted-ink">theme</span>
            <button
              type="button"
              onClick={toggleTheme}
              className="ml-auto inline-flex cursor-pointer items-center rounded-tok border border-accent bg-transparent px-[10px] py-[5px] font-body text-[11.5px] text-accent-text"
            >
              {theme === "light" ? "Light" : "Dark"}
            </button>
          </div>
        </div>
      </aside>

      <main className="console-main flex min-w-0 flex-1 flex-col overflow-hidden">
        <Outlet context={routeContext} />
      </main>
    </div>
  );
}
