import type { TraceScope } from "@/app/scope";

export type LaneRouteLaneId = "robustness" | "calibration";

export type LaneRouteMethodId =
  | "baseline"
  | "reweighting"
  | "temperature_scaling"
  | "group_dro";

export type LaneRouteStatus = "stable" | "mixed" | "failure";

export type LaneRouteRowScope = "official" | "exploratory";

export type LaneRouteTableColumnKey =
  | "method"
  | "status"
  | "worst_group"
  | "ood"
  | "id"
  | "ece"
  | "brier"
  | "delta_vs_baseline";

export type LaneRouteTableColumn = {
  key: LaneRouteTableColumnKey;
  label: string;
  align?: "left" | "right";
};

export type LaneRouteEvidenceLink = {
  label: string;
  path: string;
};

export type LaneRouteProvenanceField = {
  label: string;
  value: string;
  mono?: boolean;
};

export type LaneRouteRunRow = {
  entityId: string;
  runId: string;
  seed: number;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  keyMetricLabel: string;
  keyMetricValue: number;
  deltaVsBaseline: number | null;
  evidenceLinks: LaneRouteEvidenceLink[];
  provenance: LaneRouteProvenanceField[];
};

export type LaneRouteMethodRow = {
  entityId: string;
  methodId: LaneRouteMethodId;
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  summary: string;
  deltaVsBaseline: number | null;
  lowerIsBetter?: boolean;
  metrics: {
    worstGroup?: number;
    ood?: number;
    id?: number;
    ece?: number;
    brier?: number;
  };
  runs: LaneRouteRunRow[];
  evidenceLinks: LaneRouteEvidenceLink[];
  provenance: LaneRouteProvenanceField[];
};

export type LaneRouteSelection =
  | {
      entityType: "method";
      entityId: string;
    }
  | {
      entityType: "run";
      entityId: string;
    };

export type LaneRouteInspectorEntity = {
  entityId: string;
  entityType: "Method" | "Run";
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  summary: string;
  evidenceLinks: LaneRouteEvidenceLink[];
  provenance: LaneRouteProvenanceField[];
};

export type LaneRouteModel = {
  laneId: LaneRouteLaneId;
  question: string;
  label: string;
  status: LaneRouteStatus;
  summary: string;
  statusModifier?: string;
  scopeNote?: string;
  columns: LaneRouteTableColumn[];
  officialRows: LaneRouteMethodRow[];
  exploratoryRows: LaneRouteMethodRow[];
  rows: LaneRouteMethodRow[];
};

const ROBUSTNESS_COLUMNS: LaneRouteTableColumn[] = [
  { key: "method", label: "Method", align: "left" },
  { key: "status", label: "Status", align: "left" },
  { key: "worst_group", label: "Worst-group", align: "right" },
  { key: "ood", label: "OOD", align: "right" },
  { key: "id", label: "ID", align: "right" },
  { key: "delta_vs_baseline", label: "Delta vs baseline", align: "right" },
];

const CALIBRATION_COLUMNS: LaneRouteTableColumn[] = [
  { key: "method", label: "Method", align: "left" },
  { key: "status", label: "Status", align: "left" },
  { key: "ece", label: "ECE", align: "right" },
  { key: "brier", label: "Brier", align: "right" },
  { key: "delta_vs_baseline", label: "Delta vs baseline", align: "right" },
];

function buildEvidenceLinks(entityStem: string): LaneRouteEvidenceLink[] {
  return [
    { label: "Report", path: `/mock-artifacts/${entityStem}/report.md` },
    { label: "Eval bundle", path: `/mock-artifacts/${entityStem}/eval_bundle.json` },
    { label: "Metadata", path: `/mock-artifacts/${entityStem}/metadata.json` },
  ];
}

function buildRobustnessRun(
  methodId: LaneRouteMethodId,
  seed: number,
  status: LaneRouteStatus,
  value: number,
  deltaVsBaseline: number | null,
  scope: LaneRouteRowScope = "official",
): LaneRouteRunRow {
  const runId = `distilbert_${methodId}_seed_${seed}`;
  const entityId = `run_${runId}`;

  return {
    entityId,
    runId,
    seed,
    status,
    scope,
    keyMetricLabel: "Worst-group",
    keyMetricValue: value,
    deltaVsBaseline,
    evidenceLinks: buildEvidenceLinks(runId),
    provenance: [
      { label: "Source path", value: `artifacts/mock/runs/${runId}/metrics.json`, mono: true },
      { label: "Lane", value: "robustness" },
      { label: "Method", value: methodId },
    ],
  };
}

