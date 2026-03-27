import { Outlet } from "react-router-dom";

import { TraceHeader } from "@/components/layout/TraceHeader";

export function TraceShell() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="sticky top-0 z-20 backdrop-blur">
        <TraceHeader />
      </div>
      <main className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}
