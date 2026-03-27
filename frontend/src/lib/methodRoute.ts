import type { TraceScope } from "@/app/scope";
import type {
  LaneRouteLaneId,
  LaneRouteMethodId,
  LaneRouteRowScope,
  LaneRouteStatus,
} from "@/lib/laneRoute";

export type MethodRouteLaneId = LaneRouteLaneId;

export type MethodRouteMetric = {
  label: string;
  value: number;
  deltaVsBaseline: number | null;
  lowerIsBetter?: boolean;
};

export type MethodRouteRunMetric = {
  label: string;
  value: number;
  lowerIsBetter?: boolean;
};

export type MethodRouteEvidenceLink = {
  label: string;
  path: string;
};

export type MethodRouteProvenanceField = {
  label: string;
  value: string;
  mono?: boolean;
};

export type MethodRouteRunRow = {
  entityId: string;
  runId: string;
  seed: number;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  metrics: MethodRouteRunMetric[];
  evidenceLinks: MethodRouteEvidenceLink[];
  provenance: MethodRouteProvenanceField[];
};

export type MethodRouteExplanationSection = {
  title: "What improved" | "What regressed" | "Reason for status";
  bullets: string[];
};

export type MethodRouteLineage = {
  parentLabel: string;
  parentPath: string;
  currentLabel: string;
  childRuns: Array<{
    label: string;
    path: string;
  }>;
};

export type MethodRouteInspectorEntity = {
  entityId: string;
  entityType: "Run";
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  summary: string;
  evidenceLinks: MethodRouteEvidenceLink[];
  provenance: MethodRouteProvenanceField[];
};

export type MethodRouteReadyModel = {
  state: "ready";
  question: string;
  laneId: LaneRouteLaneId;
  laneLabel: string;
  methodId: LaneRouteMethodId;
  methodLabel: string;
  status: LaneRouteStatus;
  summary: string;
  scope: LaneRouteRowScope;
  statusModifier?: string;
  scopeNote?: string;
  metricStrip: MethodRouteMetric[];
  officialRuns: MethodRouteRunRow[];
  exploratoryRuns: MethodRouteRunRow[];
  runs: MethodRouteRunRow[];
  defaultRunEntityId: string;
  explanation: MethodRouteExplanationSection[];
  lineage: MethodRouteLineage;
};

export type MethodRouteScopeHiddenModel = {
  state: "scope-hidden";
  question: string;
  laneId: LaneRouteLaneId;
  laneLabel: string;
  methodId: LaneRouteMethodId;
  methodLabel: string;
  status: LaneRouteStatus;
  summary: string;
  scope: LaneRouteRowScope;
  message: string;
  recoveryPath: string;
};

export type MethodRouteModel = MethodRouteReadyModel | MethodRouteScopeHiddenModel;

type MethodRouteMethodSnapshot = {
  methodId: LaneRouteMethodId;
  methodLabel: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  summary: string;
  metricStrip: MethodRouteMetric[];
  runs: MethodRouteRunRow[];
  explanation: MethodRouteExplanationSection[];
  lineage: MethodRouteLineage;
};

type MethodRouteLaneSnapshot = {
  laneId: LaneRouteLaneId;
  laneLabel: string;
  methods: MethodRouteMethodSnapshot[];
};

function buildEvidenceLinks(entityStem: string): MethodRouteEvidenceLink[] {
  return [
    { label: "Report", path: `/mock-artifacts/${entityStem}/report.md` },
    { label: "Eval bundle", path: `/mock-artifacts/${entityStem}/eval_bundle.json` },
    { label: "Metadata", path: `/mock-artifacts/${entityStem}/metadata.json` },
  ];
}

function buildRunProvenance(
  laneId: LaneRouteLaneId,
  methodId: LaneRouteMethodId,
  runId: string,
): MethodRouteProvenanceField[] {
  return [
    { label: "Source path", value: `artifacts/mock/runs/${runId}/metadata.json`, mono: true },
    { label: "Lane", value: laneId },
    { label: "Method", value: methodId },
  ];
}

