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

  it("renders / with the summary verdict strip and compact lane panels", () => {
    render(<App useMemoryRouter initialEntries={["/"]} />);

    expect(screen.getByRole("heading", { name: "Where should I look?" })).toBeInTheDocument();
    expect(screen.getByText("Calibration is stable, but robustness still needs scrutiny before widening the default story.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Robustness" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Calibration" })).toBeInTheDocument();
    expect(screen.queryByText("No dynamic params for this route.")).not.toBeInTheDocument();
  });

  it("renders /lane/:laneId as a real lane workspace instead of placeholder content", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness"]} />);

    expect(screen.getByRole("heading", { name: "Robustness" })).toBeInTheDocument();
    expect(screen.getByText("What is happening in this lane?")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Method" })).toBeInTheDocument();
    expect(screen.queryByText("Current params")).not.toBeInTheDocument();
  });

  it.each(ROUTE_CASES)("renders $entry with its dedicated placeholder content", ({ entry, question, params }) => {
    render(<App useMemoryRouter initialEntries={[entry]} />);

    expect(screen.getByRole("heading", { name: question })).toBeInTheDocument();

    for (const [name, value] of params) {
      expect(screen.getByText(name)).toBeInTheDocument();
      expect(screen.getByText(value)).toBeInTheDocument();
    }
  });

  it("preserves scope=all across scaffold route links", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />);

    expect(
      screen.getByText((_, element) => element?.textContent === "Current scope: All"),
    ).toBeInTheDocument();

    const previousLink = screen.getByRole("link", { name: "Lane" });
    expect(previousLink).toHaveAttribute("href", "/lane/robustness?scope=all");

    const nextLink = screen.getByRole("link", { name: "Run sample" });
    expect(nextLink).toHaveAttribute("href", "/run/distilbert_reweighting_seed_13?scope=all");

    await user.click(nextLink);

    expect(
      await screen.findByRole("heading", { name: "What happened in this run?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByText((_, element) => element?.textContent === "Current scope: All"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Artifact sample" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
    );
  });
});
