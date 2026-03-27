import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import { buildMethodRouteModel } from "@/lib/methodRoute";

describe("Method route model", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("keeps robustness runs in seed-first order and selects the first official run by default", () => {
    const model = buildMethodRouteModel("robustness", "reweighting", "official");
    expect(model.state).toBe("ready");

    if (model.state !== "ready") {
      throw new Error("Expected the robustness reweighting route to be ready.");
    }

    expect(model.metricStrip.map((metric) => metric.label)).toEqual(["Worst-group", "OOD", "ID"]);
    expect(model.metricStrip.map((metric) => metric.deltaVsBaseline)).toEqual([0.061, -0.018, -0.008]);
    expect(model.runs.map((run) => run.seed)).toEqual([13, 42, 87]);
    expect(model.defaultRunEntityId).toBe("run_distilbert_reweighting_seed_13");
  });

  it("keeps calibration runs in seed-first order and exposes lower-is-better metrics", () => {
    const model = buildMethodRouteModel("calibration", "temperature_scaling", "official");
    expect(model.state).toBe("ready");

    if (model.state !== "ready") {
      throw new Error("Expected the calibration temperature-scaling route to be ready.");
    }

    expect(model.metricStrip.map((metric) => metric.label)).toEqual(["ECE", "Brier"]);
    expect(model.metricStrip.every((metric) => metric.lowerIsBetter)).toBe(true);
    expect(model.runs.map((run) => run.seed)).toEqual([13, 42, 87]);
    expect(model.defaultRunEntityId).toBe("run_distilbert_temperature_scaling_seed_13");
  });

  it("renders a real method route instead of placeholder content", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting"]} />);

    expect(screen.getByRole("heading", { name: "Reweighting" })).toBeInTheDocument();
    expect(screen.getByText("Why is this method judged this way?")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Reweighting runs" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Run ID" })).toBeInTheDocument();
    expect(screen.queryByText("Current params")).not.toBeInTheDocument();
  });
});
