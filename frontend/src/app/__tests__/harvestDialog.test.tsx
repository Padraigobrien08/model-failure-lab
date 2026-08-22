import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HarvestDialog } from "@/components/console/HarvestDialog";
import {
  DATASET_ID,
  FAMILY_ID,
  REPORT_ID,
  buildDatasetEvolutionWire,
  buildGovernanceRecommendation,
  buildSignal,
} from "@/test/factories";
import { stubFetch } from "@/test/render";

function renderDialog(onClose = vi.fn(), onWritten = vi.fn()) {
  render(
    <MemoryRouter>
      <HarvestDialog
        open
        onClose={onClose}
        reportId={REPORT_ID}
        dataset={DATASET_ID}
        signal={buildSignal()}
        recommendation={buildGovernanceRecommendation()}
        onWritten={onWritten}
      />
    </MemoryRouter>,
  );
  return { onClose, onWritten };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("HarvestDialog", () => {
  it("shows carrying-forward counts from the matched family and the mode segment", () => {
    renderDialog();

    expect(
      screen.getByRole("dialog", { name: "Harvest regressions" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Promote 2 regressed cases")).toBeInTheDocument();

    // Carrying-forward panel from matchedFamily.
    const panel = screen.getByText("Carrying forward").parentElement!;
    expect(panel).toHaveTextContent("2 selected cases");
    expect(panel).toHaveTextContent("12 inherited from qa-regressions-v2");
    expect(panel).toHaveTextContent("14 total");

    // Mode segment offers Evolve (family exists) and New draft pack.
    expect(
      screen.getByRole("radio", { name: `Evolve ${FAMILY_ID}` }),
    ).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "New draft pack" })).toBeInTheDocument();

    // Write button targets the next version.
    expect(screen.getByRole("button", { name: "Write v3" })).toBeInTheDocument();
  });

  it("Write posts to dataset-evolve.json and shows the receipt with outputPath", async () => {
    const calls = stubFetch([
      { match: "dataset-evolve.json", respond: buildDatasetEvolutionWire() },
    ]);
    const user = userEvent.setup();
    const { onWritten } = renderDialog();

    await user.click(screen.getByRole("button", { name: "Write v3" }));

    // Request body carries familyId and comparisonId.
    expect(await screen.findByText("Dataset written")).toBeInTheDocument();
    const post = calls.find((call) => call.url.includes("dataset-evolve.json"))!;
    expect(post.init?.method).toBe("POST");
    const body = JSON.parse(String(post.init?.body));
    expect(body.familyId).toBe(FAMILY_ID);
    expect(body.comparisonId).toBe(REPORT_ID);

    // Receipt.
    const receipt = screen
      .getByText("wrote datasets/qa-regressions-v3.json")
      .parentElement!;
    expect(receipt).toHaveTextContent("qa-regressions-v3 · version v3");
    expect(receipt).toHaveTextContent("12 inherited + 2 added");
    expect(receipt).toHaveTextContent("14 total");
    expect(onWritten).toHaveBeenCalled();
  });

  it("error path shows the message and the CLI fallback", async () => {
    stubFetch([
      {
        match: "dataset-evolve.json",
        respond: { __status: 409, body: { message: "family is capped" } },
      },
    ]);
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByRole("button", { name: "Write v3" }));

    const dialog = screen.getByRole("dialog", { name: "Harvest regressions" });
    await waitFor(() => expect(dialog).toHaveTextContent("family is capped"));
    expect(dialog).toHaveTextContent(
      `run: failure-lab dataset evolve ${FAMILY_ID} --comparison ${REPORT_ID}`,
    );
  });

  it("Escape calls onClose", async () => {
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalled();
  });
});
