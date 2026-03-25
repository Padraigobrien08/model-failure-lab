import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RunCardModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type RunCardProps = {
  run: RunCardModel;
  isSelected: boolean;
  onSelectRun: (runId: string) => void;
};

export function RunCard({ run, isSelected, onSelectRun }: RunCardProps) {
  return (
    <Card
      className={cn(
        "bg-background/60",
        isSelected ? "border-primary/35 shadow-panel" : "",
        run.isExploratory ? "border-dashed" : "",
      )}
    >
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={run.isExploratory ? "exploratory" : "accent"}>
            {run.isOfficial ? "Official" : "Exploratory"}
          </Badge>
          <Badge tone="default">{run.seedLabel}</Badge>
          <Badge tone="muted">{run.verdict}</Badge>
        </div>
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            {run.methodName}
          </p>
          <CardTitle className="text-[1.4rem]">{run.displayName}</CardTitle>
          <p className="font-mono text-xs leading-5 text-muted-foreground">{run.runId}</p>
          <p className="text-sm leading-6 text-muted-foreground">{run.summaryLabel}</p>
        </div>
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-4">
        <p className="text-xs text-muted-foreground">
          {run.timestamp ? `Saved ${run.timestamp.slice(0, 10)}` : "Saved run"}
        </p>
        <Button
          variant={isSelected ? "default" : "outline"}
          size="sm"
          aria-pressed={isSelected}
          aria-label={`Inspect ${run.displayName} run ${run.seedLabel}`}
          onClick={() => onSelectRun(run.runId)}
        >
          {isSelected ? "Selected run" : "Inspect run"}
        </Button>
      </CardContent>
    </Card>
  );
}
