import { useOutletContext } from "react-router-dom";

import type {
  ArtifactOverview,
  ArtifactShellState,
  RunInventoryState,
} from "@/lib/artifacts/types";
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
    label: "Runs",
    path: "/",
    description: "Saved run artifacts from the local engine contract",
  },
  {
    label: "Comparisons",
    path: "/comparisons",
    description: "Baseline-to-candidate comparison artifacts",
  },
];

export type AppRouteContext = {
  artifactState: ArtifactShellState;
  artifactOverview: ArtifactOverview | null;
  reloadArtifacts: () => void;
  runInventoryState: RunInventoryState;
  reloadRunInventory: () => void;
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
