import { Outlet } from "react-router-dom";

import { TraceHeader } from "@/components/layout/TraceHeader";

export function TraceShell() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="sticky top-0 z-20 backdrop-blur">
        <TraceHeader />
      </div>
      <main className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
