import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FailureDomainPanel } from "@/components/failure/FailureDomainPanel";
import type { FailureDomainKey, FailureDomainModel } from "@/lib/manifest/types";

type FailureExplorerTabsProps = {
  domains: FailureDomainModel[];
  selectedDomain: FailureDomainKey;
  selectedMethod: string | null;
  onSelectDomain: (domain: FailureDomainKey) => void;
  onSelectMethod: (methodName: string) => void;
};

export function FailureExplorerTabs({
  domains,
  selectedDomain,
  selectedMethod,
  onSelectDomain,
  onSelectMethod,
}: FailureExplorerTabsProps) {
  return (
    <Tabs value={selectedDomain} onValueChange={(value) => onSelectDomain(value as FailureDomainKey)}>
      <TabsList>
        {domains.map((domain) => (
          <TabsTrigger key={domain.domain} value={domain.domain}>
            {domain.label}
          </TabsTrigger>
        ))}
      </TabsList>

      {domains.map((domain) => (
        <TabsContent key={domain.domain} value={domain.domain} className="mt-6">
          <div className="space-y-6">
            <div className="space-y-2">
              <h3 className="text-[2rem] font-semibold tracking-[-0.05em] text-foreground">
                {domain.label}
              </h3>
              <p className="max-w-3xl text-base leading-7 text-muted-foreground">
                {domain.description}
              </p>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              {domain.items.map((item) => (
                <FailureDomainPanel
                  key={`${domain.domain}-${item.methodName}`}
                  domain={domain.domain}
                  item={item}
                  isSelected={selectedMethod === item.methodName}
                  onSelectMethod={onSelectMethod}
                  actions={domain.actions}
                />
              ))}
            </div>
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
