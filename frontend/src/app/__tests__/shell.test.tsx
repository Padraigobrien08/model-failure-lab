import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app/App";

describe("App shell", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState({}, "", "/");
  });

  it("renders a sticky-header scaffold with the trace chain and scope controls", () => {
    const { container } = render(
      <App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />,
    );

    const traceChain = screen.getByLabelText("Trace chain");

    expect(screen.getByRole("link", { name: "Failure Debugger" })).toBeInTheDocument();
    expect(traceChain).toBeInTheDocument();
    expect(within(traceChain).getByRole("link", { name: "Verdict" })).toHaveAttribute(
      "href",
      "/?scope=all",
    );
    expect(within(traceChain).getByRole("link", { name: "Lane" })).toHaveAttribute(
      "href",
      "/lane/robustness?scope=all",
    );
    expect(within(traceChain).getByText("Method")).toHaveAttribute("aria-current", "page");
    expect(within(traceChain).getByRole("link", { name: "Run" })).toHaveAttribute(
      "href",
      "/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting",
    );
    expect(within(traceChain).getByRole("link", { name: "Artifact" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
    );
    expect(screen.getByRole("button", { name: "Official" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Why is this method judged this way?")).toBeInTheDocument();
    expect(screen.getByLabelText("Method breadcrumb")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Reweighting runs" })).toBeInTheDocument();
    expect(screen.getByText("Method explanation")).toBeInTheDocument();
    expect(screen.getByText("Lineage")).toBeInTheDocument();
    expect(container.querySelector("main")).not.toBeNull();
    expect(screen.getByTestId("method-inspector")).toBeInTheDocument();
  });

  it("lets users navigate backward through the trace chain without losing scope", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness/reweighting?scope=all"]} />);

    const traceChain = screen.getByLabelText("Trace chain");

    await user.click(within(traceChain).getByRole("link", { name: "Lane" }));

    expect(await screen.findByRole("heading", { name: "Robustness" })).toBeInTheDocument();
    expect(screen.getByText("What is happening in this lane?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");

    await user.click(within(screen.getByLabelText("Trace chain")).getByRole("link", { name: "Verdict" }));

    expect(await screen.findByRole("heading", { name: "Where should I look?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  });

  it("lets users move forward from verdict to lane and method through the trace chain", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/?scope=all"]} />);

    const traceChain = screen.getByLabelText("Trace chain");

    expect(within(traceChain).getByText("Verdict")).toHaveAttribute("aria-current", "page");
    expect(within(traceChain).getByRole("link", { name: "Lane" })).toHaveAttribute(
      "href",
      "/lane/robustness?scope=all",
    );
    expect(within(traceChain).getByRole("link", { name: "Method" })).toHaveAttribute(
      "href",
      "/lane/robustness/reweighting?scope=all",
    );
    expect(within(traceChain).getByRole("link", { name: "Run" })).toHaveAttribute(
      "href",
      "/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting",
    );

    await user.click(within(traceChain).getByRole("link", { name: "Lane" }));

    expect(await screen.findByRole("heading", { name: "Robustness" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");

    await user.click(within(screen.getByLabelText("Trace chain")).getByRole("link", { name: "Method" }));

    expect(await screen.findByText("Why is this method judged this way?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  });

  it("keeps the same inspector contract visible through lane to method to run traversal", async () => {
    const user = userEvent.setup();

    render(<App useMemoryRouter initialEntries={["/lane/robustness?scope=all"]} />);

    const laneInspector = screen.getByTestId("lane-inspector");
    expect(within(laneInspector).getByText("Evidence")).toBeInTheDocument();
    expect(within(laneInspector).getByText("Provenance preview")).toBeInTheDocument();
    expect(within(laneInspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/method_baseline_robustness?scope=all",
    );

    await user.click(screen.getByRole("link", { name: "Reweighting" }));

    const methodInspector = await screen.findByTestId("method-inspector");
    expect(within(methodInspector).getByText("Evidence")).toBeInTheDocument();
    expect(within(methodInspector).getByText("Provenance preview")).toBeInTheDocument();
    expect(within(methodInspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
    );

    await user.click(screen.getByRole("link", { name: "distilbert_reweighting_seed_13" }));

    const runInspector = await screen.findByTestId("run-inspector");
    expect(within(runInspector).getByText("Evidence")).toBeInTheDocument();
    expect(within(runInspector).getByText("Provenance preview")).toBeInTheDocument();
    expect(within(runInspector).getByRole("link", { name: "Open raw" })).toHaveAttribute(
      "href",
      "/debug/raw/run_distilbert_reweighting_seed_13?scope=all",
    );
  });

  it("normalizes invalid browser scope params back to official", async () => {
    window.history.replaceState({}, "", "/run/demo-run?scope=exploratory");

    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "distilbert_baseline_seed_13",
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Official" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await waitFor(() => {
      expect(window.location.search).toBe("?scope=official");
    });
  });
});
