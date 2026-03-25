import { Badge } from "@/components/ui/badge";

type ScopeChipProps = {
  includeExploratory: boolean;
};

export function ScopeChip({ includeExploratory }: ScopeChipProps) {
  if (includeExploratory) {
    return <Badge tone="exploratory">Exploratory Evidence On</Badge>;
  }

  return <Badge tone="accent">Official Evidence Only</Badge>;
}
