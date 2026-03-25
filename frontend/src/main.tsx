import React from "react";
import ReactDOM from "react-dom/client";
import "@/styles/index.css";

function BootstrapPlaceholder() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-5xl items-center justify-center px-6 py-16">
        <section className="w-full rounded-[28px] border border-border/70 bg-card/95 p-10 shadow-panel backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-primary">
            Phase 28 Foundation
          </p>
          <h1 className="mt-4 max-w-2xl font-sans text-4xl font-semibold tracking-[-0.04em] text-foreground">
            React failure debugger shell is bootstrapping over the saved artifact contract.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
            The manifest bridge and typed selectors live under <code>frontend/src/lib/manifest</code>.
            The full route shell and overview launchpad land in Wave 2.
          </p>
        </section>
      </div>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BootstrapPlaceholder />
  </React.StrictMode>,
);
