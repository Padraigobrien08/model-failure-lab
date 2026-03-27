import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "@/app/App";

const writeText = vi.fn().mockResolvedValue(undefined);

describe("Raw debug page", () => {
  beforeEach(() => {
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
  });

  afterEach(() => {
    cleanup();
    writeText.mockClear();
    window.history.replaceState({}, "", "/");
  });

  it("keeps related entities visible while tabs switch and copies the active payload only", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/debug/raw/run_distilbert_reweighting_seed_13?scope=all"]}
      />,
    );

    expect(screen.getByRole("tab", { name: "Raw JSON" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/"runId": "distilbert_reweighting_seed_13"/)).toBeInTheDocument();

    const relatedEntities = screen.getByTestId("related-entities");
    expect(within(relatedEntities).getByText("Related entities")).toBeInTheDocument();
    expect(within(relatedEntities).getByText("Parent method")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Copy Raw JSON" }));
    expect(screen.getByRole("button", { name: "Copied Raw JSON" })).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Metadata" }));

    expect(screen.getByRole("button", { name: "Copy Metadata" })).toBeInTheDocument();
    expect(within(relatedEntities).getByText("Baseline reference")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Copy Metadata" }));
    expect(screen.getByRole("button", { name: "Copied Metadata" })).toBeInTheDocument();
  });

  it("shows a scoped warning first and lets the user recover by including exploratory entities", async () => {
    const user = userEvent.setup();

    render(
      <App
        useMemoryRouter
        initialEntries={["/debug/raw/method_group_dro_robustness?scope=official"]}
      />,
    );

    expect(screen.getByText("Scope warning")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Include exploratory" })).toHaveAttribute(
      "href",
      "/debug/raw/method_group_dro_robustness?scope=all",
    );

    await user.click(screen.getByRole("link", { name: "Include exploratory" }));

    expect(await screen.findByRole("tab", { name: "Raw JSON" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  });
});
