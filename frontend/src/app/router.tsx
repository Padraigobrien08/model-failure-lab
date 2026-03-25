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
    description: "Final verdicts and official evidence launchpad",
  },
  {
    label: "Comparisons",
    path: "/comparisons",
    description: "Method-to-method debugging",
  },
  {
    label: "Failure Explorer",
    path: "/failure-explorer",
    description: "Subgroup, ID/OOD, and calibration entrypoints",
  },
  {
    label: "Runs",
    path: "/runs",
    description: "Run-level lineage and seed context",
  },
  {
    label: "Evidence",
    path: "/evidence",
    description: "Raw reports, eval bundles, and metadata paths",
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
};

export function useAppRouteContext() {
  return useOutletContext<AppRouteContext>();
}