function buildCalibrationRun(
  methodId: LaneRouteMethodId,
  seed: number,
  status: LaneRouteStatus,
  value: number,
  deltaVsBaseline: number | null,
  scope: LaneRouteRowScope = "official",
): LaneRouteRunRow {
  const runId = `distilbert_${methodId}_seed_${seed}`;
  const entityId = `run_${runId}`;

  return {
    entityId,
    runId,
    seed,
    status,
    scope,
    keyMetricLabel: "ECE",
    keyMetricValue: value,
    deltaVsBaseline,
    evidenceLinks: buildEvidenceLinks(runId),
    provenance: [
      { label: "Source path", value: `artifacts/mock/runs/${runId}/calibration.json`, mono: true },
      { label: "Lane", value: "calibration" },
      { label: "Method", value: methodId },
    ],
  };
}

const laneRouteBaseSnapshot: Record<
  LaneRouteLaneId,
  Omit<LaneRouteModel, "rows"> & { rows: LaneRouteMethodRow[] }
> = {
  robustness: {
    laneId: "robustness",
    question: "What is happening in this lane?",
    label: "Robustness",
    status: "mixed",
    summary:
      "Reweighting improves worst-group behavior, but the official lane still carries OOD and ID tradeoffs.",
    columns: ROBUSTNESS_COLUMNS,
    rows: [
      {
        entityId: "method_baseline_robustness",
        methodId: "baseline",
        label: "Baseline",
        status: "mixed",
        scope: "official",
        summary:
          "Reference method for the lane. The gap is visible without ambiguity, but the worst-group floor is still low.",
        deltaVsBaseline: 0,
        metrics: {
          worstGroup: 0.416,
          ood: 0.639,
          id: 0.742,
        },
        runs: [
          buildRobustnessRun("baseline", 13, "mixed", 0.416, 0),
          buildRobustnessRun("baseline", 42, "mixed", 0.421, 0.005),
          buildRobustnessRun("baseline", 87, "mixed", 0.408, -0.008),
        ],
        evidenceLinks: buildEvidenceLinks("baseline_robustness"),
        provenance: [
          { label: "Source path", value: "artifacts/mock/lanes/robustness/baseline.json", mono: true },
          {
            label: "Related IDs",
            value: "run_distilbert_baseline_seed_13, run_distilbert_baseline_seed_42",
          },
        ],
      },
      {
        entityId: "method_reweighting_robustness",
        methodId: "reweighting",
        label: "Reweighting",
        status: "mixed",
        scope: "official",
        summary:
          "Best official robustness method so far, but the gain is still paired with weaker OOD and ID behavior.",
        deltaVsBaseline: 0.061,
        metrics: {
          worstGroup: 0.477,
          ood: 0.621,
          id: 0.734,
        },
        runs: [
          buildRobustnessRun("reweighting", 13, "mixed", 0.477, 0.061),
          buildRobustnessRun("reweighting", 42, "mixed", 0.468, 0.052),
          buildRobustnessRun("reweighting", 87, "mixed", 0.472, 0.056),
        ],
        evidenceLinks: buildEvidenceLinks("reweighting_robustness"),
        provenance: [
          { label: "Source path", value: "artifacts/mock/lanes/robustness/reweighting.json", mono: true },
          {
            label: "Related IDs",
            value: "run_distilbert_reweighting_seed_13, run_distilbert_reweighting_seed_42",
          },
        ],
      },
      {
        entityId: "method_temperature_scaling_robustness",
        methodId: "temperature_scaling",
        label: "Temperature Scaling",
        status: "mixed",
        scope: "official",
        summary:
          "Keeps the calibration story tidy, but barely moves the robustness lane from the baseline reference.",
        deltaVsBaseline: 0.009,
        metrics: {
          worstGroup: 0.425,
          ood: 0.634,
          id: 0.741,
        },
        runs: [
          buildRobustnessRun("temperature_scaling", 13, "mixed", 0.425, 0.009),
          buildRobustnessRun("temperature_scaling", 42, "mixed", 0.423, 0.007),
        ],
        evidenceLinks: buildEvidenceLinks("temperature_scaling_robustness"),
        provenance: [
          {
            label: "Source path",
            value: "artifacts/mock/lanes/robustness/temperature_scaling.json",
            mono: true,
          },
          { label: "Related IDs", value: "run_distilbert_temperature_scaling_seed_13" },
        ],
      },
      {
        entityId: "method_group_dro_robustness",
        methodId: "group_dro",
        label: "Group DRO",
        status: "failure",
        scope: "exploratory",
        summary: "Exploratory challenger that regressed the baseline and never cleared the promotion bar.",
        deltaVsBaseline: -0.215,
        metrics: {
          worstGroup: 0.201,
          ood: 0.517,
          id: 0.688,
        },
        runs: [buildRobustnessRun("group_dro", 13, "failure", 0.201, -0.215, "exploratory")],
        evidenceLinks: buildEvidenceLinks("group_dro_robustness"),
        provenance: [
          { label: "Source path", value: "artifacts/mock/lanes/robustness/group_dro.json", mono: true },
          { label: "Related IDs", value: "run_distilbert_group_dro_seed_13" },
        ],
      },
    ],
  },
  calibration: {
    laneId: "calibration",
    question: "What is happening in this lane?",
    label: "Calibration",
    status: "stable",
    summary:
      "Temperature scaling remains the clearest official lane win and keeps the calibration story easy to trust.",
    columns: CALIBRATION_COLUMNS,
    rows: [
      {
        entityId: "method_baseline_calibration",
        methodId: "baseline",
        label: "Baseline",
        status: "mixed",
        scope: "official",
        summary:
          "Reference confidence behavior before mitigation. Error is understandable, but not tight enough to trust by default.",
        deltaVsBaseline: 0,
        lowerIsBetter: true,
        metrics: {
          ece: 0.077,
          brier: 0.211,
        },
        runs: [
          buildCalibrationRun("baseline", 13, "mixed", 0.077, 0),
          buildCalibrationRun("baseline", 42, "mixed", 0.074, -0.003),
          buildCalibrationRun("baseline", 87, "mixed", 0.079, 0.002),
        ],
        evidenceLinks: buildEvidenceLinks("baseline_calibration"),
        provenance: [
          { label: "Source path", value: "artifacts/mock/lanes/calibration/baseline.json", mono: true },
          {
            label: "Related IDs",
            value: "run_distilbert_baseline_seed_13, run_distilbert_baseline_seed_42",
          },
        ],
      },
      {
        entityId: "method_temperature_scaling_calibration",
        methodId: "temperature_scaling",
        label: "Temperature Scaling",
        status: "stable",
        scope: "official",
        summary:
          "Cleanest official mitigation. Calibration improves without complicating the interpretation.",
        deltaVsBaseline: -0.036,
        lowerIsBetter: true,
        metrics: {
          ece: 0.041,
          brier: 0.189,
        },
        runs: [
          buildCalibrationRun("temperature_scaling", 13, "stable", 0.041, -0.036),
          buildCalibrationRun("temperature_scaling", 42, "stable", 0.044, -0.03),
          buildCalibrationRun("temperature_scaling", 87, "stable", 0.043, -0.031),
        ],
        evidenceLinks: buildEvidenceLinks("temperature_scaling_calibration"),
        provenance: [
          {
            label: "Source path",
            value: "artifacts/mock/lanes/calibration/temperature_scaling.json",
            mono: true,
          },
          {
            label: "Related IDs",
            value: "run_distilbert_temperature_scaling_seed_13, run_distilbert_temperature_scaling_seed_42",
          },
        ],
      },
      {
        entityId: "method_reweighting_calibration",
        methodId: "reweighting",
        label: "Reweighting",
        status: "mixed",
        scope: "official",
        summary:
          "Retains some calibration improvement, but not as cleanly or consistently as temperature scaling.",
        deltaVsBaseline: -0.019,
        lowerIsBetter: true,
        metrics: {
          ece: 0.058,
          brier: 0.201,
        },
        runs: [
          buildCalibrationRun("reweighting", 13, "mixed", 0.058, -0.019),
          buildCalibrationRun("reweighting", 42, "mixed", 0.062, -0.015),
          buildCalibrationRun("reweighting", 87, "mixed", 0.057, -0.02),
        ],
        evidenceLinks: buildEvidenceLinks("reweighting_calibration"),
        provenance: [
          { label: "Source path", value: "artifacts/mock/lanes/calibration/reweighting.json", mono: true },
          {
            label: "Related IDs",
            value: "run_distilbert_reweighting_seed_13, run_distilbert_reweighting_seed_42",
          },
        ],
      },
      {
        entityId: "method_group_dro_calibration",
        methodId: "group_dro",
        label: "Group DRO",
        status: "failure",
        scope: "exploratory",
        summary:
          "Exploratory mitigation that made calibration worse and stayed outside the official evidence path.",
        deltaVsBaseline: 0.036,
        lowerIsBetter: true,
        metrics: {
          ece: 0.113,
          brier: 0.238,
        },
        runs: [buildCalibrationRun("group_dro", 13, "failure", 0.113, 0.036, "exploratory")],
        evidenceLinks: buildEvidenceLinks("group_dro_calibration"),
        provenance: [
          { label: "Source path", value: "artifacts/mock/lanes/calibration/group_dro.json", mono: true },
          { label: "Related IDs", value: "run_distilbert_group_dro_seed_13" },
        ],
      },
    ],
  },
};

