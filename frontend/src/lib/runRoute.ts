import type { TraceScope } from "@/app/scope";
import type {
  LaneRouteLaneId,
  LaneRouteMethodId,
  LaneRouteRowScope,
  LaneRouteStatus,
} from "@/lib/laneRoute";

export type RunRouteMetric = {
  label: string;
  value: number;
  deltaVsBaseline: number | null;
  lowerIsBetter?: boolean;
};

export type RunRouteLineageEntry = {
  relation: "Parent method" | "Parent run" | "Current run" | "Child evidence";
  items: Array<{
    label: string;
    path?: string;
    mono?: boolean;
  }>;
};

export type RunRouteArtifactLink = {
  label: string;
  path: string;
};

export type RunRouteArtifactGroup = {
  label: string;
  items: RunRouteArtifactLink[];
};

export type RunRouteProvenanceField = {
  label: string;
  value: string;
  mono?: boolean;
};

export type RunRouteInspectorEntity = {
  entityId: string;
  entityType: "Run";
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  summary: string;
  evidenceLinks: RunRouteArtifactLink[];
  provenance: RunRouteProvenanceField[];
  rawPath: string;
};

export type RunRouteModel = {
  question: "What happened in this run?";
  entityId: string;
  runId: string;
  seed: number;
  laneId: LaneRouteLaneId;
  laneLabel: string;
  methodId: LaneRouteMethodId;
  methodLabel: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  breadcrumbs: {
    summaryPath: string;
    lanePath: string;
    methodPath: string;
  };
  metricStrip: RunRouteMetric[];
  interpretationNote: string;
  lineage: RunRouteLineageEntry[];
  artifacts: RunRouteArtifactGroup[];
  inspector: RunRouteInspectorEntity;
};

type RunRouteSnapshot = Omit<RunRouteModel, "breadcrumbs" | "inspector">;

type RunRouteContext = {
  laneId?: string | null;
  methodId?: string | null;
};

function buildScopedPath(
  path: string,
  scope: TraceScope,
  extraSearchParams?: Record<string, string | undefined>,
) {
  const searchParams = new URLSearchParams();
  searchParams.set("scope", scope);

  for (const [key, value] of Object.entries(extraSearchParams ?? {})) {
    if (value) {
      searchParams.set(key, value);
    }
  }

  return `${path}?${searchParams.toString()}`;
}

export function buildRunRoutePath(
  runId: string,
  scope: TraceScope,
  context?: {
    laneId?: string | null;
    methodId?: string | null;
  },
) {
  return buildScopedPath(`/run/${runId}`, scope, {
    lane: context?.laneId ?? undefined,
    method: context?.methodId ?? undefined,
  });
}

export function buildRawDebugPath(entityId: string, scope: TraceScope) {
  return buildScopedPath(`/debug/raw/${entityId}`, scope);
}

function buildArtifactGroups(runId: string): RunRouteArtifactGroup[] {
  return [
    {
      label: "Reports",
      items: [{ label: "Run report", path: `/mock-artifacts/${runId}/report.md` }],
    },
    {
      label: "Bundles",
      items: [
        { label: "Eval bundle", path: `/mock-artifacts/${runId}/eval_bundle.json` },
        { label: "Metadata", path: `/mock-artifacts/${runId}/metadata.json` },
      ],
    },
    {
      label: "Predictions",
      items: [
        { label: "Validation", path: `/mock-artifacts/${runId}/predictions_val.parquet` },
        { label: "Test", path: `/mock-artifacts/${runId}/predictions_test.parquet` },
      ],
    },
  ];
}

function buildInspectorEvidenceLinks(runId: string): RunRouteArtifactLink[] {
  return [
    { label: "Report", path: `/mock-artifacts/${runId}/report.md` },
    { label: "Eval bundle", path: `/mock-artifacts/${runId}/eval_bundle.json` },
    { label: "Metadata", path: `/mock-artifacts/${runId}/metadata.json` },
  ];
}

function buildProvenanceFields(
  laneId: LaneRouteLaneId,
  methodId: LaneRouteMethodId,
  runId: string,
): RunRouteProvenanceField[] {
  return [
    { label: "Source path", value: `artifacts/mock/runs/${laneId}/${methodId}/${runId}/metadata.json`, mono: true },
    { label: "Lane", value: laneId },
    { label: "Method", value: methodId },
    { label: "Related IDs", value: `run_${runId}, lane_${laneId}, method_${methodId}` },
  ];
}

