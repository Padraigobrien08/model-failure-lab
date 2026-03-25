import { useOutletContext } from "react-router-dom";

import type {
  ArtifactIndex,
  FailureDomainKey,
  FinalRobustnessBundle,
} from "@/lib/manifest/types";

export type NavigationItem = {
  label: string;
  path: string;
  description: string;
};

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    label: "Overview",
    path: "/",
    description: "System index for the final verdict and active scope",
  },
  {
    label: "Comparisons",
    path: "/comparisons",
    description: "Rank lanes and inspect why the order holds",
  },
  {
    label: "Failure Explorer",
    path: "/failure-explorer",
    description: "Separate subgroup, OOD, ID, and calibration stories",
  },
  {
    label: "Runs",
    path: "/runs",
    description: "Seeded run lineage and detailed inspection",
  },
  {
    label: "Evidence",
    path: "/evidence",
    description: "Reports, eval bundles, and manifest-backed paths",
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
  selectedMethod: string | null;
  setSelectedMethod: (value: string | null) => void;
  selectedDomain: FailureDomainKey | null;
  setSelectedDomain: (value: FailureDomainKey | null) => void;
  selectedRunId: string | null;
  setSelectedRunId: (value: string | null) => void;
  isEvidenceDrawerOpen: boolean;
  openEvidenceDrawer: (runId: string) => void;
  closeEvidenceDrawer: () => void;
};

export function useAppRouteContext() {
  return useOutletContext<AppRouteContext>();
}
