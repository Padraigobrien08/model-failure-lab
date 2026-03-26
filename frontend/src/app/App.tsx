import { BrowserRouter, MemoryRouter, Route, Routes } from "react-router-dom";

import { LanePage } from "@/app/routes/LanePage";
import { MethodPlaceholderPage } from "@/app/routes/MethodPlaceholderPage";
import { RawDebugPlaceholderPage } from "@/app/routes/RawDebugPlaceholderPage";
import { RunPlaceholderPage } from "@/app/routes/RunPlaceholderPage";
import { SummaryPage } from "@/app/routes/SummaryPage";
import { TraceScopeProvider } from "@/app/scope";
import { TraceShell } from "@/components/layout/TraceShell";
import type { ArtifactIndex, FinalRobustnessBundle } from "@/lib/manifest/types";

type AppProps = {
  manifestPath?: string;
  initialIndex?: ArtifactIndex | null;
  initialFinalRobustnessBundle?: FinalRobustnessBundle | null;
  initialIncludeExploratory?: boolean;
  useMemoryRouter?: boolean;
  initialEntries?: string[];
};

function AppFrame() {
  return (
    <Routes>
      <Route
        element={
          <TraceScopeProvider>
            <TraceShell />
          </TraceScopeProvider>
        }
      >
        <Route path="/" element={<SummaryPage />} />
        <Route path="/lane/:laneId" element={<LanePage />} />
        <Route path="/lane/:laneId/:methodId" element={<MethodPlaceholderPage />} />
        <Route path="/run/:runId" element={<RunPlaceholderPage />} />
        <Route path="/debug/raw/:entityId" element={<RawDebugPlaceholderPage />} />
      </Route>
    </Routes>
  );
}

export function App({
  useMemoryRouter = false,
  initialEntries = ["/"],
}: AppProps) {
  const appFrame = <AppFrame />;

  if (useMemoryRouter) {
    return <MemoryRouter initialEntries={initialEntries}>{appFrame}</MemoryRouter>;
  }

  return <BrowserRouter>{appFrame}</BrowserRouter>;
}