export function normalizeLaneRouteLaneId(value: string | undefined): LaneRouteLaneId {
  return value === "calibration" ? "calibration" : "robustness";
}

export function buildLaneRouteModel(
  laneId: string | undefined,
  scope: TraceScope,
): LaneRouteModel {
  const normalizedLaneId = normalizeLaneRouteLaneId(laneId);
  const lane = laneRouteBaseSnapshot[normalizedLaneId];
  const officialRows = lane.rows.filter((row) => row.scope === "official");
  const exploratoryRows = scope === "all" ? lane.rows.filter((row) => row.scope === "exploratory") : [];
  const rows = [...officialRows, ...exploratoryRows];

  return {
    ...lane,
    statusModifier: exploratoryRows.length > 0 ? "Exploratory in view" : undefined,
    scopeNote:
      exploratoryRows.length > 0
        ? "Exploratory methods are visible below. Official lane status remains canonical."
        : undefined,
    officialRows,
    exploratoryRows,
    rows,
  };
}

export function getDefaultLaneSelection(model: LaneRouteModel): LaneRouteSelection {
  return {
    entityType: "method",
    entityId: model.rows[0]?.entityId ?? "method_missing",
  };
}

export function resolveLaneSelection(
  model: LaneRouteModel,
  selection: LaneRouteSelection | null,
): LaneRouteSelection {
  if (!selection) {
    return getDefaultLaneSelection(model);
  }

  const method = model.rows.find((row) => row.entityId === selection.entityId);
  if (selection.entityType === "method" && method) {
    return selection;
  }

  const run = model.rows.flatMap((row) => row.runs).find((row) => row.entityId === selection.entityId);
  if (selection.entityType === "run" && run) {
    return selection;
  }

  return getDefaultLaneSelection(model);
}

export function getLaneInspectorEntity(
  model: LaneRouteModel,
  selection: LaneRouteSelection,
): LaneRouteInspectorEntity {
  if (selection.entityType === "run") {
    for (const row of model.rows) {
      const run = row.runs.find((candidate) => candidate.entityId === selection.entityId);
      if (run) {
        return {
          entityId: run.entityId,
          entityType: "Run",
          label: run.runId,
          status: run.status,
          scope: run.scope,
          summary: `${row.label} seed ${run.seed} for the ${model.label.toLowerCase()} lane.`,
          evidenceLinks: run.evidenceLinks,
          provenance: run.provenance,
        };
      }
    }
  }

  const method = model.rows.find((row) => row.entityId === selection.entityId) ?? model.rows[0];

  return {
    entityId: method.entityId,
    entityType: "Method",
    label: method.label,
    status: method.status,
    scope: method.scope,
    summary: method.summary,
    evidenceLinks: method.evidenceLinks,
    provenance: method.provenance,
  };
}
