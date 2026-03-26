import { useMemo } from "react";

import { useAppRouteContext } from "@/app/router";
import { RankedComparisonCanvas } from "@/components/comparisons/RankedComparisonCanvas";
import { FailureExplorerTabs } from "@/components/failure/FailureExplorerTabs";
import { ScopeStateBanner } from "@/components/layout/ScopeStateBanner";
import { WorkbenchHeader } from "@/components/layout/WorkbenchHeader";
import { WorkbenchSection } from "@/components/layout/WorkbenchSection";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  buildComparisonCards,
  buildFailureDomainModels,
  getRepresentativeRunIdForMethod,
} from "@/lib/manifest/selectors";

const LANE_OPTIONS = [
  {
    key: "robustness",
    label: "Robustness",
    description: "Worst-group, OOD, and ID tradeoffs that keep the final verdict mixed.",
  },
  {
    key: "calibration",
    label: "Calibration",
    description: "ECE and Brier shifts that explain why temperature scaling remains the stable win.",
  },
] as const;

export function ComparisonsPage() {
  const {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selection,
    selectedLane,
    setSelectedLane,
    selectedMethod,
    selectedDomain,
    setSelectedMethod,
    setSelectedDomain,
    openEvidenceDrawer,
  } = useAppRouteContext();

  if (isLoading || isFinalRobustnessBundleLoading) {
    return (
      <section className="space-y-4">
        <Badge tone="accent">Lanes</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Loading lane workspace.
        </h2>
      </section>
    );
  }

  if (error || finalRobustnessBundleError || index === null || finalRobustnessBundle === null) {
    return (
      <section className="space-y-4">
        <Badge tone="default">Lanes</Badge>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
          The lane workspace is unavailable.
        </h2>
        <Card className="bg-background/60">
          <CardContent className="px-6 py-6 font-mono text-sm text-foreground">
            {finalRobustnessBundleError ?? error ?? "Missing saved lane payload."}
          </CardContent>
        </Card>
      </section>
    );
  }

  const manifestIndex = index;
  const comparisonCards = buildComparisonCards(index, finalRobustnessBundle, includeExploratory);
  const failureDomains = buildFailureDomainModels(index, finalRobustnessBundle, includeExploratory);
  const activeLane = selectedLane ?? "robustness";
  const activeDomain =
    selectedDomain ?? (activeLane === "calibration" ? "calibration" : "worst_group");

  function buildDomainTracePath(domain: "worst_group" | "ood" | "id" | "calibration") {
    const searchParams = new URLSearchParams();

    if (selection.scope === "exploratory") {
      searchParams.set("scope", "exploratory");
    }
    if (selection.verdict) {
      searchParams.set("verdict", selection.verdict);
    }
    if (selection.method) {
      searchParams.set("method", selection.method);
    }
    if (selection.run) {
      searchParams.set("run", selection.run);
    }
    if (selection.artifact) {
      searchParams.set("artifact", selection.artifact);
    }

    searchParams.set("lane", domain === "calibration" ? "calibration" : "robustness");
    searchParams.set("domain", domain);

    return `/failure-explorer?${searchParams.toString()}`;
  }

  const orderedDomains = useMemo(() => {
    if (activeLane === "calibration") {
      return [
        ...failureDomains.filter((domain) => domain.domain === "calibration"),
        ...failureDomains.filter((domain) => domain.domain !== "calibration"),
      ];
    }

    return [
      ...failureDomains.filter((domain) => domain.domain !== "calibration"),
      ...failureDomains.filter((domain) => domain.domain === "calibration"),
    ];
  }, [activeLane, failureDomains]);

  function handleSelectLane(lane: "robustness" | "calibration") {
    setSelectedLane(lane);
    setSelectedDomain(lane === "calibration" ? "calibration" : "worst_group");
  }

  function handleSelectMethod(methodName: string) {
    setSelectedMethod(methodName);
  }

  function handleInspectMethod(methodName: string) {
    handleSelectMethod(methodName);

    const runId = getRepresentativeRunIdForMethod(manifestIndex, methodName, true);
    if (runId) {
      openEvidenceDrawer(runId);
    }
  }

  const laneMeta =
    LANE_OPTIONS.find((option) => option.key === activeLane) ?? LANE_OPTIONS[0];

  return (
    <section className="space-y-8">
      <WorkbenchHeader
        meta={
          <>
            <Badge tone="accent">Lanes</Badge>
            {includeExploratory ? <Badge tone="exploratory">Exploratory scope active</Badge> : null}
            <Badge tone="default">{laneMeta.label}</Badge>
          </>
        }
        title={`${laneMeta.label} lane workspace.`}
        description={laneMeta.description}
        supportingText="The lane route absorbs the old comparison and failure-explorer posture into one lineage-aware workspace."
        aside={
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active lane
              </p>
              <p className="mt-1 text-foreground">{laneMeta.label}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                Active domain
              </p>
              <p className="mt-1 text-foreground">{activeDomain}</p>
            </div>
          </div>
        }
      />

      <ScopeStateBanner
        includeExploratory={includeExploratory}
        onChange={setIncludeExploratory}
      />

      <WorkbenchSection
        eyebrow="Lane selector"
        title="Choose the lane that explains the verdict"
        description="Switch between robustness and calibration without leaving the route. Method focus and domain focus stay in the same workspace."
      >
        <div className="flex flex-wrap gap-3">
          {LANE_OPTIONS.map((lane) => (
            <Button
              key={lane.key}
              variant={activeLane === lane.key ? "default" : "outline"}
              onClick={() => handleSelectLane(lane.key)}
            >
              {lane.label}
            </Button>
          ))}
        </div>
      </WorkbenchSection>

      <RankedComparisonCanvas
        items={comparisonCards}
        domains={orderedDomains}
        selectedMethod={selectedMethod}
        selectedDomain={activeDomain}
        onSelectMethod={handleSelectMethod}
        onSelectDomain={setSelectedDomain}
        onInspectMethod={handleInspectMethod}
        buildDomainTracePath={buildDomainTracePath}
      />

      <FailureExplorerTabs
        domains={orderedDomains}
        selectedDomain={activeDomain}
        selectedMethod={selectedMethod}
        onSelectDomain={setSelectedDomain}
        onSelectMethod={handleSelectMethod}
        onInspectMethod={handleInspectMethod}
      />
    </section>
  );
}
