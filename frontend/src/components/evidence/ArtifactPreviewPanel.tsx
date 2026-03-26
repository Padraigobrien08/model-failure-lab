import { Badge } from "@/components/ui/badge";
import type { ArtifactPreviewModel } from "@/lib/manifest/types";

type ArtifactPreviewPanelProps = {
  preview: ArtifactPreviewModel | null | undefined;
};

export function ArtifactPreviewPanel({ preview }: ArtifactPreviewPanelProps) {
  if (!preview) {
    return null;
  }

  return (
    <section className="space-y-3">
      <div className="space-y-2">
        <Badge tone="muted">{preview.title}</Badge>
        {preview.description ? (
          <p className="text-sm leading-6 text-muted-foreground">{preview.description}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        {preview.items.map((item) => (
          <div
            key={`${preview.title}-${item.label}-${item.value}`}
            className="rounded-[16px] border border-border/70 bg-background/55 px-4 py-3"
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
    </section>
  );
}