function buildRobustnessRun(
  methodId: LaneRouteMethodId,
  seed: number,
  status: LaneRouteStatus,
  worstGroup: number,
  ood: number,
  id: number,
  scope: LaneRouteRowScope = "official",
): MethodRouteRunRow {
  const runId = `distilbert_${methodId}_seed_${seed}`;

  return {
    entityId: `run_${runId}`,
    runId,
    seed,
    status,
    scope,
    metrics: [
      { label: "Worst-group", value: worstGroup },
      { label: "OOD", value: ood },
      { label: "ID", value: id },
    ],
    evidenceLinks: buildEvidenceLinks(runId),
    provenance: buildRunProvenance("robustness", methodId, runId),
  };
}

function buildCalibrationRun(
  methodId: LaneRouteMethodId,
  seed: number,
  status: LaneRouteStatus,
  ece: number,
  brier: number,
  scope: LaneRouteRowScope = "official",
): MethodRouteRunRow {
  const runId = `distilbert_${methodId}_seed_${seed}`;

  return {
    entityId: `run_${runId}`,
    runId,
    seed,
    status,
    scope,
    metrics: [
      { label: "ECE", value: ece, lowerIsBetter: true },
      { label: "Brier", value: brier, lowerIsBetter: true },
    ],
    evidenceLinks: buildEvidenceLinks(runId),
    provenance: buildRunProvenance("calibration", methodId, runId),
  };
}

