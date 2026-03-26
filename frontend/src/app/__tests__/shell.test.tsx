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
    expect(screen.getByRole("heading", { name: "Method" })).toBeInTheDocument();
    expect(screen.getByText("/lane/robustness/reweighting")).toBeInTheDocument();
    expect(screen.getByText("methodId")).toBeInTheDocument();
    expect(screen.getByText("reweighting")).toBeInTheDocument();
    expect(container.querySelector("aside")).toBeNull();
  });

  it("normalizes invalid browser scope params back to official", async () => {
    window.history.replaceState({}, "", "/run/demo-run?scope=exploratory");

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Run" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Official" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await waitFor(() => {
      expect(window.location.search).toBe("?scope=official");
    });
  });
});
