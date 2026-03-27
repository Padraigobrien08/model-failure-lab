import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { RawDebugPayloadTab, RawDebugTabKey } from "@/lib/rawDebugRoute";

type RawEntityTabsProps = {
  tabs: RawDebugPayloadTab[];
};

export function RawEntityTabs({ tabs }: RawEntityTabsProps) {
  const defaultTab = tabs[0]?.key ?? "raw_json";
  const [activeTab, setActiveTab] = useState<RawDebugTabKey>(defaultTab);
  const [copiedTab, setCopiedTab] = useState<string | null>(null);

  useEffect(() => {
    setActiveTab(defaultTab);
    setCopiedTab(null);
  }, [defaultTab, tabs]);

  const activePayload = useMemo(
    () => tabs.find((tab) => tab.key === activeTab) ?? tabs[0],
    [activeTab, tabs],
  );

  async function handleCopy(content: string, key: string) {
    const clipboard = globalThis.navigator?.clipboard;

    if (clipboard && typeof clipboard.writeText === "function") {
      await clipboard.writeText(content);
    }

    setCopiedTab(key);
  }

  return (
    <section className="space-y-4" aria-label="Raw entity tabs">
      <Tabs
        className="space-y-4"
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as RawDebugTabKey)}
      >
        <TabsList>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.key} value={tab.key}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {tabs.map((tab) => (
          <TabsContent key={tab.key} className="space-y-3" value={tab.key}>
            <div className="flex items-center justify-between gap-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {tab.label}
              </p>
              <Button
                size="sm"
                type="button"
                variant="outline"
                onClick={() => handleCopy(tab.content, tab.key)}
              >
                {copiedTab === tab.key ? `Copied ${tab.label}` : tab.copyLabel}
              </Button>
            </div>
            <pre className="overflow-x-auto border border-border/70 bg-muted/10 p-4 font-mono text-xs leading-6 text-foreground">
              <code>{tab.content}</code>
            </pre>
          </TabsContent>
        ))}
      </Tabs>

      {activePayload ? (
        <p className="text-xs text-muted-foreground">
          Active payload: <span className="font-medium text-foreground">{activePayload.label}</span>
        </p>
      ) : null}
    </section>
  );
}
