import { Badge } from "@/components/ui/badge";

type ScopeChipProps = {
  includeExploratory: boolean;
};

export function ScopeChip({ includeExploratory }: ScopeChipProps) {
  if (includeExploratory) {
    return <Badge tone="exploratory">Scope: Official + Exploratory</Badge>;
  }

  return <Badge tone="accent">Scope: Official Only</Badge>;
}
