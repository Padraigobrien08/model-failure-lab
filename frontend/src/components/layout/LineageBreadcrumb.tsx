import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";
import type { WorkbenchSelection } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type LineageBreadcrumbProps = {
  selection: WorkbenchSelection;
  fallbackVerdict?: string | null;
};

type BreadcrumbNode = {
  label: string;
  value: string;
  href: string;
};

function createHref(selection: WorkbenchSelection, patch: Partial<WorkbenchSelection>, path: string) {
  const params = new URLSearchParams();
  const next = { ...selection, ...patch };

  if (next.scope === "exploratory") {
    params.set("scope", "exploratory");
  }
  if (next.verdict) {
    params.set("verdict", next.verdict);
  }
  if (next.lane) {
    params.set("lane", next.lane);
  }
  if (next.method) {
    params.set("method", next.method);
  }
  if (next.run) {
    params.set("run", next.run);
  }
  if (next.artifact) {
    params.set("artifact", next.artifact);
  }
  if (next.domain) {
    params.set("domain", next.domain);
  }

  const search = params.toString();
  return search ? `${path}?${search}` : path;
}

export function LineageBreadcrumb({
  selection,
  fallbackVerdict,
}: LineageBreadcrumbProps) {
  const activeIndex = selection.artifact
    ? 4
    : selection.run
      ? 3
      : selection.method
        ? 2
        : selection.lane
          ? 1
          : 0;

  const nodes: BreadcrumbNode[] = [
    {
      label: "Verdict",
      value: formatLabel(selection.verdict ?? fallbackVerdict ?? "unknown"),
      href: createHref(selection, { run: null, artifact: null, method: null, lane: null }, "/"),
    },
    {
      label: "Lane",
      value: formatLabel(selection.lane ?? "robustness"),
      href: createHref(selection, { run: null, artifact: null, method: null }, "/lanes"),
    },
    {
      label: "Method",
      value: selection.method ? formatLabel(selection.method) : "No method",
      href: createHref(selection, { run: null, artifact: null }, "/lanes"),
    },
    {
      label: "Run",
      value: selection.run ?? "No run",
      href: createHref(selection, { artifact: null }, "/runs"),
    },
    {
      label: "Artifact",
      value: selection.artifact ?? "No artifact",
      href: createHref(selection, {}, "/evidence"),
    },
  ];

  return (
    <nav
      aria-label="Lineage breadcrumb"
      className="flex flex-wrap items-center gap-2 border-b border-border/70 px-4 py-3 lg:px-6"
    >
      <Badge tone={selection.scope === "exploratory" ? "exploratory" : "accent"}>
        {selection.scope === "exploratory" ? "Include exploratory" : "Official only"}
      </Badge>
      {nodes.map((node, index) => {
        const isActive = index === activeIndex;

        return (
          <div key={node.label} className="flex items-center gap-2">
            {index > 0 ? (
              <ChevronRight
                className="h-4 w-4 text-muted-foreground"
                aria-hidden="true"
              />
            ) : null}
            {isActive ? (
              <span
                className="rounded-full border border-primary/25 bg-primary/10 px-3 py-2 text-xs font-semibold tracking-[0.16em] text-primary"
              >
                {node.label}: {node.value}
              </span>
            ) : (
              <Link
                to={node.href}
                className={cn(
                  "rounded-full border border-border/70 bg-background/55 px-3 py-2 text-xs font-semibold tracking-[0.16em] text-muted-foreground transition-colors hover:border-primary/20 hover:text-foreground",
                )}
              >
                {node.label}: {node.value}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
