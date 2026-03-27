import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";

const ROBUSTNESS_LANE_PATH = "/lane/robustness?scope=all";
const REWEIGHTING_METHOD_PATH = "/lane/robustness/reweighting?scope=all";

describe("Summary route", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders the compact verdict view with baseline-first previews in official scope", () => {
    window.history.replaceState({}, "", "/");

    render(<App />);

    expect(screen.getByRole("heading", { name: "Where should I look?" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Robustness" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Calibration" })).toBeInTheDocument();
    expect(screen.queryByText("Exploratory")).not.toBeInTheDocument();

    const robustnessPanel = screen.getByTestId("robustness-lane-panel");
    const robustnessMethodLinks = Array.from(robustnessPanel.querySelectorAll("a")).map((link) =>
      link.textContent?.trim(),
    );

    expect(robustnessMethodLinks).toEqual(["Baseline", "Reweighting"]);

    const calibrationPanel = screen.getByTestId("calibration-lane-panel");
    const calibrationMethodLinks = Array.from(calibrationPanel.querySelectorAll("a")).map((link) =>
      link.textContent?.trim(),
    );

    expect(calibrationMethodLinks[0]).toBe("Baseline");
  });

  it("opens the lane route from the whole lane panel while preserving scope=all", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/?scope=all");

    render(<App />);

    const robustnessPanel = screen.getByTestId("robustness-lane-panel");
    expect(within(robustnessPanel).getByText("Exploratory")).toBeInTheDocument();

    await user.click(robustnessPanel);

    expect(await screen.findByRole("heading", { name: "Robustness" })).toBeInTheDocument();

    await waitFor(() => {
      expect(`${window.location.pathname}${window.location.search}`).toBe(ROBUSTNESS_LANE_PATH);
    });
  });

  it("opens the inline method route without falling back to the whole-panel target", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/?scope=all");

    render(<App />);

    const robustnessPanel = screen.getByTestId("robustness-lane-panel");
    const reweightingLink = within(robustnessPanel).getByRole("link", { name: "Reweighting" });

    await user.click(reweightingLink);

    expect(await screen.findByRole("heading", { name: "Reweighting" })).toBeInTheDocument();
    expect(screen.getByText("Why is this method judged this way?")).toBeInTheDocument();

    await waitFor(() => {
      expect(`${window.location.pathname}${window.location.search}`).toBe(REWEIGHTING_METHOD_PATH);
    });
  });
});
