import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ScopeStateBannerProps = {
  includeExploratory: boolean;
  onChange: (next: boolean) => void;
  className?: string;
};

export function ScopeStateBanner({
  includeExploratory,
  onChange,
  className,
}: ScopeStateBannerProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone="muted">Evidence scope</Badge>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={includeExploratory ? "ghost" : "default"}
            size="sm"
            aria-pressed={!includeExploratory}
            onClick={() => onChange(false)}
          >
            Official only
          </Button>
          <Button
            variant={includeExploratory ? "outline" : "ghost"}
            size="sm"
            aria-pressed={includeExploratory}
            onClick={() => onChange(true)}
          >
            Include exploratory
          </Button>
        </div>
      </div>

      {includeExploratory ? (
        <div className="rounded-[22px] border border-dashed border-primary/35 bg-primary/10 px-4 py-4 text-sm leading-6 text-foreground">
          Exploratory evidence is enabled. Rejected scout runs stay clearly labeled and should not
          be read as part of the default official story.
        </div>
      ) : (
        <div className="rounded-[22px] border border-border/70 bg-background/55 px-4 py-4 text-sm leading-6 text-muted-foreground">
          Official evidence stays default here. Expand scope only when you intentionally want the
          rejected scout lanes in view.
        </div>
      )}
    </div>
  );
}
