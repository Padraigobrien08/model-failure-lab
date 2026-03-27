import { BrowserRouter, MemoryRouter, Route, Routes } from "react-router-dom";

import { LanePage } from "@/app/routes/LanePage";
import { MethodPage } from "@/app/routes/MethodPage";
import { RawDebugPage } from "@/app/routes/RawDebugPage";
import { RunPage } from "@/app/routes/RunPage";
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
        <Route path="/lane/:laneId/:methodId" element={<MethodPage />} />
        <Route path="/run/:runId" element={<RunPage />} />
        <Route path="/debug/raw/:entityId" element={<RawDebugPage />} />
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
