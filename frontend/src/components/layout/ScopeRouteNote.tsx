import { Badge } from "@/components/ui/badge";

type ScopeRouteNoteProps = {
  message: string;
  modifier?: string;
};

export function ScopeRouteNote({
  message,
  modifier = "Exploratory in view",
}: ScopeRouteNoteProps) {
  return (
    <section
      className="flex flex-wrap items-start gap-3 border border-border/70 bg-muted/10 px-4 py-3"
      data-testid="scope-route-note"
    >
      <Badge tone="exploratory">{modifier}</Badge>
      <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{message}</p>
    </section>
  );
}
