import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { RunDetailSummaryRow, RunTagSlice } from "@/lib/artifacts/types";
import { formatLabel } from "@/lib/formatters";

type RunSummarySectionsProps = {
  failureTypes: RunDetailSummaryRow[];
  expectationVerdicts: RunDetailSummaryRow[];
  tagSlices: RunTagSlice[];
};

const DEFAULT_LIMIT = 5;

function formatPercent(value: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function RankedSummarySection({
  title,
  description,
  rows,
}: {
  title: string;
  description: string;
  rows: RunDetailSummaryRow[];
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleRows = expanded ? rows : rows.slice(0, DEFAULT_LIMIT);

  return (
    <Card className="rounded-[24px] bg-card/75">
      <CardHeader className="space-y-1 pb-3">
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {visibleRows.length > 0 ? (
          visibleRows.map((row, index) => (
            <div
              key={`${title}-${row.label}`}
              className="flex items-start justify-between gap-3 rounded-[18px] border border-border/60 bg-background/60 px-3.5 py-3"
            >
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-foreground">
                    {formatLabel(row.label)}
                  </p>
                  {index === 0 ? <Badge tone="accent">Highest share</Badge> : null}
                </div>
                <p className="text-xs text-muted-foreground">{row.caseIds.length} linked cases</p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Badge tone="muted">{row.count}</Badge>
                <Badge tone="default">{formatPercent(row.share)}</Badge>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No rows available for this section.</p>
        )}

        {rows.length > DEFAULT_LIMIT ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((current) => !current)}
          >
            {expanded ? "Show fewer" : `Show ${rows.length - DEFAULT_LIMIT} more`}
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}

function TagSlicesSection({ rows }: { rows: RunTagSlice[] }) {
  const [expanded, setExpanded] = useState(false);
  const visibleRows = expanded ? rows : rows.slice(0, DEFAULT_LIMIT);

  return (
    <Card className="rounded-[24px] bg-card/75">
      <CardHeader className="space-y-1 pb-3">
        <CardTitle className="text-lg">Tag pressure points</CardTitle>
        <CardDescription>
          Which tags carry the most failure pressure once attempted and classified cases are
          factored in.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {visibleRows.length > 0 ? (
          visibleRows.map((row) => (
            <div
              key={row.tag}
              className="rounded-[18px] border border-border/60 bg-background/60 px-3.5 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">{formatLabel(row.tag)}</p>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge tone="muted">{row.failureCaseCount}</Badge>
                  <Badge tone="default">{formatPercent(row.failureRate)}</Badge>
                </div>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {row.failureCaseCount} failures / {row.classifiedCaseCount} classified /{" "}
                {row.attemptedCaseCount} attempted
              </p>
              {Object.keys(row.expectationVerdictCounts).length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {Object.entries(row.expectationVerdictCounts).map(([label, count]) => (
                    <Badge key={`${row.tag}-${label}`} tone="muted">
                      {formatLabel(label)} {count}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No tag slices are available yet.</p>
        )}

        {rows.length > DEFAULT_LIMIT ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((current) => !current)}
          >
            {expanded ? "Show fewer" : `Show ${rows.length - DEFAULT_LIMIT} more`}
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function RunSummarySections({
  failureTypes,
  expectationVerdicts,
  tagSlices,
}: RunSummarySectionsProps) {
  return (
    <section className="space-y-4" aria-label="Run summaries">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Stage 3 · Diagnosis
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Why it failed
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Separate the dominant failure labels, expectation drift, and tag hotspots before opening
          individual rows.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
        <RankedSummarySection
          title="Failure types"
          description="Most common classifier labels in this run."
          rows={failureTypes}
        />
        <RankedSummarySection
          title="Expectation verdicts"
          description="Where expected and observed outcomes diverged."
          rows={expectationVerdicts}
        />
        <TagSlicesSection rows={tagSlices} />
      </div>
    </section>
  );
}