function inferMethodIdFromRunId(runId: string): LaneRouteMethodId {
  if (runId.includes("temperature_scaling")) {
    return "temperature_scaling";
  }

  if (runId.includes("reweighting")) {
    return "reweighting";
  }

  if (runId.includes("group_dro")) {
    return "group_dro";
  }

  return "baseline";
}

function inferCanonicalLaneId(methodId: LaneRouteMethodId): LaneRouteLaneId {
  return methodId === "temperature_scaling" ? "calibration" : "robustness";
}

function buildLineage(
  laneId: LaneRouteLaneId,
  laneLabel: string,
  methodId: LaneRouteMethodId,
  methodLabel: string,
  runId: string,
  seed: number,
  artifactGroups: RunRouteArtifactGroup[],
): RunRouteLineageEntry[] {
  const baselineRunId = `distilbert_baseline_seed_${seed}`;

  return [
    {
      relation: "Parent method",
      items: [
        {
          label: `${laneLabel} / ${methodLabel}`,
          path: `/lane/${laneId}/${methodId}`,
        },
      ],
    },
    {
      relation: "Parent run",
      items: [
        methodId === "baseline"
          ? {
              label: `${laneLabel} lane reference`,
              path: `/lane/${laneId}`,
            }
          : {
              label: baselineRunId,
              path: `/run/${baselineRunId}`,
              mono: true,
            },
      ],
    },
    {
      relation: "Current run",
      items: [{ label: runId, mono: true }],
    },
    {
      relation: "Child evidence",
      items: artifactGroups.map((group) => ({
        label: `${group.label} (${group.items.length})`,
      })),
    },
  ];
}

function buildRunSnapshot({
  laneId,
  laneLabel,
  methodId,
  methodLabel,
  seed,
  status,
  scope = "official",
  metricStrip,
  interpretationNote,
}: {
  laneId: LaneRouteLaneId;
  laneLabel: string;
  methodId: LaneRouteMethodId;
  methodLabel: string;
  seed: number;
  status: LaneRouteStatus;
  scope?: LaneRouteRowScope;
  metricStrip: RunRouteMetric[];
  interpretationNote: string;
}): RunRouteSnapshot {
  const runId = `distilbert_${methodId}_seed_${seed}`;
  const entityId = `run_${runId}`;
  const artifacts = buildArtifactGroups(runId);

  return {
    question: "What happened in this run?",
    entityId,
    runId,
    seed,
    laneId,
    laneLabel,
    methodId,
    methodLabel,
    status,
    scope,
    metricStrip,
    interpretationNote,
    lineage: buildLineage(laneId, laneLabel, methodId, methodLabel, runId, seed, artifacts),
    artifacts,
  };
}

