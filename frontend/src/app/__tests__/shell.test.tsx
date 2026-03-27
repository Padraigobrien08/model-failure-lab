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
