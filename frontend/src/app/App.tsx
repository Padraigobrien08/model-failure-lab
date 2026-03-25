import { useEffect, useState } from "react";
import { BrowserRouter, MemoryRouter, Route, Routes } from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { ComparisonsPage } from "@/app/routes/ComparisonsPage";
import { EvidencePage } from "@/app/routes/EvidencePage";
import { FailureExplorerPage } from "@/app/routes/FailureExplorerPage";
import { RunsPage } from "@/app/routes/RunsPage";
import { AppShell } from "@/components/layout/AppShell";
import { loadArtifactIndex, DEFAULT_MANIFEST_PATH } from "@/lib/manifest/load";
import { loadFinalRobustnessBundle } from "@/lib/manifest/reportData";
import type {
  ArtifactIndex,
  FailureDomainKey,
  FinalRobustnessBundle,
  RunEntity,
} from "@/lib/manifest/types";
import { OverviewPage } from "@/app/routes/OverviewPage";

type AppProps = {
  manifestPath?: string;
  initialIndex?: ArtifactIndex | null;
  initialFinalRobustnessBundle?: FinalRobustnessBundle | null;
  initialIncludeExploratory?: boolean;
  useMemoryRouter?: boolean;
  initialEntries?: string[];
};

type AppFrameProps = {
  manifestPath: string;
  initialIndex?: ArtifactIndex | null;
  initialFinalRobustnessBundle?: FinalRobustnessBundle | null;
  initialIncludeExploratory: boolean;
};

function AppFrame({
  manifestPath,
  initialIndex = null,
  initialFinalRobustnessBundle = null,
  initialIncludeExploratory,
}: AppFrameProps) {
  const [index, setIndex] = useState<ArtifactIndex | null>(initialIndex);
  const [isLoading, setIsLoading] = useState<boolean>(initialIndex === null);
  const [error, setError] = useState<string | null>(null);
  const [includeExploratory, setIncludeExploratory] = useState(initialIncludeExploratory);
  const [finalRobustnessBundle, setFinalRobustnessBundle] =
    useState<FinalRobustnessBundle | null>(initialFinalRobustnessBundle);
  const [isFinalRobustnessBundleLoading, setIsFinalRobustnessBundleLoading] = useState(
    initialFinalRobustnessBundle === null,
  );
  const [finalRobustnessBundleError, setFinalRobustnessBundleError] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<FailureDomainKey | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState(false);

  useEffect(() => {
    if (initialIndex !== null) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    loadArtifactIndex(manifestPath)
      .then((payload) => {
        if (!cancelled) {
          setIndex(payload);
          setError(null);
        }
      })
      .catch((loadError: Error) => {
        if (!cancelled) {
          setError(loadError.message);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [initialIndex, manifestPath]);

  useEffect(() => {
    if (index === null) {
      return;
    }

    if (initialFinalRobustnessBundle !== null) {
      setFinalRobustnessBundle(initialFinalRobustnessBundle);
      setIsFinalRobustnessBundleLoading(false);
      setFinalRobustnessBundleError(null);
      return;
    }

    let cancelled = false;
    setIsFinalRobustnessBundleLoading(true);
    loadFinalRobustnessBundle(index)
      .then((bundle) => {
        if (!cancelled) {
          setFinalRobustnessBundle(bundle);
          setFinalRobustnessBundleError(null);
        }
      })
      .catch((loadError: Error) => {
        if (!cancelled) {
          setFinalRobustnessBundleError(loadError.message);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsFinalRobustnessBundleLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [index, initialFinalRobustnessBundle]);

  useEffect(() => {
    if (index === null || includeExploratory || selectedRunId === null) {
      return;
    }

    const selectedRun = (index.entities.runs as RunEntity[]).find(
      (run) => run.id === selectedRunId || run.run_id === selectedRunId,
    );
    if (selectedRun?.default_visible === false) {
      setSelectedRunId(null);
      setIsEvidenceDrawerOpen(false);
    }
  }, [includeExploratory, index, selectedRunId]);

  function openEvidenceDrawer(runId: string) {
    setSelectedRunId(runId);
    setIsEvidenceDrawerOpen(true);
  }

  function closeEvidenceDrawer() {
    setIsEvidenceDrawerOpen(false);
  }

  const routeContext: AppRouteContext = {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory,
    manifestPath,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selectedMethod,
    setSelectedMethod,
    selectedDomain,
    setSelectedDomain,
    selectedRunId,
    setSelectedRunId,
    isEvidenceDrawerOpen,
    openEvidenceDrawer,
    closeEvidenceDrawer,
  };

  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppShell
            includeExploratory={includeExploratory}
            onToggleExploratory={setIncludeExploratory}
            manifestPath={manifestPath}
            routeContext={routeContext}
          />
        }
      >
        <Route index element={<OverviewPage />} />
        <Route path="comparisons" element={<ComparisonsPage />} />
        <Route path="failure-explorer" element={<FailureExplorerPage />} />
        <Route path="runs" element={<RunsPage />} />
        <Route path="evidence" element={<EvidencePage />} />
      </Route>
    </Routes>
  );
}

export function App({
  manifestPath = DEFAULT_MANIFEST_PATH,
  initialIndex = null,
  initialFinalRobustnessBundle = null,
  initialIncludeExploratory = false,
  useMemoryRouter = false,
  initialEntries = ["/"],
}: AppProps) {
  const appFrame = (
    <AppFrame
      manifestPath={manifestPath}
      initialIndex={initialIndex}
      initialFinalRobustnessBundle={initialFinalRobustnessBundle}
      initialIncludeExploratory={initialIncludeExploratory}
    />
  );

  if (useMemoryRouter) {
    return <MemoryRouter initialEntries={initialEntries}>{appFrame}</MemoryRouter>;
  }

  return <BrowserRouter>{appFrame}</BrowserRouter>;
}
