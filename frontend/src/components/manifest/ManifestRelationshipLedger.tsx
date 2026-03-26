import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ManifestRelationshipLedgerModel } from "@/lib/manifest/types";
import { cn } from "@/lib/utils";

type ManifestRelationshipLedgerProps = {
  model: ManifestRelationshipLedgerModel;
  onSelectEntity: (id: string, entityType: "report" | "evaluation" | "run") => void;
};

export function ManifestRelationshipLedger({
  model,
  onSelectEntity,
}: ManifestRelationshipLedgerProps) {
  return (
    <div className="space-y-6">
      <section className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          {model.selectedBadges.map((badge) => (
            <Badge key={`${badge.label}-${badge.tone}`} tone={badge.tone}>
              {badge.label}
            </Badge>
          ))}
        </div>
        <div className="space-y-2">
          <h3 className="text-[1.9rem] font-semibold tracking-[-0.05em] text-foreground">
            {model.selectedTitle}
          </h3>
          <p className="font-mono text-xs leading-6 text-muted-foreground">
            {model.selectedSubtitle}
          </p>
          {model.selectedDescription ? (
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              {model.selectedDescription}
            </p>
          ) : null}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="muted">Entity focus</Badge>
          <Badge tone={model.selectedScope === "exploratory" ? "exploratory" : "accent"}>
            {model.selectedScope === "exploratory" ? "Exploratory" : "Official"}
          </Badge>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {model.entityOptions.map((option) => (
            <button
              key={`${option.entityType}-${option.id}`}
              type="button"
              className={cn(
                "rounded-[16px] border bg-background/55 px-4 py-4 text-left transition-colors",
                option.isSelected
                  ? "border-primary/30 shadow-panel"
                  : "border-border/70 hover:border-primary/20",
                option.scope === "exploratory" ? "border-dashed" : "",
              )}
              onClick={() => onSelectEntity(option.id, option.entityType)}
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="muted">{option.entityType}</Badge>
                <Badge tone={option.scope === "exploratory" ? "exploratory" : "accent"}>
                  {option.scope}
                </Badge>
              </div>
              <p className="mt-3 text-sm font-semibold text-foreground">{option.title}</p>
              <p className="mt-1 font-mono text-xs leading-5 text-muted-foreground">
                {option.subtitle}
              </p>
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        {model.sections.map((section) => (
          <div
            key={section.title}
            className="rounded-[18px] border border-border/70 bg-background/55 p-4"
          >
            <div className="flex items-center justify-between gap-4">
              <Badge tone="muted">{section.title}</Badge>
              <Button variant="ghost" size="sm" disabled>
                Read-only
              </Button>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {section.items.map((item) => (
                <div
                  key={`${section.title}-${item.label}-${item.value}`}
                  className="rounded-[14px] border border-border/70 bg-card/45 px-4 py-3"
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    {item.label}
                  </p>
                  <p
                    className={item.mono ? "mt-1 break-all font-mono text-xs leading-6 text-foreground" : "mt-1 text-sm leading-6 text-foreground"}
                  >
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
