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
    label: "Verdicts",
    path: "/",
    description: "Final verdict, supporting lanes, and first evidence path",
  },
  {
    label: "Lanes",
    path: "/lanes",
    description: "Calibration-versus-robustness workspace and method ordering",
  },
  {
    label: "Runs",
    path: "/runs",
    description: "Run lineage, seeded detail, and artifact handoff",
  },
  {
    label: "Evidence",
    path: "/evidence",
    description: "Reports, eval bundles, and manifest-backed artifact paths",
  },
  {
    label: "Manifest",
    path: "/manifest",
    description: "Contract provenance, visibility flags, and entity relationships",
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