const RUN_ROUTE_SNAPSHOT: RunRouteSnapshot[] = [
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 13,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.416, deltaVsBaseline: 0 },
      { label: "OOD", value: 0.639, deltaVsBaseline: 0 },
      { label: "ID", value: 0.742, deltaVsBaseline: 0 },
    ],
    interpretationNote:
      "Reference run that keeps the robustness gap legible without introducing mitigation uplift.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 42,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.421, deltaVsBaseline: 0.005 },
      { label: "OOD", value: 0.642, deltaVsBaseline: 0.003 },
      { label: "ID", value: 0.743, deltaVsBaseline: 0.001 },
    ],
    interpretationNote:
      "Seed variation is minor here, which is why baseline remains the clean reference even without closing the lane gap.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 87,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.408, deltaVsBaseline: -0.008 },
      { label: "OOD", value: 0.634, deltaVsBaseline: -0.005 },
      { label: "ID", value: 0.739, deltaVsBaseline: -0.003 },
    ],
    interpretationNote:
      "The robustness floor stays low even when the seed shifts, reinforcing the baseline as a stable but insufficient reference.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 13,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.477, deltaVsBaseline: 0.061 },
      { label: "OOD", value: 0.621, deltaVsBaseline: -0.018 },
      { label: "ID", value: 0.734, deltaVsBaseline: -0.008 },
    ],
    interpretationNote:
      "Worst-group performance improves over baseline, but the same run still gives back OOD and ID headroom.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 42,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.468, deltaVsBaseline: 0.052 },
      { label: "OOD", value: 0.626, deltaVsBaseline: -0.013 },
      { label: "ID", value: 0.736, deltaVsBaseline: -0.006 },
    ],
    interpretationNote:
      "The mitigation signal holds across seeds, but the tradeoff profile remains too costly to call this a clean robustness win.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 87,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.472, deltaVsBaseline: 0.056 },
      { label: "OOD", value: 0.623, deltaVsBaseline: -0.016 },
      { label: "ID", value: 0.735, deltaVsBaseline: -0.007 },
    ],
    interpretationNote:
      "Reweighting still lifts the hard subgroup, but not enough to erase the broader OOD and ID compromise.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 13,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.425, deltaVsBaseline: 0.009 },
      { label: "OOD", value: 0.634, deltaVsBaseline: -0.005 },
      { label: "ID", value: 0.741, deltaVsBaseline: -0.001 },
    ],
    interpretationNote:
      "This run stays readable, but it does not materially change the robustness story beyond the baseline reference.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 42,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.423, deltaVsBaseline: 0.007 },
      { label: "OOD", value: 0.636, deltaVsBaseline: -0.003 },
      { label: "ID", value: 0.742, deltaVsBaseline: 0 },
    ],
    interpretationNote:
      "Seed drift stays small, but the mitigation still reads as calibration-first rather than robustness-resolving.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 87,
    status: "mixed",
    metricStrip: [
      { label: "Worst-group", value: 0.427, deltaVsBaseline: 0.011 },
      { label: "OOD", value: 0.633, deltaVsBaseline: -0.006 },
      { label: "ID", value: 0.74, deltaVsBaseline: -0.002 },
    ],
    interpretationNote:
      "The run stays interpretable, but the hard subgroup uplift remains too small to change the lane verdict.",
  }),
  buildRunSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "group_dro",
    methodLabel: "Group DRO",
    seed: 13,
    status: "failure",
    scope: "exploratory",
    metricStrip: [
      { label: "Worst-group", value: 0.201, deltaVsBaseline: -0.215 },
      { label: "OOD", value: 0.517, deltaVsBaseline: -0.122 },
      { label: "ID", value: 0.688, deltaVsBaseline: -0.054 },
    ],
    interpretationNote:
      "Exploratory scout failure: the run regresses worst-group, OOD, and ID against the official reference.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 13,
    status: "mixed",
    metricStrip: [
      { label: "ECE", value: 0.077, deltaVsBaseline: 0, lowerIsBetter: true },
      { label: "Brier", value: 0.211, deltaVsBaseline: 0, lowerIsBetter: true },
    ],
    interpretationNote:
      "Reference confidence behavior before mitigation. The run is understandable, but not tight enough to trust by default.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 42,
    status: "mixed",
    metricStrip: [
      { label: "ECE", value: 0.074, deltaVsBaseline: -0.003, lowerIsBetter: true },
      { label: "Brier", value: 0.208, deltaVsBaseline: -0.003, lowerIsBetter: true },
    ],
    interpretationNote:
      "Seed variation does not fix the calibration gap; it only reinforces that the reference lane still needs mitigation.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 87,
    status: "mixed",
    metricStrip: [
      { label: "ECE", value: 0.079, deltaVsBaseline: 0.002, lowerIsBetter: true },
      { label: "Brier", value: 0.213, deltaVsBaseline: 0.002, lowerIsBetter: true },
    ],
    interpretationNote:
      "Confidence remains looser than the stable mitigation lane, even when the seed changes.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 13,
    status: "stable",
    metricStrip: [
      { label: "ECE", value: 0.041, deltaVsBaseline: -0.036, lowerIsBetter: true },
      { label: "Brier", value: 0.189, deltaVsBaseline: -0.022, lowerIsBetter: true },
    ],
    interpretationNote:
      "Clean calibration improvement with no conflicting signal, which is why this run supports the stable lane verdict.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 42,
    status: "stable",
    metricStrip: [
      { label: "ECE", value: 0.044, deltaVsBaseline: -0.03, lowerIsBetter: true },
      { label: "Brier", value: 0.192, deltaVsBaseline: -0.016, lowerIsBetter: true },
    ],
    interpretationNote:
      "The calibration win remains intact across seeds, keeping this run inside the stable reliability story.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 87,
    status: "stable",
    metricStrip: [
      { label: "ECE", value: 0.043, deltaVsBaseline: -0.036, lowerIsBetter: true },
      { label: "Brier", value: 0.191, deltaVsBaseline: -0.022, lowerIsBetter: true },
    ],
    interpretationNote:
      "The seeded variation stays narrow, which helps this run carry the stable calibration conclusion cleanly.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 13,
    status: "mixed",
    metricStrip: [
      { label: "ECE", value: 0.058, deltaVsBaseline: -0.019, lowerIsBetter: true },
      { label: "Brier", value: 0.201, deltaVsBaseline: -0.01, lowerIsBetter: true },
    ],
    interpretationNote:
      "Calibration improves against baseline, but the gain is weaker and less tidy than temperature scaling.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 42,
    status: "mixed",
    metricStrip: [
      { label: "ECE", value: 0.062, deltaVsBaseline: -0.012, lowerIsBetter: true },
      { label: "Brier", value: 0.204, deltaVsBaseline: -0.004, lowerIsBetter: true },
    ],
    interpretationNote:
      "The reliability gain remains real, but this seeded run is not clean enough to overtake the stable lane leader.",
  }),
  buildRunSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 87,
    status: "mixed",
    metricStrip: [
      { label: "ECE", value: 0.057, deltaVsBaseline: -0.022, lowerIsBetter: true },
      { label: "Brier", value: 0.2, deltaVsBaseline: -0.011, lowerIsBetter: true },
    ],
    interpretationNote:
      "This run still points in the right direction, but not with the consistency needed for a stable calibration verdict.",
  }),
];

