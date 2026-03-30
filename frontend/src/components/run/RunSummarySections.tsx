import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  rows,
}: {
  title: string;
  rows: RunDetailSummaryRow[];
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleRows = expanded ? rows : rows.slice(0, DEFAULT_LIMIT);

  return (
    <Card className="rounded-[24px] bg-card/75">
      <CardHeader className="space-y-1 pb-4">
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {visibleRows.length > 0 ? (
          visibleRows.map((row) => (
            <div
              key={`${title}-${row.label}`}
              className="flex items-center justify-between gap-3 rounded-[18px] border border-border/60 bg-background/60 px-4 py-3"
            >
              <div className="space-y-1">
                <p className="text-sm font-semibold text-foreground">{formatLabel(row.label)}</p>
                <p className="text-xs text-muted-foreground">{row.caseIds.length} case ids linked</p>
              </div>
              <div className="flex items-center gap-2">
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
      <CardHeader className="space-y-1 pb-4">
        <CardTitle className="text-lg">Tag slices</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {visibleRows.length > 0 ? (
          visibleRows.map((row) => (
            <div
              key={row.tag}
              className="rounded-[18px] border border-border/60 bg-background/60 px-4 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">{formatLabel(row.tag)}</p>
                <div className="flex items-center gap-2">
                  <Badge tone="muted">{row.failureCaseCount}</Badge>
                  <Badge tone="default">{formatPercent(row.failureRate)}</Badge>
                </div>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Failures {row.failureCaseCount} / classified {row.classifiedCaseCount} / attempted{" "}
                {row.attemptedCaseCount}
              </p>
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
          Summary
        </p>
        <h2 className="text-2xl font-semibold tracking-[-0.04em] text-foreground">
          Failure types, verdicts, and tag slices
        </h2>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <RankedSummarySection title="Failure types" rows={failureTypes} />
        <RankedSummarySection title="Expectation verdicts" rows={expectationVerdicts} />
        <TagSlicesSection rows={tagSlices} />
      </div>
    </section>
  );
}
