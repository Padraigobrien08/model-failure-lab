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

  it("redirects the removed lane routes to the runs workspace", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness"]} />);

    expect(screen.getByRole("link", { name: "Runs" })).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByRole("heading", { name: "Start from saved runs, not abstract reports." }),
    ).toBeInTheDocument();
  });
});
