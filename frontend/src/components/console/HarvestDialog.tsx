import { X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  ConsoleButton,
  ConsoleInput,
  SectionLabel,
  SegmentedControl,
  formatScore,
} from "@/components/console/primitives";
import {
  createArtifactRegressionPack,
  evolveArtifactDataset,
} from "@/lib/artifacts/load";
import type {
  ArtifactDatasetEvolutionResponse,
  ArtifactGovernanceRecommendation,
  ArtifactRegressionPackResponse,
  ComparisonSignal,
} from "@/lib/artifacts/types";
import { cn } from "@/lib/utils";

type HarvestMode = "evolve" | "create";

type WriteResult =
  | { kind: "evolve"; response: ArtifactDatasetEvolutionResponse }
  | { kind: "create"; response: ArtifactRegressionPackResponse };

type HarvestDialogProps = {
  open: boolean;
  onClose: () => void;
  reportId: string;
  dataset: string | null;
  signal: ComparisonSignal;
  recommendation: ArtifactGovernanceRecommendation | null;
  onWritten?: () => void;
};

function suggestedFamilyId(
  recommendation: ArtifactGovernanceRecommendation | null,
  dataset: string | null,
): string {
  if (recommendation) return recommendation.matchedFamily.familyId;
  if (dataset) return `${dataset.replace(/-v\d+$/, "")}-regressions`;
  return "regressions";
}

