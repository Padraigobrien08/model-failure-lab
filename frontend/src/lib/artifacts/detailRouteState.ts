import type {
  ComparisonCaseDeltaRecord,
  ComparisonTransitionSummaryRow,
  RunCaseLensKey,
  RunDetail,
} from "@/lib/artifacts/types";

export const RUN_DETAIL_SECTIONS = [
  { id: "identity", label: "Run identity" },
  { id: "shape", label: "Failure shape" },
  { id: "diagnosis", label: "Why it failed" },
  { id: "notable", label: "Notable cases" },
  { id: "evidence", label: "Selected evidence" },
] as const;

export const COMPARISON_DETAIL_SECTIONS = [
  { id: "framing", label: "Comparison framing" },
  { id: "coverage", label: "Scope and compatibility" },
  { id: "transitions", label: "Transition evidence" },
] as const;

export type RunDetailSectionKey = (typeof RUN_DETAIL_SECTIONS)[number]["id"];
export type ComparisonDetailSectionKey =
  (typeof COMPARISON_DETAIL_SECTIONS)[number]["id"];

export type RunDetailSearchState = {
  section: RunDetailSectionKey | null;
  lens: RunCaseLensKey | null;
  caseId: string | null;
};

export type ComparisonDetailSearchState = {
  section: ComparisonDetailSectionKey | null;
  caseId: string | null;
  transition: string | null;
};

const RUN_DETAIL_SECTION_SET = new Set<string>(
  RUN_DETAIL_SECTIONS.map((section) => section.id),
);
const COMPARISON_DETAIL_SECTION_SET = new Set<string>(
  COMPARISON_DETAIL_SECTIONS.map((section) => section.id),
);
const RUN_CASE_LENS_SET = new Set<RunCaseLensKey>([
  "mismatches",
  "notable",
  "all",
  "errors",
]);
const RUN_CASE_LENS_ORDER: RunCaseLensKey[] = [
  "mismatches",
  "notable",
  "all",
  "errors",
];

function readSearchValue(searchParams: URLSearchParams, key: string): string | null {
  const value = searchParams.get(key);
  if (value === null) {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function setSearchValue(
  searchParams: URLSearchParams,
  key: string,
  value: string | null | undefined,
) {
  if (value === null || value === undefined || value.trim().length === 0) {
    searchParams.delete(key);
    return;
  }

  searchParams.set(key, value);
}

export function parseRunDetailSearch(
  searchParams: URLSearchParams,
): RunDetailSearchState {
  const section = readSearchValue(searchParams, "section");
  const lens = readSearchValue(searchParams, "lens");

  return {
    section:
      section !== null && RUN_DETAIL_SECTION_SET.has(section)
        ? (section as RunDetailSectionKey)
        : null,
    lens:
      lens !== null && RUN_CASE_LENS_SET.has(lens as RunCaseLensKey)
        ? (lens as RunCaseLensKey)
        : null,
    caseId: readSearchValue(searchParams, "case"),
  };
}

export function parseComparisonDetailSearch(
  searchParams: URLSearchParams,
): ComparisonDetailSearchState {
  const section = readSearchValue(searchParams, "section");

  return {
    section:
      section !== null && COMPARISON_DETAIL_SECTION_SET.has(section)
        ? (section as ComparisonDetailSectionKey)
        : null,
    caseId: readSearchValue(searchParams, "case"),
    transition: readSearchValue(searchParams, "transition"),
  };
}

export function buildRunDetailSearchParams(
  current: URLSearchParams,
  patch: Partial<RunDetailSearchState>,
): URLSearchParams {
  const next = new URLSearchParams(current);
  setSearchValue(next, "section", patch.section);
  setSearchValue(next, "lens", patch.lens);
  setSearchValue(next, "case", patch.caseId);
  return next;
}

export function buildComparisonDetailSearchParams(
  current: URLSearchParams,
  patch: Partial<ComparisonDetailSearchState>,
): URLSearchParams {
  const next = new URLSearchParams(current);
  setSearchValue(next, "section", patch.section);
  setSearchValue(next, "case", patch.caseId);
  setSearchValue(next, "transition", patch.transition);
  return next;
}

export function searchParamsEqual(left: URLSearchParams, right: URLSearchParams): boolean {
  return left.toString() === right.toString();
}

export function resolveRunDetailSection(
  requestedSection: RunDetailSectionKey | null,
  requestedLens: RunCaseLensKey | null,
  requestedCaseId: string | null,
): RunDetailSectionKey {
  if (requestedSection !== null) {
    return requestedSection;
  }

  if (requestedLens !== null || requestedCaseId !== null) {
    return "evidence";
  }

  return "identity";
}

export function resolveComparisonDetailSection(
  requestedSection: ComparisonDetailSectionKey | null,
  requestedCaseId: string | null,
  requestedTransition: string | null,
): ComparisonDetailSectionKey {
  if (requestedSection !== null) {
    return requestedSection;
  }

  if (requestedCaseId !== null || requestedTransition !== null) {
    return "transitions";
  }

  return "framing";
}

function lensCaseIds(detail: RunDetail, lens: RunCaseLensKey): string[] {
  if (lens === "mismatches") {
    return detail.lenses.mismatchCaseIds;
  }

  if (lens === "notable") {
    return detail.lenses.notableCaseIds;
  }

  if (lens === "errors") {
    return detail.lenses.errorCaseIds;
  }

  return detail.lenses.allCaseIds;
}

export function resolveRunLensForCase(
  detail: RunDetail,
  caseId: string | null,
): RunCaseLensKey | null {
  if (caseId === null) {
    return null;
  }

  for (const lens of RUN_CASE_LENS_ORDER) {
    if (lensCaseIds(detail, lens).includes(caseId)) {
      return lens;
    }
  }

  return null;
}

export function resolveComparisonCaseForTransition(
  summary: ComparisonTransitionSummaryRow[],
  caseDeltas: ComparisonCaseDeltaRecord[],
  transition: string | null,
): ComparisonCaseDeltaRecord | null {
  if (transition === null) {
    return null;
  }

  const matchingGroup = summary.find((group) => group.transitionType === transition);
  if (!matchingGroup) {
    return null;
  }

  const caseMap = new Map(caseDeltas.map((caseRow) => [caseRow.caseId, caseRow]));
  for (const caseId of matchingGroup.caseIds) {
    const caseRow = caseMap.get(caseId);
    if (caseRow) {
      return caseRow;
    }
  }

  return null;
}
