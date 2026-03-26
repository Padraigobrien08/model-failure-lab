import {
  BrowserRouter,
  MemoryRouter,
  Route,
  Routes,
  useLocation,
  useParams,
} from "react-router-dom";

import { TraceScopeProvider, useTraceScope } from "@/app/scope";
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

type TraceScaffoldPageProps = {
  title: string;
  description: string;
};

function TraceScaffoldPage({ title, description }: TraceScaffoldPageProps) {
  const location = useLocation();
  const params = useParams();
  const { scope } = useTraceScope();
  const routeParams = Object.entries(params).filter(([, value]) => value !== undefined);

  return (
    <section className="space-y-6 rounded-[24px] border border-border/70 bg-card/70 p-6 shadow-sm">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Phase 36 scaffold
        </p>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">{title}</h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p>
      </div>

      <dl className="grid gap-3 md:grid-cols-2">
        <div className="rounded-[18px] border border-border/70 bg-background/60 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Active scope
          </dt>
          <dd className="mt-2 text-sm font-medium text-foreground">
            {scope === "all" ? "All" : "Official"}
          </dd>
        </div>
        <div className="rounded-[18px] border border-border/70 bg-background/60 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Current path
          </dt>
          <dd className="mt-2 font-mono text-sm text-foreground">{location.pathname}</dd>
        </div>
      </dl>

      <div className="rounded-[18px] border border-border/70 bg-background/60 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Route params
        </p>
        {routeParams.length > 0 ? (
          <dl className="mt-3 space-y-2">
            {routeParams.map(([key, value]) => (
              <div key={key} className="flex items-center justify-between gap-3 text-sm">
                <dt className="font-medium text-foreground">{key}</dt>
                <dd className="font-mono text-muted-foreground">{value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">No dynamic params for this route.</p>
        )}
      </div>
    </section>
  );
}

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
        <Route
          path="/"
          element={
            <TraceScaffoldPage
              title="Verdict"
              description="This route becomes the trace entry point before the dedicated summary content lands in the next plan."
            />
          }
        />
        <Route
          path="/lane/:laneId"
          element={
            <TraceScaffoldPage
              title="Lane"
              description="This scaffold route holds one lane branch in the Phase 36 trace chain."
            />
          }
        />
        <Route
          path="/lane/:laneId/:methodId"
          element={
            <TraceScaffoldPage
              title="Method"
              description="This scaffold route narrows the selected lane to one method."
            />
          }
        />
        <Route
          path="/run/:runId"
          element={
            <TraceScaffoldPage
              title="Run"
              description="This scaffold route will host the focused run trace."
            />
          }
        />
        <Route
          path="/debug/raw/:entityId"
          element={
            <TraceScaffoldPage
              title="Artifact"
              description="This scaffold route reserves the raw debug surface for a single entity."
            />
          }
        />
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
