import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";

const LEGACY_TRACE_PATHS = [
  "/lane/robustness",
  "/lane/robustness/reweighting",
  "/lane/robustness/reweighting?scope=all",
  "/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting",
  "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
  "/failure-explorer",
  "/evidence",
];

describe("Trace scaffold routes", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders the runs workspace at /", () => {
    render(<App useMemoryRouter initialEntries={["/"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });

  it.each(LEGACY_TRACE_PATHS)(
    "redirects the removed manifest-era route %s to the runs workspace",
    (path) => {
      render(<App useMemoryRouter initialEntries={[path]} />);

      expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
      expect(
        screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
      ).toBeInTheDocument();
    },
  );
});
