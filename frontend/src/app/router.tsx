import { useOutletContext } from "react-router-dom";

import type {
  ArtifactOverview,
  ArtifactShellState,
  ComparisonInventoryState,
  RunInventoryState,
} from "@/lib/artifacts/types";
import type {
  DatasetFamiliesResponse,
  GateResponse,
} from "@/lib/artifacts/extended";

type RemoteState<T> =
  | { status: "idle" | "loading"; data: null; message: null }
  | { status: "ready"; data: T; message: null }
  | { status: "incompatible"; data: null; message: string };

export type DatasetFamiliesState = RemoteState<DatasetFamiliesResponse>;
export type GateState = RemoteState<GateResponse>;

export type NavigationItem = {
  label: string;
  path: string;
};

export const NAVIGATION_ITEMS: NavigationItem[] = [
  { label: "Runs", path: "/" },
  { label: "Comparisons", path: "/comparisons" },
  { label: "Evidence", path: "/evidence" },
  { label: "Datasets", path: "/datasets" },
];

export type AppRouteContext = {
  artifactState: ArtifactShellState;
  artifactOverview: ArtifactOverview | null;
  reloadArtifacts: () => void;
  runInventoryState: RunInventoryState;
  reloadRunInventory: () => void;
  comparisonInventoryState: ComparisonInventoryState;
  reloadComparisonInventory: () => void;
  datasetFamiliesState: DatasetFamiliesState;
  reloadDatasetFamilies: () => void;
  gateState: GateState;
  reloadGate: () => void;
};

export function useAppRouteContext() {
  return useOutletContext<AppRouteContext>();
}
