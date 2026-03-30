import { startTransition, useEffect, useMemo, useState } from "react";
import { BrowserRouter, MemoryRouter, Navigate, Route, Routes } from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { ComparisonsPage } from "@/app/routes/ComparisonsPage";
import { RunsPage } from "@/app/routes/RunsPage";
import { TraceShell } from "@/components/layout/TraceShell";
import {
  buildIncompatibleArtifactOverview,
  loadArtifactOverview,
} from "@/lib/artifacts/load";
import type { ArtifactShellState } from "@/lib/artifacts/types";
import type { ArtifactIndex, FinalRobustnessBundle } from "@/lib/manifest/types";
import type { FailureDomainKey, WorkbenchSelection } from "@/lib/manifest/types";

type AppProps = {
  manifestPath?: string;
  initialIndex?: ArtifactIndex | null;
  initialFinalRobustnessBundle?: FinalRobustnessBundle | null;
  initialIncludeExploratory?: boolean;
  initialArtifactState?: ArtifactShellState;
  useMemoryRouter?: boolean;
  initialEntries?: string[];
};

const DEFAULT_SELECTION: WorkbenchSelection = {
  scope: "official",
  verdict: null,
  lane: null,
  method: null,
  run: null,
  artifact: null,
  domain: null,
};

const noop = () => {};

function AppFrame({ initialArtifactState }: Pick<AppProps, "initialArtifactState">) {
  const [artifactState, setArtifactState] = useState<ArtifactShellState>(
    initialArtifactState ?? {
      status: "loading",
      overview: null,
    },
  );
  const [selection, setSelection] = useState<WorkbenchSelection>(DEFAULT_SELECTION);
  const [selectedVerdict, setSelectedVerdict] = useState<string | null>(null);
  const [selectedLane, setSelectedLane] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<FailureDomainKey | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);

  const refreshArtifacts = useMemo(
    () => () => {
      if (initialArtifactState) {
        startTransition(() => {
          setArtifactState(initialArtifactState);
        });
        return;
      }

      startTransition(() => {
        setArtifactState({ status: "loading", overview: null });
      });

      void loadArtifactOverview()
        .then((overview) => {
          startTransition(() => {
            setArtifactState({
              status: overview.status,
              overview,
            });
          });
        })
        .catch((error: unknown) => {
          const message =
            error instanceof Error ? error.message : "Failed to load artifact overview";
          startTransition(() => {
            setArtifactState({
              status: "incompatible",
              overview: buildIncompatibleArtifactOverview(message),
            });
          });
        });
    },
    [initialArtifactState],
  );

  useEffect(() => {
    refreshArtifacts();
  }, [refreshArtifacts]);

  const routeContext = useMemo<AppRouteContext>(
    () => ({
      artifactState,
      artifactOverview: artifactState.overview,
      reloadArtifacts: refreshArtifacts,
      index: null,
      isLoading: false,
      error: null,
      includeExploratory: false,
      setIncludeExploratory: noop,
      manifestPath: "legacy manifest path disabled for the main app shell",
      finalRobustnessBundle: null,
      finalRobustnessBundleError: null,
      isFinalRobustnessBundleLoading: false,
      selection,
      setSelection: (patch) => {
        setSelection((current) => ({ ...current, ...patch }));
      },
      selectedVerdict,
      setSelectedVerdict,
      selectedLane,
      setSelectedLane,
      selectedMethod,
      setSelectedMethod,
      selectedDomain,
      setSelectedDomain,
      selectedRunId,
      setSelectedRunId,
      selectedArtifact,
      setSelectedArtifact,
      isEvidenceDrawerOpen: false,
      openEvidenceDrawer: noop,
      closeEvidenceDrawer: noop,
    }),
    [
      artifactState,
      refreshArtifacts,
      selectedArtifact,
      selectedDomain,
      selectedLane,
      selectedMethod,
      selectedRunId,
      selectedVerdict,
      selection,
    ],
  );

  return (
    <Routes>
      <Route element={<TraceShell routeContext={routeContext} />}>
        <Route path="/" element={<RunsPage />} />
        <Route path="/runs" element={<Navigate to="/" replace />} />
        <Route path="/comparisons" element={<ComparisonsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export function App({
  useMemoryRouter = false,
  initialEntries = ["/"],
  initialArtifactState,
}: AppProps) {
  const appFrame = <AppFrame initialArtifactState={initialArtifactState} />;

  if (useMemoryRouter) {
    return <MemoryRouter initialEntries={initialEntries}>{appFrame}</MemoryRouter>;
  }

  return <BrowserRouter>{appFrame}</BrowserRouter>;
}
