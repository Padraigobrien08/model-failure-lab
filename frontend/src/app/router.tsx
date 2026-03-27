import { useOutletContext } from "react-router-dom";

import type {
  ArtifactIndex,
  FailureDomainKey,
  FinalRobustnessBundle,
  WorkbenchSelection,
} from "@/lib/manifest/types";

export type NavigationItem = {
  label: string;
  path: string;
  description: string;
};

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    label: "Verdict",
    path: "/",
    description: "Starting point for the trace-first scaffold",
  },
  {
    label: "Lane",
    path: "/lane/:laneId",
    description: "Focused lane route for one trace branch",
  },
  {
    label: "Method",
    path: "/lane/:laneId/:methodId",
    description: "Method drilldown inside a selected lane",
  },
  {
    label: "Run",
    path: "/run/:runId",
    description: "Single-run trace route",
  },
  {
    label: "Artifact",
    path: "/debug/raw/:entityId",
    description: "Raw debug route for a trace entity",
  },
];

export type AppRouteContext = {
  index: ArtifactIndex | null;
  isLoading: boolean;
  error: string | null;
  includeExploratory: boolean;
  setIncludeExploratory: (value: boolean) => void;
  manifestPath: string;
  finalRobustnessBundle: FinalRobustnessBundle | null;
  finalRobustnessBundleError: string | null;
  isFinalRobustnessBundleLoading: boolean;
  selection: WorkbenchSelection;
  setSelection: (patch: Partial<WorkbenchSelection>) => void;
  selectedVerdict: string | null;
  setSelectedVerdict: (value: string | null) => void;
  selectedLane: string | null;
  setSelectedLane: (value: string | null) => void;
  selectedMethod: string | null;
  setSelectedMethod: (value: string | null) => void;
  selectedDomain: FailureDomainKey | null;
  setSelectedDomain: (value: FailureDomainKey | null) => void;
  selectedRunId: string | null;
  setSelectedRunId: (value: string | null) => void;
  selectedArtifact: string | null;
  setSelectedArtifact: (value: string | null) => void;
  isEvidenceDrawerOpen: boolean;
  openEvidenceDrawer: (runId: string) => void;
  closeEvidenceDrawer: () => void;
};

export function useAppRouteContext() {
  return useOutletContext<AppRouteContext>();
}
