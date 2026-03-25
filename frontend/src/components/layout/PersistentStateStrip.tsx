import { Badge } from "@/components/ui/badge";
import { formatLabel } from "@/lib/formatters";

type PersistentStateStripProps = {
  includeExploratory: boolean;
  finalRobustnessVerdict?: string;
  datasetExpansionRecommendation?: string;
  selectedMethod?: string | null;
  selectedDomain?: string | null;
  selectedRunId?: string | null;
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
  finalRobustnessVerdict,
  datasetExpansionRecommendation,
  selectedMethod,
  selectedDomain,
  selectedRunId,
}: PersistentStateStripProps) {
  const items: StateItem[] = [
    {
      label: "Scope",
      value: includeExploratory ? "Official + Exploratory" : "Official Only",
      tone: includeExploratory ? "exploratory" : "accent",
    },
    {
      label: "Verdict",
      value: finalRobustnessVerdict ? formatLabel(finalRobustnessVerdict) : "Not loaded",
      tone: "accent",
    },
    {
      label: "Gate",
      value: datasetExpansionRecommendation
        ? formatLabel(datasetExpansionRecommendation)
        : "Not loaded",
    },
    {
      label: "Lane",
      value: selectedMethod ? formatLabel(selectedMethod) : "No focused lane",
    },
    {
      label: "Domain",
      value: selectedDomain ? formatLabel(selectedDomain) : "No domain focus",
    },
    {
      label: "Run",
      value: selectedRunId ?? "No selected run",
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
