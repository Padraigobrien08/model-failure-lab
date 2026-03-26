import { cleanup, render, screen, waitFor, within } from "@testing-library/react";

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

    expect(screen.getByRole("link", { name: "Failure Debugger" })).toBeInTheDocument();
    expect(screen.getByLabelText("Trace chain")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Trace chain")).getByText("Verdict")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Trace chain")).getByText("Lane")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Trace chain")).getByText("Method")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Trace chain")).getByText("Run")).toBeInTheDocument();
    expect(within(screen.getByLabelText("Trace chain")).getByText("Artifact")).toBeInTheDocument();
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
