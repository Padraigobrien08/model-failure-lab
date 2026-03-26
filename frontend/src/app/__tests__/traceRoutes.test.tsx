import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";

type RouteCase = {
  entry: string;
  question: string;
  params: Array<[name: string, value: string]>;
};

const ROUTE_CASES: RouteCase[] = [
  {
    entry: "/",
    question: "Where should I look?",
    params: [],
  },
  {
    entry: "/lane/robustness",
    question: "Why is this lane in focus?",
    params: [["laneId", "robustness"]],
  },
  {
    entry: "/lane/robustness/reweighting",
    question: "Why is this method judged this way?",
    params: [
      ["laneId", "robustness"],
      ["methodId", "reweighting"],
    ],
  },
  {
    entry: "/run/distilbert_reweighting_seed_13",
    question: "What happened in this run?",
    params: [["runId", "distilbert_reweighting_seed_13"]],
  },
  {
    entry: "/debug/raw/run_distilbert_reweighting_seed_13",
    question: "What artifact backs this entity?",
    params: [["entityId", "run_distilbert_reweighting_seed_13"]],
  },
];

describe("Trace scaffold routes", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it.each(ROUTE_CASES)("renders $entry with its dedicated placeholder content", ({ entry, question, params }) => {
    render(<App useMemoryRouter initialEntries={[entry]} />);

    expect(screen.getByRole("heading", { name: question })).toBeInTheDocument();

    if (params.length === 0) {
      expect(screen.getByText("No dynamic params for this route.")).toBeInTheDocument();
      return;
    }

    for (const [name, value] of params) {
      expect(screen.getByText(name)).toBeInTheDocument();
      expect(screen.getByText(value)).toBeInTheDocument();
    }
  });

  it("preserves scope=all across scaffold route links", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=all"]} />);

    expect(
      screen.getByText((_, element) => element?.textContent === "Current scope: All"),
    ).toBeInTheDocument();

    const nextLink = screen.getByRole("link", { name: "Method sample" });
    expect(nextLink).toHaveAttribute("href", "/lane/robustness/reweighting?scope=all");

    await user.click(nextLink);

    expect(
      await screen.findByRole("heading", { name: "Why is this method judged this way?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByText((_, element) => element?.textContent === "Current scope: All"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Run sample" })).toHaveAttribute(
      "href",
      "/run/distilbert_reweighting_seed_13?scope=all",
    );
  });
});
