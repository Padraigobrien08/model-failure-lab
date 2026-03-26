import { useEffect, useMemo, useState } from "react";
import {
  BrowserRouter,
  MemoryRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useSearchParams,
} from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { ComparisonsPage } from "@/app/routes/ComparisonsPage";
import { EvidencePage } from "@/app/routes/EvidencePage";
import { FailureExplorerPage } from "@/app/routes/FailureExplorerPage";
import { ManifestPage } from "@/app/routes/ManifestPage";
import { RunsPage } from "@/app/routes/RunsPage";
import { AppShell } from "@/components/layout/AppShell";
import { loadArtifactIndex, DEFAULT_MANIFEST_PATH } from "@/lib/manifest/load";
import { loadFinalRobustnessBundle } from "@/lib/manifest/reportData";
import type {
  ArtifactIndex,
  FailureDomainKey,
  FinalRobustnessBundle,
  RunEntity,
  WorkbenchSelection,
} from "@/lib/manifest/types";
import { OverviewPage } from "@/app/routes/OverviewPage";
import { buildVerdictWorkspaceModel, getMethodLaneKey } from "@/lib/manifest/selectors";

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

const FAILURE_DOMAIN_KEYS: FailureDomainKey[] = ["worst_group", "ood", "id", "calibration"];

function isFailureDomainKey(value: string | null): value is FailureDomainKey {
  return value !== null && FAILURE_DOMAIN_KEYS.includes(value as FailureDomainKey);
}

function buildSelectionFromSearchParams(
  searchParams: URLSearchParams,
  initialIncludeExploratory: boolean,
): WorkbenchSelection {
  const scopeParam = searchParams.get("scope");
  const scope =
    scopeParam === "exploratory" || (!scopeParam && initialIncludeExploratory)
      ? "exploratory"
      : "official";
  const domainParam = searchParams.get("domain");

  return {
    scope,
    verdict: searchParams.get("verdict"),
    lane: searchParams.get("lane"),
    method: searchParams.get("method"),
    run: searchParams.get("run"),
    artifact: searchParams.get("artifact"),
    domain: isFailureDomainKey(domainParam) ? domainParam : null,
  };
}

function LegacyRouteRedirect({ to }: { to: string }) {
  const location = useLocation();

  return <Navigate replace to={`${to}${location.search}`} />;
}

function AppFrame({
  manifestPath,
  initialIndex = null,
  initialFinalRobustnessBundle = null,
  initialIncludeExploratory,
}: AppFrameProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [index, setIndex] = useState<ArtifactIndex | null>(initialIndex);
  const [isLoading, setIsLoading] = useState<boolean>(initialIndex === null);
  const [error, setError] = useState<string | null>(null);
  const [finalRobustnessBundle, setFinalRobustnessBundle] =
    useState<FinalRobustnessBundle | null>(initialFinalRobustnessBundle);
  const [isFinalRobustnessBundleLoading, setIsFinalRobustnessBundleLoading] = useState(
    initialFinalRobustnessBundle === null,
  );
  const [finalRobustnessBundleError, setFinalRobustnessBundleError] = useState<string | null>(null);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState(false);
  const selection = useMemo(
    () => buildSelectionFromSearchParams(searchParams, initialIncludeExploratory),
    [initialIncludeExploratory, searchParams],
  );
  const includeExploratory = selection.scope === "exploratory";

  function setSelection(patch: Partial<WorkbenchSelection>) {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);

      for (const [key, value] of Object.entries(patch)) {
        if (value === null || value === "" || value === undefined) {
          next.delete(key);
          continue;
        }

        next.set(key, String(value));
      }

      return next;
    });
  }

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
    if (index === null || includeExploratory) {
      return;
    }

    const selectedRun =
      selection.run === null
        ? null
        : (index.entities.runs as RunEntity[]).find(
            (run) => run.id === selection.run || run.run_id === selection.run,
          ) ?? null;
    const selectedArtifact =
      selection.artifact === null
        ? null
        : [
            ...index.entities.reports,
            ...index.entities.evaluations,
            ...index.entities.runs,
          ].find((entity) => entity.id === selection.artifact) ?? null;

    if (selectedRun?.default_visible === false || selectedArtifact?.default_visible === false) {
      setSelection({ run: null, artifact: null });
      setIsEvidenceDrawerOpen(false);
    }
  }, [includeExploratory, index, selection.artifact, selection.run]);

  useEffect(() => {
    if (index === null || finalRobustnessBundle === null) {
      return;
    }

    const defaults = buildVerdictWorkspaceModel(index, finalRobustnessBundle, includeExploratory);
    const patch: Partial<WorkbenchSelection> = {};

    if (!selection.verdict) {
      patch.verdict = defaults.finalVerdict;
    }

    if (!selection.lane) {
      patch.lane = defaults.dominantLaneKey;
    }

    if (Object.keys(patch).length > 0) {
      setSelection(patch);
    }
  }, [
    finalRobustnessBundle,
    includeExploratory,
    index,
    selection.lane,
    selection.verdict,
  ]);

  function openEvidenceDrawer(runId: string) {
    setSelection({ run: runId, artifact: null });
    setIsEvidenceDrawerOpen(true);
  }

  function closeEvidenceDrawer() {
    setIsEvidenceDrawerOpen(false);
    setSelection({ run: null, artifact: null });
  }

  const routeContext: AppRouteContext = {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory: (value: boolean) =>
      setSelection({ scope: value ? "exploratory" : "official" }),
    manifestPath,
    finalRobustnessBundle,
    finalRobustnessBundleError,
    isFinalRobustnessBundleLoading,
    selection,
    setSelection,
    selectedVerdict: selection.verdict,
    setSelectedVerdict: (value: string | null) =>
      setSelection({ verdict: value, lane: null, method: null, run: null, artifact: null }),
    selectedLane: selection.lane,
    setSelectedLane: (value: string | null) =>
      setSelection({
        lane: value,
        method: null,
        run: null,
        artifact: null,
        domain:
          value === "calibration"
            ? "calibration"
            : value === "robustness" && selection.domain === "calibration"
              ? "worst_group"
              : selection.domain,
      }),
    selectedMethod: selection.method,
    setSelectedMethod: (value: string | null) =>
      setSelection({
        method: value,
        lane: value ? getMethodLaneKey(value) : selection.lane,
        run: null,
        artifact: null,
      }),
    selectedDomain: selection.domain,
    setSelectedDomain: (value: FailureDomainKey | null) =>
      setSelection({
        domain: value,
        lane:
          value === "calibration"
            ? "calibration"
            : value === null
              ? selection.lane
              : "robustness",
      }),
    selectedRunId: selection.run,
    setSelectedRunId: (value: string | null) => setSelection({ run: value, artifact: null }),
    selectedArtifact: selection.artifact,
    setSelectedArtifact: (value: string | null) => setSelection({ artifact: value }),
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
            onToggleExploratory={(next) =>
              setSelection({ scope: next ? "exploratory" : "official" })
            }
            manifestPath={manifestPath}
            routeContext={routeContext}
          />
        }
      >
        <Route index element={<OverviewPage />} />
        <Route path="overview" element={<LegacyRouteRedirect to="/" />} />
        <Route path="lanes" element={<ComparisonsPage />} />
        <Route path="runs" element={<RunsPage />} />
        <Route path="evidence" element={<EvidencePage />} />
        <Route path="manifest" element={<ManifestPage />} />
        <Route path="comparisons" element={<LegacyRouteRedirect to="/lanes" />} />
        <Route path="failure-explorer" element={<FailureExplorerPage />} />
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
