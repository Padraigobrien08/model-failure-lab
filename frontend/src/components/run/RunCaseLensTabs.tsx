import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { RunCaseLensKey } from "@/lib/artifacts/types";
import { formatCount, formatLabel } from "@/lib/formatters";

type RunCaseLensTabsProps = {
  value: RunCaseLensKey;
  counts: Record<RunCaseLensKey, number>;
  onValueChange: (value: RunCaseLensKey) => void;
};

const LENS_ORDER: RunCaseLensKey[] = ["mismatches", "notable", "all", "errors"];

export function RunCaseLensTabs({
  value,
  counts,
  onValueChange,
}: RunCaseLensTabsProps) {
  return (
    <Tabs value={value} onValueChange={(nextValue) => onValueChange(nextValue as RunCaseLensKey)}>
      <TabsList>
        {LENS_ORDER.map((lens) => (
          <TabsTrigger key={lens} value={lens}>
            {formatLabel(lens)} ({formatCount(counts[lens] ?? 0)})
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
