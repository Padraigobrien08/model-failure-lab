import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";

type PersistentStateStripProps = {
  includeExploratory: boolean;
  selectedVerdict?: string | null;
  selectedLane?: string | null;
  selectedMethod?: string | null;
  selectedRunId?: string | null;
  manifestStatus?: string | null;
};

type StateItem = {
  label: string;
  value: string;
  tone?: "default" | "accent" | "exploratory" | "muted";
};

function StateCell({ label, value, tone = "muted" }: StateItem) {
  return (
    <div className="min-w-0 rounded-[16px] border border-border/70 bg-background/55 px-3 py-3">
      <div className="flex items-center gap-2">
        <Badge tone={tone}>{label}</Badge>
      </div>
      <p className="mt-2 truncate text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}

export function PersistentStateStrip({
  includeExploratory,
  selectedVerdict,
  selectedLane,
  selectedMethod,
  selectedRunId,
  manifestStatus,
}: PersistentStateStripProps) {
  const items: StateItem[] = [
    {
      label: "Scope",
      value: includeExploratory ? "Official + Exploratory" : "Official Only",
      tone: includeExploratory ? "exploratory" : "accent",
    },
    {
      label: "Verdict",
      value: selectedVerdict ? formatLabel(selectedVerdict) : "Not loaded",
      tone: "accent",
    },
    {
      label: "Lane",
      value: selectedLane ? formatLabel(selectedLane) : "No active lane",
    },
    {
      label: "Method",
      value: selectedMethod ? formatLabel(selectedMethod) : "No active method",
    },
    {
      label: "Run",
      value: selectedRunId ?? "No selected run",
    },
    {
      label: "Manifest",
      value: manifestStatus ?? "Manifest unavailable",
    },
  ];

  return (
    <section
      aria-label="Workbench state"
      className="grid gap-2 border-b border-border/70 px-4 py-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6"
    >
      {items.map((item) => (
        <StateCell key={item.label} {...item} />
      ))}
    </section>
  );
}
