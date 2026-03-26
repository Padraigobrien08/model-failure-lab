import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvidenceSectionModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type EvidenceEntitySectionProps = {
  section: EvidenceSectionModel;
  selectedItemId?: string | null;
  onInspectItem?: (id: string, entityType: "report" | "evaluation" | "run", relatedRunId?: string | null) => void;
};

export function EvidenceEntitySection({
  section,
  selectedItemId,
  onInspectItem,
}: EvidenceEntitySectionProps) {
  return (
    <section className="space-y-4">
      <header className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge tone="accent">{section.title}</Badge>
          <Badge tone="muted">{section.items.length} items</Badge>
        </div>
        <h3 className="text-[1.9rem] font-semibold tracking-[-0.05em] text-foreground">
          {section.title}
        </h3>
        <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{section.description}</p>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        {section.items.map((item) => (
          <Card
            key={`${section.key}-${item.id}`}
            className={cn(
              "bg-background/60",
              item.scope === "exploratory" ? "border-dashed" : "",
              selectedItemId === item.id ? "border-primary/35 shadow-panel" : "",
            )}
          >
            <CardHeader className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={item.scope === "exploratory" ? "exploratory" : "accent"}>
                  {item.scope}
                </Badge>
                <Badge tone="default">{item.badgeLabel}</Badge>
                <Badge tone="muted">{item.entityType}</Badge>
                {item.defaultVisible ? <Badge tone="accent">default_visible</Badge> : null}
              </div>
              <div className="space-y-2">
                <CardDescription>{item.subtitle}</CardDescription>
                <CardTitle className="text-[1.5rem]">{item.title}</CardTitle>
                {item.description ? (
                  <p className="text-sm leading-6 text-muted-foreground">{item.description}</p>
                ) : null}
                {item.sourcePath ? (
                  <p className="break-all font-mono text-xs leading-6 text-muted-foreground">
                    {item.sourcePath}
                  </p>
                ) : null}
              </div>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {onInspectItem ? (
                <Button
                  variant={selectedItemId === item.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => onInspectItem(item.id, item.entityType, item.relatedRunId)}
                >
                  {selectedItemId === item.id ? "Provenance focused" : "Inspect provenance"}
                </Button>
              ) : null}
              {item.actions.map((action) => (
                <a
                  key={`${item.id}-${action.label}-${action.path}`}
                  href={action.path}
                  target="_blank"
                  rel="noreferrer"
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                >
                  {action.label}
                </a>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