export function HarvestDialog({
  open,
  onClose,
  reportId,
  dataset,
  signal,
  recommendation,
  onWritten,
}: HarvestDialogProps) {
  const navigate = useNavigate();
  const familyExists = recommendation?.matchedFamily.exists ?? false;
  const [mode, setMode] = useState<HarvestMode>(familyExists ? "evolve" : "create");
  const [familyId, setFamilyId] = useState(() => suggestedFamilyId(recommendation, dataset));
  const [failureType, setFailureType] = useState("");
  const [topN, setTopN] = useState(recommendation?.policy.topN ?? 10);
  const [writing, setWriting] = useState(false);
  const [result, setResult] = useState<WriteResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const panel = panelRef.current;
    const focusables = () =>
      panel
        ? Array.from(
            panel.querySelectorAll<HTMLElement>(
              'button, input, select, textarea, [tabindex]:not([tabindex="-1"])',
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

  const driverTypes = useMemo(
    () =>
      signal.topDrivers
        .filter((driver) => driver.direction === "regression")
        .map((driver) => driver.failureType),
    [signal.topDrivers],
  );

  if (!open) return null;

  const matched = recommendation?.matchedFamily ?? null;
  const selectedCount = recommendation?.selectedCaseCount ?? null;
  const regressedCaseCount = signal.topDrivers
    .filter((driver) => driver.direction === "regression")
    .reduce((total, driver) => total + driver.caseIds.length, 0);

  const write = () => {
    setWriting(true);
    setError(null);
    const request =
      mode === "evolve"
        ? evolveArtifactDataset({
            familyId,
            comparisonId: reportId,
            failureType: failureType || null,
            topN,
          }).then((response) => setResult({ kind: "evolve", response }))
        : createArtifactRegressionPack({
            comparisonId: reportId,
            familyId: familyId || null,
            failureType: failureType || null,
            topN,
          }).then((response) => setResult({ kind: "create", response }));
    void request
      .then(() => onWritten?.())
      .catch((requestError: unknown) => {
        setError(
          requestError instanceof Error ? requestError.message : "harvest write failed",
        );
      })
      .finally(() => setWriting(false));
  };

  const receiptFamilyId = result?.kind === "evolve" ? result.response.familyId : null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Harvest regressions"
      className="fixed inset-0 z-50 grid place-items-center bg-[rgba(20,21,28,0.55)] p-10"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        className="w-[760px] max-w-full overflow-hidden rounded-tok border border-line bg-ground shadow-[0_24px_60px_rgba(15,17,24,0.45)]"
      >
        <div className="flex items-center gap-3.5 border-b border-line px-6 py-[18px]">
          <div>
            <SectionLabel className="tracking-[0.18em]">Harvest</SectionLabel>
            <div className="mt-[5px] font-heading text-[20px] font-semibold">
              {result
                ? "Dataset written"
                : selectedCount != null
                  ? `Promote ${selectedCount} regressed cases`
                  : "Promote regressed cases"}
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
              wrote {result.response.outputPath}
            </div>
            <div className="font-mono text-[12px] leading-relaxed">
              {result.kind === "evolve" ? (
                <>
                  {result.response.datasetId} · version {result.response.versionTag}
                  <br />
                  {result.response.previousCaseCount} inherited + {result.response.addedCaseCount}{" "}
                  added
                  {result.response.duplicateCaseCount > 0
                    ? ` · ${result.response.duplicateCaseCount} duplicates skipped`
                    : ""}{" "}
                  = <span className="font-semibold">{result.response.totalCaseCount} total</span>
                </>
              ) : (
                <>
                  {result.response.datasetId} · draft pack ·{" "}
                  <span className="font-semibold">
                    {result.response.selectedCaseCount} cases
                  </span>
                  <br />
                  suggested family {result.response.suggestedFamilyId} · lifecycle{" "}
                  {result.response.lifecycle ?? "draft"}
                  <br />
                  promote: failure-lab dataset promote {result.response.outputPath}
                </>
              )}
            </div>
            {result.response.previewCases.length > 0 ? (
              <div className="max-h-44 overflow-auto rounded-tok border border-line bg-panel p-3">
                <SectionLabel className="text-[9.5px] tracking-[0.16em]">
                  Cases carried
                </SectionLabel>
                <div className="mt-2 flex flex-col gap-1 font-mono text-[11.5px]">
                  {result.response.previewCases.map((previewCase) => (
                    <div key={previewCase.caseId} className="flex justify-between gap-3">
                      <span>{previewCase.sourceCaseId}</span>
                      <span className="text-muted-ink">
                        {previewCase.driverFailureType ?? previewCase.transitionType}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)_280px]">
            <div className="flex flex-col gap-3.5 px-6 py-5">
              <div>
                <div className="mb-[5px] text-[12px] text-muted-ink">Dataset family</div>
                {familyExists ? (
                  <SegmentedControl
                    aria-label="Dataset family mode"
                    options={[
                      {
                        value: "evolve" as const,
                        label: `Evolve ${matched?.familyId ?? "family"}`,
                      },
                      { value: "create" as const, label: "New draft pack" },
                    ]}
                    value={mode}
                    onChange={setMode}
                  />
                ) : (
                  <div className="w-fit rounded-tok border border-line bg-raised px-3 py-1.5 font-body text-[12.5px]">
                    New draft pack · no matching family yet
                  </div>
                )}
              </div>
              <div>
                <div className="mb-[5px] text-[12px] text-muted-ink">Family id</div>
                <ConsoleInput
                  aria-label="Family id"
                  value={familyId}
                  onChange={(event) => setFamilyId(event.target.value)}
                  title={familyId}
                  className="w-full text-[12px]"
                />
                <div className="mt-1 break-all font-mono text-[10.5px] text-muted-ink">
                  {mode === "evolve" && matched
                    ? `datasets/${familyId}-v${(matched.versionCount ?? 0) + 1}.json`
                    : `datasets/${familyId}.json`}
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <div className="mb-[5px] text-[12px] text-muted-ink">Failure type</div>
                  <select
                    aria-label="Failure type filter"
                    value={failureType}
                    onChange={(event) => setFailureType(event.target.value)}
                    className="w-full rounded-tok border border-line bg-raised px-[10px] py-[7px] font-mono text-[12px] text-ink focus:border-accent focus:outline-none"
                  >
                    <option value="">all regressed types</option>
                    {driverTypes.map((driverType) => (
                      <option key={driverType} value={driverType}>
                        {driverType}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="w-24">
                  <div className="mb-[5px] text-[12px] text-muted-ink">Top N</div>
                  <ConsoleInput
                    aria-label="Top N cases"
                    type="number"
                    min={1}
                    max={regressedCaseCount || undefined}
                    value={topN}
                    onChange={(event) => setTopN(Number(event.target.value) || 1)}
                    className="w-full"
                  />
                  {regressedCaseCount > 0 ? (
                    <div className="mt-1 font-mono text-[10.5px] text-muted-ink">
                      of {regressedCaseCount} regressed
                    </div>
                  ) : null}
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <div className="mb-[5px] text-[12px] text-muted-ink">Lifecycle</div>
                  <div className="rounded-tok border border-line bg-raised px-[10px] py-2 font-mono text-[13px]">
                    draft
                  </div>
                </div>
                <div className="flex-1">
                  <div className="mb-[5px] text-[12px] text-muted-ink">Gate future runs</div>
                  <div className="rounded-tok border border-line bg-raised px-[10px] py-2 font-mono text-[13px]">
                    severity &gt;{" "}
                    {recommendation
                      ? recommendation.policy.minimumSeverity.toFixed(2)
                      : "0.05"}
                  </div>
                </div>
              </div>
              {error ? (
                <div className="rounded-tok border border-line bg-warn-bg px-3 py-2.5 font-mono text-[11.5px] text-warn">
                  {error}
                  <br />
                  run: failure-lab dataset evolve {familyId} --comparison {reportId}
                </div>
              ) : null}
            </div>

            <div className="flex flex-col gap-3 border-l border-line bg-panel p-5">
              <SectionLabel className="text-[9.5px] tracking-[0.16em]">
                Carrying forward
              </SectionLabel>
              {matched ? (
                <div className="font-mono text-[12px] leading-[1.9]">
                  {matched.proposedAdditionCount} selected cases
                  <br />
                  {matched.currentCaseCount} inherited
                  {matched.latestDatasetId ? ` from ${matched.latestDatasetId}` : ""}
                  <br />
                  <span className="font-semibold">
                    {matched.projectedCaseCount} total
                  </span>
                  {matched.duplicateCaseCount > 0 ? (
                    <>
                      <br />
                      <span className="text-muted-ink">
                        {matched.duplicateCaseCount} duplicates skipped
                      </span>
                    </>
                  ) : null}
                </div>
              ) : (
                <div className="font-mono text-[12px] leading-[1.9] text-muted-ink">
                  counts known after write
                </div>
              )}
              <div className="border-t border-line pt-2.5 font-mono text-[11.5px] leading-[1.9] text-muted-ink">
                {signal.topDrivers
                  .filter((driver) => driver.direction === "regression")
                  .map((driver) => (
                    <div key={driver.failureType}>
                      {driver.failureType} {driver.caseIds.length}
                    </div>
                  ))}
                <div>severity {formatScore(signal.severity)}</div>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 border-t border-line px-6 py-3.5">
          <span className="mr-auto font-mono text-[11px] text-muted-ink">
            {result
              ? `${result.response.outputPath} · immutable`
              : `writes datasets/${
                  mode === "evolve" && matched
                    ? `${familyId}-v${(matched.versionCount ?? 0) + 1}`
                    : familyId
                }.json · deterministic write · no network`}
          </span>
          {result ? (
            <>
              {receiptFamilyId ? (
                <ConsoleButton
                  onClick={() => {
                    onClose();
                    navigate(`/datasets/${encodeURIComponent(receiptFamilyId)}`);
                  }}
                >
                  Open family
                </ConsoleButton>
              ) : (
                <ConsoleButton
                  onClick={() => {
                    onClose();
                    navigate("/datasets");
                  }}
                >
                  View drafts
                </ConsoleButton>
              )}
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
                disabled={writing || !familyId}
                className={cn(writing && "opacity-60")}
              >
                {writing
                  ? "Writing…"
                  : mode === "evolve"
                    ? `Write v${(matched?.versionCount ?? 0) + 1}`
                    : "Write draft pack"}
              </ConsoleButton>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
