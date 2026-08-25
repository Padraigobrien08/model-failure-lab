import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ConsoleButton, SectionLabel } from "@/components/console/primitives";
import { createArtifactHarvestDraft } from "@/lib/artifacts/load";
import type {
  ArtifactHarvestResponse,
  RunDetailSummaryRow,
} from "@/lib/artifacts/types";

type RunHarvestDialogProps = {
  open: boolean;
  onClose: () => void;
  runId: string;
  dataset: string;
  failureTypes: RunDetailSummaryRow[];
  initialFailureType: string;
};

/** Harvest failing cases from a single run into a draft pack — no baseline needed. */
export function RunHarvestDialog({
  open,
  onClose,
  runId,
  dataset,
  failureTypes,
  initialFailureType,
}: RunHarvestDialogProps) {
  const navigate = useNavigate();
  const [failureType, setFailureType] = useState(initialFailureType);
  const [writing, setWriting] = useState(false);
  const [result, setResult] = useState<ArtifactHarvestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (open) setFailureType(initialFailureType);
  }, [open, initialFailureType]);

  useEffect(() => {
    if (!open) return;
    const panel = panelRef.current;
    const focusables = () =>
      panel
        ? Array.from(
            panel.querySelectorAll<HTMLElement>(
              'button, input, select, [tabindex]:not([tabindex="-1"])',
            ),
          ).filter((element) => !element.hasAttribute("disabled"))
        : [];
    focusables()[1]?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const elements = focusables();
      if (elements.length === 0) return;
      const first = elements[0];
      const last = elements[elements.length - 1];
      const active = document.activeElement;
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const harvestableRows = failureTypes.filter((row) => row.label !== "no_failure");
  const selectedRow = failureType
    ? harvestableRows.find((row) => row.label === failureType) ?? null
    : null;
  const selectedCount = selectedRow
    ? selectedRow.count
    : harvestableRows.reduce((total, row) => total + row.count, 0);

  const write = () => {
    setWriting(true);
    setError(null);
    void createArtifactHarvestDraft({
      mode: "cases",
      filters: { runId, failureType: failureType || null },
    })
      .then(setResult)
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : "harvest write failed");
      })
      .finally(() => setWriting(false));
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Harvest failing cases"
      className="fixed inset-0 z-50 grid place-items-center bg-[rgba(20,21,28,0.55)] p-10"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        className="w-[640px] max-w-full overflow-hidden rounded-tok border border-line bg-ground shadow-[0_24px_60px_rgba(15,17,24,0.45)]"
      >
        <div className="flex items-center gap-3.5 border-b border-line px-6 py-[18px]">
          <div>
            <SectionLabel className="tracking-[0.18em]">Harvest</SectionLabel>
            <div className="mt-[5px] font-heading text-[20px] font-semibold">
              {result ? "Draft written" : `Harvest ${selectedCount} failing cases`}
            </div>
          </div>
          <button
            type="button"
            aria-label="Close harvest dialog"
            onClick={onClose}
            className="ml-auto h-8 w-8 cursor-pointer rounded-tok border border-line bg-transparent text-ink hover:bg-raised"
          >
            <X size={12} strokeWidth={1.5} aria-hidden="true" />
          </button>
        </div>

        {result ? (
          <div className="flex flex-col gap-3 px-6 py-5">
            <div className="rounded-tok border border-line bg-good-bg px-4 py-3 font-mono text-[12px] text-good">
              wrote {result.outputPath}
            </div>
            <div className="font-mono text-[12px] leading-relaxed">
              {result.datasetId} · draft pack ·{" "}
              <span className="font-semibold">{result.selectedCaseCount} cases</span> · lifecycle{" "}
              {result.lifecycle ?? "draft"}
              <br />
              promote: failure-lab dataset promote {result.outputPath}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3.5 px-6 py-5">
            <div>
              <div className="mb-[5px] text-[12px] text-muted-ink">Source run</div>
              <div className="break-all rounded-tok border border-line bg-raised px-[10px] py-2 font-mono text-[12px]">
                {runId}
              </div>
            </div>
            <div>
              <div className="mb-[5px] text-[12px] text-muted-ink">Failure type</div>
              <select
                aria-label="Failure type filter"
                value={failureType}
                onChange={(event) => setFailureType(event.target.value)}
                className="w-full rounded-tok border border-line bg-raised px-[10px] py-[7px] font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
              >
                <option value="">all failing types</option>
                {harvestableRows.map((row) => (
                  <option key={row.label} value={row.label}>
                    {row.label} ({row.count})
                  </option>
                ))}
              </select>
            </div>
            <div className="font-mono text-[11.5px] leading-[1.9] text-muted-ink">
              {selectedCount} {selectedCount === 1 ? "case" : "cases"} from {dataset}
              <br />
              lifecycle draft · promote later to gate future runs
            </div>
            {error ? (
              <div className="rounded-tok border border-line bg-warn-bg px-3 py-2.5 font-mono text-[11.5px] text-warn">
                {error}
                <br />
                run: failure-lab harvest --run {runId}
              </div>
            ) : null}
          </div>
        )}

        <div className="flex items-center gap-2 border-t border-line px-6 py-3.5">
          <span className="mr-auto font-mono text-[11px] text-muted-ink">
            {result
              ? `${result.outputPath} · draft · promote to version it`
              : "writes datasets/harvested/<draft-id>.json · deterministic write · no network"}
          </span>
          {result ? (
            <>
              <ConsoleButton
                onClick={() => {
                  onClose();
                  navigate("/datasets");
                }}
              >
                View drafts
              </ConsoleButton>
              <ConsoleButton variant="primary" onClick={onClose}>
                Done
              </ConsoleButton>
            </>
          ) : (
            <>
              <ConsoleButton onClick={onClose}>Cancel</ConsoleButton>
              <ConsoleButton
                variant="primary"
                onClick={write}
                disabled={writing || selectedCount === 0}
              >
                {writing ? "Writing…" : "Write draft pack"}
              </ConsoleButton>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
