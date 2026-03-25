import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FailureDomainPanel } from "@/components/failure/FailureDomainPanel";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import type { FailureDomainKey, FailureDomainModel } from "@/lib/manifest/types";

type FailureExplorerTabsProps = {
  domains: FailureDomainModel[];
  selectedDomain: FailureDomainKey;
  selectedMethod: string | null;
  onSelectDomain: (domain: FailureDomainKey) => void;
  onSelectMethod: (methodName: string) => void;
  onInspectMethod: (methodName: string) => void;
};

export function FailureExplorerTabs({
  domains,
  selectedDomain,
  selectedMethod,
  onSelectDomain,
  onSelectMethod,
  onInspectMethod,
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
          <WorkbenchSection
            eyebrow="Domain view"
            title={domain.label}
            description={domain.description}
          >
            <div className="grid gap-4 xl:grid-cols-2">
              {domain.items.map((item) => (
                <FailureDomainPanel
                  key={`${domain.domain}-${item.methodName}`}
                  domain={domain.domain}
                  item={item}
                  isSelected={selectedMethod === item.methodName}
                  onSelectMethod={onSelectMethod}
                  onInspectMethod={onInspectMethod}
                  actions={domain.actions}
                />
              ))}
            </div>
          </WorkbenchSection>
        </TabsContent>
      ))}
    </Tabs>
  );
}
