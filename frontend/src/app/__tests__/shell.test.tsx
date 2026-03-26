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
    expect(within(traceChain).getByText("Run")).toHaveAttribute("aria-disabled", "true");
    expect(within(traceChain).getByText("Artifact")).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("button", { name: "Official" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("heading", { name: "Why is this method judged this way?" }),
    ).toBeInTheDocument();
    expect(screen.getByText("/lane/:laneId/:methodId")).toBeInTheDocument();
    expect(screen.getByText("methodId")).toBeInTheDocument();
    expect(screen.getByText("reweighting")).toBeInTheDocument();
    expect(
      screen.getByText((_, element) => element?.textContent === "Current scope: All"),
    ).toBeInTheDocument();
    expect(screen.getByText("Previous step")).toBeInTheDocument();
    expect(screen.getByText("Next step")).toBeInTheDocument();
    expect(container.querySelector("main")).not.toBeNull();
    expect(container.querySelector("aside")).toBeNull();
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

  it("normalizes invalid browser scope params back to official", async () => {
    window.history.replaceState({}, "", "/run/demo-run?scope=exploratory");

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "What happened in this run?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Official" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(
      screen.getByText((_, element) => element?.textContent === "Current scope: Official"),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(window.location.search).toBe("?scope=official");
    });
  });
});
