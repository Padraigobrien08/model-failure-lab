import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buildGateState, SOURCE } from "@/test/factories";
import { renderApp } from "@/test/render";

describe("ConsoleShell", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("renders the brand and the four nav items with counts", () => {
    renderApp();

    expect(screen.getByText("Failure Lab")).toBeInTheDocument();

    const nav = screen.getByRole("navigation", { name: "Primary" });
    const runsLink = screen.getByRole("link", { name: /Runs/ });
    const comparisonsLink = screen.getByRole("link", { name: /Comparisons/ });
    const evidenceLink = screen.getByRole("link", { name: "Evidence" });
    const datasetsLink = screen.getByRole("link", { name: /Datasets/ });
    for (const link of [runsLink, comparisonsLink, evidenceLink, datasetsLink]) {
      expect(nav).toContainElement(link);
    }

    // Counts: 2 runs, 1 comparison, 2 dataset families.
    expect(runsLink).toHaveTextContent("2");
    expect(comparisonsLink).toHaveTextContent("1");
    expect(datasetsLink).toHaveTextContent("2");
  });

  it("shows a FAIL chip on the Gate row when the gate is blocked", () => {
    renderApp(["/"], { initialGateState: buildGateState("blocked") });
    const gateLink = screen.getByRole("link", { name: /Gate/ });
    expect(gateLink).toHaveTextContent("FAIL");
  });

  it("shows a PASS chip on the Gate row when the gate is clear", () => {
    renderApp(["/"], { initialGateState: buildGateState("clear") });
    const gateLink = screen.getByRole("link", { name: /Gate/ });
    expect(gateLink).toHaveTextContent("PASS");
  });

  it("shows the artifact root path and the contract-clean chip", () => {
    renderApp();
    expect(screen.getByText(SOURCE.path)).toBeInTheDocument();
    expect(screen.getByText("contract clean")).toBeInTheDocument();
  });

  it("theme toggle flips data-theme on documentElement and persists to localStorage", async () => {
    const user = userEvent.setup();
    renderApp();

    // Mount effect applies the default light theme.
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(window.localStorage.getItem("failure-lab-theme")).toBe("light");

    await user.click(screen.getByRole("button", { name: "Light" }));

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(window.localStorage.getItem("failure-lab-theme")).toBe("dark");
    expect(screen.getByRole("button", { name: "Dark" })).toBeInTheDocument();
  });
});
