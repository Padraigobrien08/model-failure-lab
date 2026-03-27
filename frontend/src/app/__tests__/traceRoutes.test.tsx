import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";

type RouteCase = {
  entry: string;
  question: string;
  params: Array<[name: string, value: string]>;
};

const ROUTE_CASES: RouteCase[] = [
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

  it("renders /lane/:laneId/:methodId as a real method workspace instead of placeholder content", () => {
    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting"]} />);

    expect(screen.getByRole("heading", { name: "Reweighting" })).toBeInTheDocument();
    expect(screen.getByText("Why is this method judged this way?")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Reweighting runs" })).toBeInTheDocument();
    expect(screen.queryByText("Current params")).not.toBeInTheDocument();
  });

  it("renders /run/:runId as a real run workspace instead of placeholder content", () => {
    render(
      <App
        useMemoryRouter
        initialEntries={["/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting"]}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "distilbert_reweighting_seed_13", level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByText("What happened in this run?")).toBeInTheDocument();
    expect(screen.getByLabelText("Run breadcrumb")).toBeInTheDocument();
    expect(screen.getByText("Interpretation")).toBeInTheDocument();
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

  it("preserves scope=all across method route links", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />);

    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");

    const breadcrumb = screen.getByLabelText("Method breadcrumb");
    const summaryLink = within(breadcrumb).getByRole("link", { name: "Summary" });
    expect(summaryLink).toHaveAttribute("href", "/?scope=all");

    const laneLink = within(breadcrumb).getByRole("link", { name: "Robustness" });
    expect(laneLink).toHaveAttribute("href", "/lane/robustness?scope=all");

    const runTable = screen.getByRole("table", { name: "Reweighting runs" });
    const runLink = within(runTable).getByRole("link", {
      name: "distilbert_reweighting_seed_13",
    });
    expect(runLink).toHaveAttribute(
      "href",
      "/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting",
    );

    await user.click(runLink);

    expect(
      await screen.findByRole("heading", {
        name: "distilbert_reweighting_seed_13",
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    expect(within(screen.getByLabelText("Run breadcrumb")).getByRole("link", { name: "Reweighting" })).toHaveAttribute(
      "href",
      "/lane/robustness/reweighting?scope=all",
    );
  });
});
