import { loadArtifactJson } from "@/lib/manifest/load";
import { getReportEntityByScope } from "@/lib/manifest/selectors";
import type {
  ArtifactIndex,
  FinalRobustnessBundle,
  FinalRobustnessReportData,
  FinalRobustnessReportSummary,
  ReportEntity,
} from "@/lib/manifest/types";

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function requireArray<T>(value: unknown, label: string): T[] {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array.`);
  }

  return value as T[];
}

function validateFinalRobustnessReportData(payload: unknown): FinalRobustnessReportData {
  if (!isObject(payload)) {
    throw new Error("Final robustness report data must be an object.");
  }

  return {
    official_method_summaries: requireArray(payload.official_method_summaries, "official_method_summaries"),
    exploratory_method_summaries: requireArray(
      payload.exploratory_method_summaries,
      "exploratory_method_summaries",
    ),
    worst_group_summary: requireArray(payload.worst_group_summary, "worst_group_summary"),
    ood_summary: requireArray(payload.ood_summary, "ood_summary"),
    id_summary: requireArray(payload.id_summary, "id_summary"),
    calibration_summary: requireArray(payload.calibration_summary, "calibration_summary"),
    final_robustness_verdict:
      typeof payload.final_robustness_verdict === "string"
        ? payload.final_robustness_verdict
        : undefined,
    promotion_audit: isObject(payload.promotion_audit)
      ? (payload.promotion_audit as FinalRobustnessReportData["promotion_audit"])
      : undefined,
  };
}

function validateFinalRobustnessReportSummary(payload: unknown): FinalRobustnessReportSummary {
  if (!isObject(payload)) {
    throw new Error("Final robustness report summary must be an object.");
  }

  return {
    final_robustness_verdict:
      typeof payload.final_robustness_verdict === "string"
        ? payload.final_robustness_verdict
        : undefined,
    headline_findings: requireArray(payload.headline_findings, "headline_findings"),
    key_takeaway: typeof payload.key_takeaway === "string" ? payload.key_takeaway : undefined,
    next_step: typeof payload.next_step === "string" ? payload.next_step : undefined,
    official_methods: requireArray(payload.official_methods, "official_methods"),
    exploratory_methods: requireArray(payload.exploratory_methods, "exploratory_methods"),
  };
}

function requireRefPath(report: ReportEntity, key: "report_data_json" | "report_summary_json") {
  const ref = report.payload_refs?.[key] ?? report.artifact_refs?.[key];
  if (
    typeof ref !== "object" ||
    ref === null ||
    !("path" in ref) ||
    typeof ref.path !== "string"
  ) {
    throw new Error(`Report ${report.id} is missing ${key}.`);
  }

  return ref.path;
}

export async function loadFinalRobustnessBundle(
  index: ArtifactIndex,
  fetchImpl: typeof fetch = fetch,
): Promise<FinalRobustnessBundle> {
  const report = getReportEntityByScope(index, "phase26_robustness_final");
  if (!report) {
    throw new Error("The manifest does not expose the official final robustness report.");
  }

  const [dataPayload, summaryPayload] = await Promise.all([
    loadArtifactJson(requireRefPath(report, "report_data_json"), fetchImpl),
    loadArtifactJson(requireRefPath(report, "report_summary_json"), fetchImpl),
  ]);

  return {
    report,
    data: validateFinalRobustnessReportData(dataPayload),
    summary: validateFinalRobustnessReportSummary(summaryPayload),
  };
}