const METHOD_ROUTE_SNAPSHOT: Record<LaneRouteLaneId, MethodRouteLaneSnapshot> = {
  robustness: {
    laneId: "robustness",
    laneLabel: "Robustness",
    methods: [
      {
        methodId: "baseline",
        methodLabel: "Baseline",
        status: "mixed",
        scope: "official",
        summary:
          "Reference method for the robustness lane. It keeps the gap legible, but the worst-group floor remains too low to trust.",
        metricStrip: [
          { label: "Worst-group", value: 0.416, deltaVsBaseline: 0 },
          { label: "OOD", value: 0.639, deltaVsBaseline: 0 },
          { label: "ID", value: 0.742, deltaVsBaseline: 0 },
        ],
        runs: [
          buildRobustnessRun("baseline", 13, "mixed", 0.416, 0.639, 0.742),
          buildRobustnessRun("baseline", 42, "mixed", 0.421, 0.642, 0.743),
          buildRobustnessRun("baseline", 87, "mixed", 0.408, 0.634, 0.739),
        ],
        explanation: [
          {
            title: "What improved",
            bullets: ["No mitigation uplift here; this route exists as the baseline anchor for later comparisons."],
          },
          {
            title: "What regressed",
            bullets: [
              "Worst-group F1 stays at the lane floor, which is why the remaining robustness gap is still easy to see.",
            ],
          },
          {
            title: "Reason for status",
            bullets: ["The method is mixed because it is stable enough to interpret, but not strong enough to resolve the robustness story."],
          },
        ],
        lineage: {
          parentLabel: "Summary -> Robustness baseline",
          parentPath: "/lane/robustness",
          currentLabel: "Baseline",
          childRuns: [
            { label: "Seed 13", path: "/run/distilbert_baseline_seed_13" },
            { label: "Seed 42", path: "/run/distilbert_baseline_seed_42" },
            { label: "Seed 87", path: "/run/distilbert_baseline_seed_87" },
          ],
        },
      },
      {
        methodId: "reweighting",
        methodLabel: "Reweighting",
        status: "mixed",
        scope: "official",
        summary:
          "Best current robustness lane. It lifts worst-group behavior, but the gain is still paired with OOD and ID tradeoffs.",
        metricStrip: [
          { label: "Worst-group", value: 0.477, deltaVsBaseline: 0.061 },
          { label: "OOD", value: 0.621, deltaVsBaseline: -0.018 },
          { label: "ID", value: 0.734, deltaVsBaseline: -0.008 },
        ],
        runs: [
          buildRobustnessRun("reweighting", 13, "mixed", 0.477, 0.621, 0.734),
          buildRobustnessRun("reweighting", 42, "mixed", 0.468, 0.626, 0.736),
          buildRobustnessRun("reweighting", 87, "mixed", 0.472, 0.623, 0.735),
        ],
        explanation: [
          {
            title: "What improved",
            bullets: [
              "Worst-group performance moved up over baseline across the seeded runs.",
              "The lane is still easier to defend here than with the rejected exploratory challengers.",
            ],
          },
          {
            title: "What regressed",
            bullets: [
              "OOD Macro F1 remains below the baseline reference.",
              "ID performance gives back some headroom, which keeps the story from becoming a clean win.",
            ],
          },
          {
            title: "Reason for status",
            bullets: [
              "The method is mixed because it improves the hardest subgroup outcome without resolving the wider robustness tradeoff.",
            ],
          },
        ],
        lineage: {
          parentLabel: "Baseline / distilbert_baseline_seed_13",
          parentPath: "/lane/robustness",
          currentLabel: "Reweighting",
          childRuns: [
            { label: "Seed 13", path: "/run/distilbert_reweighting_seed_13" },
            { label: "Seed 42", path: "/run/distilbert_reweighting_seed_42" },
            { label: "Seed 87", path: "/run/distilbert_reweighting_seed_87" },
          ],
        },
      },
      {
        methodId: "temperature_scaling",
        methodLabel: "Temperature Scaling",
        status: "mixed",
        scope: "official",
        summary:
          "Keeps the reliability story tidy, but barely moves the robustness lane beyond the baseline reference.",
        metricStrip: [
          { label: "Worst-group", value: 0.425, deltaVsBaseline: 0.009 },
          { label: "OOD", value: 0.634, deltaVsBaseline: -0.005 },
          { label: "ID", value: 0.741, deltaVsBaseline: -0.001 },
        ],
        runs: [
          buildRobustnessRun("temperature_scaling", 13, "mixed", 0.425, 0.634, 0.741),
          buildRobustnessRun("temperature_scaling", 42, "mixed", 0.423, 0.636, 0.742),
          buildRobustnessRun("temperature_scaling", 87, "mixed", 0.427, 0.633, 0.74),
        ],
        explanation: [
          {
            title: "What improved",
            bullets: ["The lane holds roughly baseline robustness while keeping the calibration story cleaner elsewhere."],
          },
          {
            title: "What regressed",
            bullets: ["Worst-group and OOD movement are too small to call this a meaningful robustness intervention."],
          },
          {
            title: "Reason for status",
            bullets: ["The method is mixed in this lane because it stays interpretable but does not materially resolve robustness."],
          },
        ],
        lineage: {
          parentLabel: "Baseline / distilbert_baseline_seed_13",
          parentPath: "/lane/robustness",
          currentLabel: "Temperature Scaling",
          childRuns: [
            { label: "Seed 13", path: "/run/distilbert_temperature_scaling_seed_13" },
            { label: "Seed 42", path: "/run/distilbert_temperature_scaling_seed_42" },
            { label: "Seed 87", path: "/run/distilbert_temperature_scaling_seed_87" },
          ],
        },
      },
      {
        methodId: "group_dro",
        methodLabel: "Group DRO",
        status: "failure",
        scope: "exploratory",
        summary:
          "Exploratory challenger that regressed the official baseline and never cleared the promotion bar.",
        metricStrip: [
          { label: "Worst-group", value: 0.201, deltaVsBaseline: -0.215 },
          { label: "OOD", value: 0.517, deltaVsBaseline: -0.122 },
          { label: "ID", value: 0.688, deltaVsBaseline: -0.054 },
        ],
        runs: [buildRobustnessRun("group_dro", 13, "failure", 0.201, 0.517, 0.688, "exploratory")],
        explanation: [
          {
            title: "What improved",
            bullets: ["No official robustness gain emerged from the scout run."],
          },
          {
            title: "What regressed",
            bullets: [
              "Worst-group, OOD, and ID all moved the wrong way against baseline.",
            ],
          },
          {
            title: "Reason for status",
            bullets: ["The method is a failure because the exploratory scout clearly underperformed the official reference lane."],
          },
        ],
        lineage: {
          parentLabel: "Baseline / distilbert_baseline_seed_13",
          parentPath: "/lane/robustness",
          currentLabel: "Group DRO",
          childRuns: [{ label: "Seed 13", path: "/run/distilbert_group_dro_seed_13" }],
        },
      },
    ],
  },
  calibration: {
    laneId: "calibration",
    laneLabel: "Calibration",
    methods: [
      {
        methodId: "baseline",
        methodLabel: "Baseline",
        status: "mixed",
        scope: "official",
        summary:
          "Reference confidence behavior before mitigation. The calibration gap is understandable, but not tight enough to trust by default.",
        metricStrip: [
          { label: "ECE", value: 0.077, deltaVsBaseline: 0, lowerIsBetter: true },
          { label: "Brier", value: 0.211, deltaVsBaseline: 0, lowerIsBetter: true },
        ],
        runs: [
          buildCalibrationRun("baseline", 13, "mixed", 0.077, 0.211),
          buildCalibrationRun("baseline", 42, "mixed", 0.074, 0.208),
          buildCalibrationRun("baseline", 87, "mixed", 0.079, 0.213),
        ],
        explanation: [
          {
            title: "What improved",
            bullets: ["This route keeps the uncorrected confidence reference available for comparison."],
          },
          {
            title: "What regressed",
            bullets: ["Calibration error remains visibly higher than the stabilized mitigation lane."],
          },
          {
            title: "Reason for status",
            bullets: ["The method is mixed because it is interpretable but still leaves the confidence story too loose."],
          },
        ],
        lineage: {
          parentLabel: "Summary -> Calibration baseline",
          parentPath: "/lane/calibration",
          currentLabel: "Baseline",
          childRuns: [
            { label: "Seed 13", path: "/run/distilbert_baseline_seed_13" },
            { label: "Seed 42", path: "/run/distilbert_baseline_seed_42" },
            { label: "Seed 87", path: "/run/distilbert_baseline_seed_87" },
          ],
        },
      },
      {
        methodId: "temperature_scaling",
        methodLabel: "Temperature Scaling",
        status: "stable",
        scope: "official",
        summary:
          "Cleanest official mitigation. Calibration improves without complicating the interpretation.",
        metricStrip: [
          { label: "ECE", value: 0.041, deltaVsBaseline: -0.036, lowerIsBetter: true },
          { label: "Brier", value: 0.189, deltaVsBaseline: -0.022, lowerIsBetter: true },
        ],
        runs: [
          buildCalibrationRun("temperature_scaling", 13, "stable", 0.041, 0.189),
          buildCalibrationRun("temperature_scaling", 42, "stable", 0.044, 0.192),
          buildCalibrationRun("temperature_scaling", 87, "stable", 0.043, 0.191),
        ],
        explanation: [
          {
            title: "What improved",
            bullets: [
              "ECE and Brier both move cleanly below baseline across seeds.",
              "The seeded behavior stays consistent enough to support a stable verdict.",
            ],
          },
          {
            title: "What regressed",
            bullets: ["No material regression is carrying the lane story here."],
          },
          {
            title: "Reason for status",
            bullets: ["The method is stable because it improves calibration cleanly and consistently without introducing a conflicting story."],
          },
        ],
        lineage: {
          parentLabel: "Baseline / distilbert_baseline_seed_13",
          parentPath: "/lane/calibration",
          currentLabel: "Temperature Scaling",
          childRuns: [
            { label: "Seed 13", path: "/run/distilbert_temperature_scaling_seed_13" },
            { label: "Seed 42", path: "/run/distilbert_temperature_scaling_seed_42" },
            { label: "Seed 87", path: "/run/distilbert_temperature_scaling_seed_87" },
          ],
        },
      },
      {
        methodId: "reweighting",
        methodLabel: "Reweighting",
        status: "mixed",
        scope: "official",
        summary:
          "Retains some calibration improvement, but not as cleanly or consistently as temperature scaling.",
        metricStrip: [
          { label: "ECE", value: 0.058, deltaVsBaseline: -0.019, lowerIsBetter: true },
          { label: "Brier", value: 0.201, deltaVsBaseline: -0.01, lowerIsBetter: true },
        ],
        runs: [
          buildCalibrationRun("reweighting", 13, "mixed", 0.058, 0.201),
          buildCalibrationRun("reweighting", 42, "mixed", 0.062, 0.204),
          buildCalibrationRun("reweighting", 87, "mixed", 0.057, 0.2),
        ],
        explanation: [
          {
            title: "What improved",
            bullets: ["Calibration does improve against baseline, which keeps the method from becoming a failure in this lane."],
          },
          {
            title: "What regressed",
            bullets: ["The improvement is weaker and less uniform than temperature scaling, so the lane is harder to call stable."],
          },
          {
            title: "Reason for status",
            bullets: ["The method is mixed because there is signal, but not enough clarity to overtake the stable calibration reference."],
          },
        ],
        lineage: {
          parentLabel: "Baseline / distilbert_baseline_seed_13",
          parentPath: "/lane/calibration",
          currentLabel: "Reweighting",
          childRuns: [
            { label: "Seed 13", path: "/run/distilbert_reweighting_seed_13" },
            { label: "Seed 42", path: "/run/distilbert_reweighting_seed_42" },
            { label: "Seed 87", path: "/run/distilbert_reweighting_seed_87" },
          ],
        },
      },
    ],
  },
};

