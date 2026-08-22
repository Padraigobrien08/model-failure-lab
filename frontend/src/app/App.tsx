import { startTransition, useEffect, useMemo, useState } from "react";
import { BrowserRouter, MemoryRouter, Navigate, Route, Routes } from "react-router-dom";

import type { AppRouteContext, DatasetFamiliesState, GateState } from "@/app/router";
import { ComparisonsPage } from "@/app/routes/ComparisonsPage";
import { ComparisonDetailPage } from "@/app/routes/ComparisonDetailPage";
import { DatasetFamilyPage } from "@/app/routes/DatasetFamilyPage";
import { DatasetsPage } from "@/app/routes/DatasetsPage";
import { EvidencePage } from "@/app/routes/EvidencePage";
import { ExplorerPage } from "@/app/routes/ExplorerPage";
import { GatePage } from "@/app/routes/GatePage";
import { RunDetailPage } from "@/app/routes/RunDetailPage";
import { RunsPage } from "@/app/routes/RunsPage";
import { ConsoleShell } from "@/components/layout/ConsoleShell";
import { loadDatasetFamilies, loadGate } from "@/lib/artifacts/extended";
import {
  buildIncompatibleArtifactOverview,
  loadArtifactOverview,
  loadComparisonInventory,
  loadRunInventory,
} from "@/lib/artifacts/load";
import type {
  ArtifactShellState,
  ComparisonInventory,
  ComparisonInventoryState,
  RunInventory,
  RunInventoryState,
} from "@/lib/artifacts/types";

type AppProps = {
  initialArtifactState?: ArtifactShellState;
  initialRunInventoryState?: RunInventoryState;
  initialComparisonInventoryState?: ComparisonInventoryState;
  initialDatasetFamiliesState?: DatasetFamiliesState;
  initialGateState?: GateState;
  useMemoryRouter?: boolean;
  initialEntries?: string[];
};

const ROUTER_FUTURE_FLAGS = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

const IDLE_REMOTE = { status: "idle", data: null, message: null } as const;

type RemoteState<T> =
  | { status: "idle" | "loading"; data: null; message: null }
  | { status: "ready"; data: T; message: null }
  | { status: "incompatible"; data: null; message: string };

