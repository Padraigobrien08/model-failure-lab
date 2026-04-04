import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ArtifactInsightEvidenceRef, ArtifactInsightReport } from "@/lib/artifacts/types";

type InsightPanelProps = {
  badgeLabel: string;
  title: string;
  description: string;
  report: ArtifactInsightReport | null;
  renderEvidenceLink: (reference: ArtifactInsightEvidenceRef) => ReactNode;
};

function formatShare(share: number | null): string {
  if (share == null) {
    return "n/a";
  }
  return `${(share * 100).toFixed(1)}%`;
}

export function InsightPanel({
  badgeLabel,
  title,
  description,
  report,
  renderEvidenceLink,
}: InsightPanelProps) {
  if (report === null) {
    return null;
  }

  return (
    <Card className="rounded-[28px] border border-primary/20 bg-primary/[0.035]">
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">{badgeLabel}</Badge>
          <Badge tone="muted">{report.analysisMode}</Badge>
          <Badge tone="muted">{report.sampling.sampledMatches} sampled</Badge>
        </div>
        <div className="space-y-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <p className="text-sm leading-6 text-foreground">{report.summary}</p>
      </CardHeader>
      <CardContent className="space-y-6">
        {report.patterns.length > 0 ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Key patterns
            </p>
            <div className="grid gap-4 lg:grid-cols-2">
              {report.patterns.map((pattern) => (
                <div
                  key={`${pattern.kind}:${pattern.groupKey ?? pattern.label}`}
                  className="rounded-[20px] border border-border/70 bg-background/75 p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="accent">{pattern.label}</Badge>
                    <Badge tone="muted">{pattern.count} cases</Badge>
                    <Badge tone="muted">{formatShare(pattern.share)}</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-foreground">{pattern.summary}</p>
                  {pattern.evidenceRefs.length > 0 ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {pattern.evidenceRefs.map((reference) =>
                        renderEvidenceLink(reference),
                      )}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {report.anomalies.length > 0 ? (
          <section className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Notable outliers
            </p>
            <div className="grid gap-4 lg:grid-cols-2">
              {report.anomalies.map((anomaly) => (
                <div
                  key={`${anomaly.kind}:${anomaly.groupKey ?? anomaly.label}`}
                  className="rounded-[20px] border border-border/70 bg-background/75 p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="default">{anomaly.label}</Badge>
                    <Badge tone="muted">{formatShare(anomaly.share)}</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-foreground">{anomaly.summary}</p>
                  {anomaly.evidenceRefs.length > 0 ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {anomaly.evidenceRefs.map((reference) =>
                        renderEvidenceLink(reference),
                      )}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <div className="rounded-[18px] border border-border/70 bg-background/70 p-4 text-sm text-muted-foreground">
          Sampling strategy: {report.sampling.strategy}. Visible evidence covers{" "}
          {report.sampling.sampledMatches} of {report.sampling.totalMatches} matched rows.
        </div>
      </CardContent>
    </Card>
  );
}