function normalizeLaneId(
  requestedLaneId: string | null | undefined,
  runId: string,
  requestedMethodId?: string | null,
): LaneRouteLaneId {
  if (requestedLaneId === "robustness" || requestedLaneId === "calibration") {
    return requestedLaneId;
  }

  const inferredMethodId = requestedMethodId
    ? (requestedMethodId as LaneRouteMethodId)
    : inferMethodIdFromRunId(runId);

  return inferCanonicalLaneId(inferredMethodId);
}

function normalizeMethodId(runId: string, requestedMethodId?: string | null): LaneRouteMethodId {
  if (
    requestedMethodId === "baseline" ||
    requestedMethodId === "reweighting" ||
    requestedMethodId === "temperature_scaling" ||
    requestedMethodId === "group_dro"
  ) {
    return requestedMethodId;
  }

  return inferMethodIdFromRunId(runId);
}

function findSnapshot(
  runId: string | undefined,
  scope: TraceScope,
  context?: RunRouteContext,
): RunRouteSnapshot {
  const visibleSnapshots = RUN_ROUTE_SNAPSHOT.filter(
    (snapshot) => scope === "all" || snapshot.scope === "official",
  );
  const requestedRunId = runId ?? "distilbert_reweighting_seed_13";
  const requestedMethodId = normalizeMethodId(requestedRunId, context?.methodId);
  const requestedLaneId = normalizeLaneId(context?.laneId, requestedRunId, requestedMethodId);

  const exactMatch = visibleSnapshots.find(
    (snapshot) => snapshot.runId === requestedRunId && snapshot.laneId === requestedLaneId,
  );

  if (exactMatch) {
    return exactMatch;
  }

  const inferredMatch = visibleSnapshots.find((snapshot) => snapshot.runId === requestedRunId);

  if (inferredMatch) {
    return inferredMatch;
  }

  return (
    visibleSnapshots.find(
      (snapshot) => snapshot.laneId === requestedLaneId && snapshot.methodId === requestedMethodId,
    ) ?? visibleSnapshots[0]
  );
}

export function buildRunRouteModel(
  runId: string | undefined,
  scope: TraceScope,
  context?: RunRouteContext,
): RunRouteModel {
  const snapshot = findSnapshot(runId, scope, context);
  const methodPath = buildScopedPath(`/lane/${snapshot.laneId}/${snapshot.methodId}`, scope);
  const provenance = buildProvenanceFields(snapshot.laneId, snapshot.methodId, snapshot.runId);
  const lineage = snapshot.lineage.map((entry) => ({
    ...entry,
    items: entry.items.map((item) => {
      if (!item.path) {
        return item;
      }

      if (item.path.startsWith("/run/")) {
        const lineageRunId = item.path.replace("/run/", "");

        return {
          ...item,
          path: buildRunRoutePath(lineageRunId, scope, {
            laneId: snapshot.laneId,
            methodId: "baseline",
          }),
        };
      }

      return {
        ...item,
        path: buildScopedPath(item.path, scope),
      };
    }),
  }));

  return {
    ...snapshot,
    breadcrumbs: {
      summaryPath: buildScopedPath("/", scope),
      lanePath: buildScopedPath(`/lane/${snapshot.laneId}`, scope),
      methodPath,
    },
    lineage,
    inspector: {
      entityId: snapshot.entityId,
      entityType: "Run",
      label: snapshot.runId,
      status: snapshot.status,
      scope: snapshot.scope,
      summary: snapshot.interpretationNote,
      evidenceLinks: buildInspectorEvidenceLinks(snapshot.runId),
      provenance,
      rawPath: buildRawDebugPath(snapshot.entityId, scope),
    },
  };
}