function normalizeMethodRouteMethodId(
  methods: MethodRouteMethodSnapshot[],
  methodId: string | undefined,
): MethodRouteMethodSnapshot {
  const requestedMethod = methodId
    ? methods.find((candidate) => candidate.methodId === methodId)
    : null;

  return (
    requestedMethod ??
    methods.find((candidate) => candidate.methodId !== "baseline") ??
    methods[0]
  );
}

export function buildMethodRouteModel(
  laneId: string | undefined,
  methodId: string | undefined,
  scope: TraceScope,
): MethodRouteModel {
  const normalizedLaneId: LaneRouteLaneId = laneId === "calibration" ? "calibration" : "robustness";
  const lane = METHOD_ROUTE_SNAPSHOT[normalizedLaneId];
  const requestedMethod = methodId
    ? lane.methods.find((candidate) => candidate.methodId === methodId)
    : null;

  if (requestedMethod?.scope === "exploratory" && scope === "official") {
    return {
      state: "scope-hidden",
      question: "Why is this method judged this way?",
      laneId: lane.laneId,
      laneLabel: lane.laneLabel,
      methodId: requestedMethod.methodId,
      methodLabel: requestedMethod.methodLabel,
      status: requestedMethod.status,
      summary: requestedMethod.summary,
      scope: requestedMethod.scope,
      message:
        "This method is exploratory. Switch scope to include exploratory evidence before opening its method-level breakdown.",
      recoveryPath: `/lane/${lane.laneId}/${requestedMethod.methodId}?scope=all`,
    };
  }

  const visibleMethods = lane.methods.filter((candidate) => scope === "all" || candidate.scope === "official");
  const method = normalizeMethodRouteMethodId(visibleMethods, methodId);
  const officialRuns = method.runs.filter((candidate) => candidate.scope === "official");
  const exploratoryRuns = scope === "all" ? method.runs.filter((candidate) => candidate.scope === "exploratory") : [];
  const visibleRuns = [...officialRuns, ...exploratoryRuns];
  const defaultRunEntityId =
    officialRuns[0]?.entityId ?? exploratoryRuns[0]?.entityId ?? "run_missing";
  const hasExploratoryInView = method.scope === "exploratory" || exploratoryRuns.length > 0;

  return {
    state: "ready",
    question: "Why is this method judged this way?",
    laneId: lane.laneId,
    laneLabel: lane.laneLabel,
    methodId: method.methodId,
    methodLabel: method.methodLabel,
    status: method.status,
    summary: method.summary,
    scope: method.scope,
    statusModifier: hasExploratoryInView ? "Exploratory in view" : undefined,
    scopeNote: hasExploratoryInView
      ? method.scope === "exploratory"
        ? "Exploratory method is in view. Official lane status remains canonical."
        : "Exploratory runs are visible below. Official method status remains canonical."
      : undefined,
    metricStrip: method.metricStrip,
    officialRuns,
    exploratoryRuns,
    runs: visibleRuns,
    defaultRunEntityId,
    explanation: method.explanation,
    lineage: method.lineage,
  };
}

export function getDefaultMethodRunEntityId(model: MethodRouteReadyModel) {
  return model.defaultRunEntityId;
}

export function resolveMethodRunEntityId(
  model: MethodRouteReadyModel,
  entityId: string | null,
) {
  if (!entityId) {
    return model.defaultRunEntityId;
  }

  return model.runs.some((run) => run.entityId === entityId) ? entityId : model.defaultRunEntityId;
}

export function getMethodInspectorEntity(
  model: MethodRouteReadyModel,
  entityId: string,
): MethodRouteInspectorEntity {
  const run = model.runs.find((candidate) => candidate.entityId === entityId) ?? model.runs[0];

  return {
    entityId: run.entityId,
    entityType: "Run",
    label: run.runId,
    status: run.status,
    scope: run.scope,
    summary: `${model.methodLabel} seed ${run.seed} for the ${model.laneLabel.toLowerCase()} lane.`,
    evidenceLinks: run.evidenceLinks,
    provenance: run.provenance,
  };
}
