import { cleanup, render, screen, waitFor } from "@testing-library/react";

import { App } from "@/app/App";

describe("App shell", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("mounts the scaffold route contract in a memory router", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />);

    expect(screen.getByRole("heading", { name: "Method" })).toBeInTheDocument();
    expect(screen.getByText("/lane/robustness/reweighting")).toBeInTheDocument();
    expect(screen.getByText("methodId")).toBeInTheDocument();
    expect(screen.getByText("reweighting")).toBeInTheDocument();
    expect(screen.getByText("Active scope")).toBeInTheDocument();
    expect(screen.getByText("All")).toBeInTheDocument();
  });

  it("normalizes invalid browser scope params back to official", async () => {
    window.history.replaceState({}, "", "/run/demo-run?scope=exploratory");

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Run" })).toBeInTheDocument();
    expect(screen.getByText("Official")).toBeInTheDocument();
    await waitFor(() => {
      expect(window.location.search).toBe("?scope=official");
    });
  });
});
