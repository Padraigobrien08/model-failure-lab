import { cleanup, render, screen } from "@testing-library/react";

import { App } from "@/app/App";
import { buildLaneRouteModel } from "@/lib/laneRoute";

describe("Lane route model", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("keeps baseline first and exposes the robustness columns", () => {
    const lane = buildLaneRouteModel("robustness", "official");

    expect(lane.rows[0]?.methodId).toBe("baseline");
    expect(lane.columns.map((column) => column.label)).toEqual([
      "Method",
      "Status",
      "Worst-group",
      "OOD",
      "ID",
      "Delta vs baseline",
    ]);
  });

  it("keeps baseline first and exposes the calibration columns", () => {
    const lane = buildLaneRouteModel("calibration", "official");

    expect(lane.rows[0]?.methodId).toBe("baseline");
    expect(lane.columns.map((column) => column.label)).toEqual([
      "Method",
      "Status",
      "ECE",
      "Brier",
      "Delta vs baseline",
    ]);
  });

  it("renders a real table-first lane route for robustness", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness"]} />);

    expect(screen.getByRole("heading", { name: "Robustness" })).toBeInTheDocument();
    expect(screen.getByText("What is happening in this lane?")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Worst-group" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "OOD" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "ID" })).toBeInTheDocument();
    expect(screen.queryByText("Why is this lane in focus?")).not.toBeInTheDocument();
  });

  it("switches the visible columns for the calibration lane", () => {
    render(<App useMemoryRouter initialEntries={["/lane/calibration"]} />);

    expect(screen.getByRole("heading", { name: "Calibration" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "ECE" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Brier" })).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Worst-group" })).not.toBeInTheDocument();
  });
});
