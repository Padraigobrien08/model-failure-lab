import { useEffect, useState } from "react";
import { BrowserRouter, MemoryRouter, Route, Routes } from "react-router-dom";

import type { AppRouteContext } from "@/app/router";
import { AppShell } from "@/components/layout/AppShell";
import { loadArtifactIndex, DEFAULT_MANIFEST_PATH } from "@/lib/manifest/load";
import type { ArtifactIndex } from "@/lib/manifest/types";
import { PlaceholderPage } from "@/app/routes/PlaceholderPage";
import { OverviewPage } from "@/app/routes/OverviewPage";

type AppProps = {
  manifestPath?: string;
  initialIndex?: ArtifactIndex | null;
  initialIncludeExploratory?: boolean;
  useMemoryRouter?: boolean;
  initialEntries?: string[];
};

type AppFrameProps = {
  manifestPath: string;
  initialIndex?: ArtifactIndex | null;
  initialIncludeExploratory: boolean;
};

function AppFrame({
  manifestPath,
  initialIndex = null,
  initialIncludeExploratory,
}: AppFrameProps) {
  const [index, setIndex] = useState<ArtifactIndex | null>(initialIndex);
  const [isLoading, setIsLoading] = useState<boolean>(initialIndex === null);
  const [error, setError] = useState<string | null>(null);
  const [includeExploratory, setIncludeExploratory] = useState(initialIncludeExploratory);

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

  const routeContext: AppRouteContext = {
    index,
    isLoading,
    error,
    includeExploratory,
    setIncludeExploratory,
    manifestPath,
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
        <Route
          path="comparisons"
          element={
            <PlaceholderPage
              title="Comparisons"
              description="Phase 29 turns the saved baseline and mitigation evidence into side-by-side comparison flows."
            />
          }
        />
        <Route
          path="failure-explorer"
          element={
            <PlaceholderPage
              title="Failure Explorer"
              description="Phase 29 brings subgroup, ID/OOD, and calibration failure surfaces into this route."
            />
          }
        />
        <Route
          path="runs"
          element={
            <PlaceholderPage
              title="Runs"
              description="Phase 30 adds run-level drillthrough, lineage context, and route-preserving debug transitions."
            />
          }
        />
        <Route
          path="evidence"
          element={
            <PlaceholderPage
              title="Evidence"
              description="Phase 30 adds artifact drillthrough and explicit evidence-scope controls here."
            />
          }
        />
      </Route>
    </Routes>
  );
}

export function App({
  manifestPath = DEFAULT_MANIFEST_PATH,
  initialIndex = null,
  initialIncludeExploratory = false,
  useMemoryRouter = false,
  initialEntries = ["/"],
}: AppProps) {
  const appFrame = (
    <AppFrame
      manifestPath={manifestPath}
      initialIndex={initialIndex}
      initialIncludeExploratory={initialIncludeExploratory}
    />
  );

  if (useMemoryRouter) {
    return <MemoryRouter initialEntries={initialEntries}>{appFrame}</MemoryRouter>;
  }

  return <BrowserRouter>{appFrame}</BrowserRouter>;
}