function useRemote<T>(
  enabled: boolean,
  initial: RemoteState<T> | undefined,
  load: () => Promise<T>,
): [RemoteState<T>, () => void] {
  type State = RemoteState<T>;
  const [state, setState] = useState<State>(initial ?? IDLE_REMOTE);

  const refresh = useMemo(
    () => () => {
      if (initial) {
        startTransition(() => setState(initial as State));
        return;
      }
      if (!enabled) {
        startTransition(() => setState(IDLE_REMOTE));
        return;
      }
      startTransition(() => setState({ status: "loading", data: null, message: null }));
      void load()
        .then((data) => {
          startTransition(() => setState({ status: "ready", data, message: null }));
        })
        .catch((error: unknown) => {
          const message = error instanceof Error ? error.message : "request failed";
          startTransition(() => setState({ status: "incompatible", data: null, message }));
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [enabled, initial],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  return [state, refresh];
}

function AppFrame({
  initialArtifactState,
  initialRunInventoryState,
  initialComparisonInventoryState,
  initialDatasetFamiliesState,
  initialGateState,
}: Omit<AppProps, "useMemoryRouter" | "initialEntries">) {
  const [artifactState, setArtifactState] = useState<ArtifactShellState>(
    initialArtifactState ?? { status: "loading", overview: null },
  );

  const refreshArtifacts = useMemo(
    () => () => {
      if (initialArtifactState) {
        startTransition(() => setArtifactState(initialArtifactState));
        return;
      }
      startTransition(() => setArtifactState({ status: "loading", overview: null }));
      void loadArtifactOverview()
        .then((overview) => {
          startTransition(() => setArtifactState({ status: overview.status, overview }));
        })
        .catch((error: unknown) => {
          const message =
            error instanceof Error ? error.message : "Failed to load artifact overview";
          startTransition(() =>
            setArtifactState({
              status: "incompatible",
              overview: buildIncompatibleArtifactOverview(message),
            }),
          );
        });
    },
    [initialArtifactState],
  );

  useEffect(() => {
    refreshArtifacts();
  }, [refreshArtifacts]);

  const ready = artifactState.status === "ready";

  const initialRunRemote = useMemo<RemoteState<RunInventory> | undefined>(() => {
    if (!initialRunInventoryState) return undefined;
    if (initialRunInventoryState.status === "ready") {
      return { status: "ready", data: initialRunInventoryState.inventory, message: null };
    }
    if (initialRunInventoryState.status === "incompatible") {
      return {
        status: "incompatible",
        data: null,
        message: initialRunInventoryState.message,
      };
    }
    return { status: initialRunInventoryState.status, data: null, message: null };
  }, [initialRunInventoryState]);

  const initialComparisonRemote = useMemo<
    RemoteState<ComparisonInventory> | undefined
  >(() => {
    if (!initialComparisonInventoryState) return undefined;
    if (initialComparisonInventoryState.status === "ready") {
      return {
        status: "ready",
        data: initialComparisonInventoryState.inventory,
        message: null,
      };
    }
    if (initialComparisonInventoryState.status === "incompatible") {
      return {
        status: "incompatible",
        data: null,
        message: initialComparisonInventoryState.message,
      };
    }
    return { status: initialComparisonInventoryState.status, data: null, message: null };
  }, [initialComparisonInventoryState]);

  const [runInventoryRemote, reloadRunInventory] = useRemote(
    ready,
    initialRunRemote,
    loadRunInventory,
  );
  const [comparisonInventoryRemote, reloadComparisonInventory] = useRemote(
    ready,
    initialComparisonRemote,
    loadComparisonInventory,
  );
  const [datasetFamiliesState, reloadDatasetFamilies] = useRemote(
    ready,
    initialDatasetFamiliesState,
    loadDatasetFamilies,
  );
  const [gateState, reloadGate] = useRemote(ready, initialGateState, loadGate);

  const runInventoryState = useMemo<RunInventoryState>(() => {
    if (runInventoryRemote.status === "ready") {
      return { status: "ready", inventory: runInventoryRemote.data, message: null };
    }
    if (runInventoryRemote.status === "incompatible") {
      return { status: "incompatible", inventory: null, message: runInventoryRemote.message };
    }
    return { status: runInventoryRemote.status, inventory: null, message: null };
  }, [runInventoryRemote]);

  const comparisonInventoryState = useMemo<ComparisonInventoryState>(() => {
    if (comparisonInventoryRemote.status === "ready") {
      return { status: "ready", inventory: comparisonInventoryRemote.data, message: null };
    }
    if (comparisonInventoryRemote.status === "incompatible") {
      return {
        status: "incompatible",
        inventory: null,
        message: comparisonInventoryRemote.message,
      };
    }
    return { status: comparisonInventoryRemote.status, inventory: null, message: null };
  }, [comparisonInventoryRemote]);

  const routeContext = useMemo<AppRouteContext>(
    () => ({
      artifactState,
      artifactOverview: artifactState.overview,
      reloadArtifacts: refreshArtifacts,
      runInventoryState,
      reloadRunInventory,
      comparisonInventoryState,
      reloadComparisonInventory,
      datasetFamiliesState: datasetFamiliesState as DatasetFamiliesState,
      reloadDatasetFamilies,
      gateState: gateState as GateState,
      reloadGate,
    }),
    [
      artifactState,
      comparisonInventoryState,
      datasetFamiliesState,
      gateState,
      refreshArtifacts,
      reloadComparisonInventory,
      reloadDatasetFamilies,
      reloadGate,
      reloadRunInventory,
      runInventoryState,
    ],
  );

  return (
    <Routes>
      <Route element={<ConsoleShell routeContext={routeContext} />}>
        <Route path="/" element={<RunsPage />} />
        <Route path="/runs" element={<Navigate to="/" replace />} />
        <Route path="/runs/:runId" element={<RunDetailPage />} />
        <Route path="/comparisons" element={<ComparisonsPage />} />
        <Route path="/comparisons/:reportId" element={<ComparisonDetailPage />} />
        <Route path="/comparisons/:reportId/evidence" element={<EvidencePage />} />
        <Route path="/evidence" element={<ExplorerPage />} />
        <Route path="/datasets" element={<DatasetsPage />} />
        <Route path="/datasets/:familyId" element={<DatasetFamilyPage />} />
        <Route path="/gate" element={<GatePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export function App({ useMemoryRouter = false, initialEntries = ["/"], ...initialStates }: AppProps) {
  const appFrame = <AppFrame {...initialStates} />;

  if (useMemoryRouter) {
    return (
      <MemoryRouter future={ROUTER_FUTURE_FLAGS} initialEntries={initialEntries}>
        {appFrame}
      </MemoryRouter>
    );
  }

  return <BrowserRouter future={ROUTER_FUTURE_FLAGS}>{appFrame}</BrowserRouter>;
}
