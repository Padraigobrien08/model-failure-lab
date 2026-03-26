import { createContext, useContext, useEffect, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";

export type TraceScope = "official" | "all";

type TraceScopeContextValue = {
  scope: TraceScope;
  setScope: (next: TraceScope) => void;
};

type TraceScopeProviderProps = {
  children: ReactNode;
};

const DEFAULT_SCOPE: TraceScope = "official";

const TraceScopeContext = createContext<TraceScopeContextValue | null>(null);

function normalizeTraceScope(value: string | null): TraceScope {
  return value === "all" ? "all" : DEFAULT_SCOPE;
}

export function TraceScopeProvider({ children }: TraceScopeProviderProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const scope = normalizeTraceScope(searchParams.get("scope"));

  useEffect(() => {
    const currentScope = searchParams.get("scope");

    if (currentScope === scope) {
      return;
    }

    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("scope", scope);
    setSearchParams(nextSearchParams, { replace: true });
  }, [scope, searchParams, setSearchParams]);

  function setScope(next: TraceScope) {
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("scope", next);
    setSearchParams(nextSearchParams, { replace: true });
  }

  return (
    <TraceScopeContext.Provider value={{ scope, setScope }}>
      {children}
    </TraceScopeContext.Provider>
  );
}

export function useTraceScope() {
  const context = useContext(TraceScopeContext);

  if (context === null) {
    throw new Error("useTraceScope must be used within a TraceScopeProvider");
  }

  return context;
}
