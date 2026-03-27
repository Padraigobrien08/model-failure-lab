import type { TraceScope } from "@/app/scope";
import type {
  LaneRouteRowScope,
  LaneRouteStatus,
} from "@/lib/laneRoute";
import { buildRawDebugPath } from "@/lib/runRoute";

const RAW_JSON_TAB_SLUG = "raw JSON";
const MANIFEST_ENTITY_TAB_SLUG = "manifest entity";
const METADATA_TAB_SLUG = "metadata";

export type RawDebugTabKey = "raw_json" | "manifest_entity" | "metadata";

export type RawDebugEntityType = "Run" | "Method";

export type RawDebugPayloadTab = {
  key: RawDebugTabKey;
  label: "Raw JSON" | "Manifest entity" | "Metadata";
  copyLabel: string;
  content: string;
};

export type RawDebugRelatedEntity = {
  relation: string;
  entityId: string;
  entityType: RawDebugEntityType;
  label: string;
  scope: LaneRouteRowScope;
  path: string;
};

export type RawDebugReadyModel = {
  state: "ready";
  question: "What artifact backs this entity?";
  entityId: string;
  entityType: RawDebugEntityType;
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  defaultTab: RawDebugTabKey;
  tabs: RawDebugPayloadTab[];
  relatedEntities: RawDebugRelatedEntity[];
};

export type RawDebugScopeHiddenModel = {
  state: "scope-hidden";
  question: "What artifact backs this entity?";
  entityId: string;
  entityType: RawDebugEntityType;
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  message: string;
  recoveryPath: string;
  relatedEntities: RawDebugRelatedEntity[];
};

export type RawDebugMissingModel = {
  state: "missing";
  question: "What artifact backs this entity?";
  entityId: string;
  message: string;
};

export type RawDebugRouteModel =
  | RawDebugReadyModel
  | RawDebugScopeHiddenModel
  | RawDebugMissingModel;

type RawDebugEntitySnapshot = {
  entityId: string;
  entityType: RawDebugEntityType;
  label: string;
  status: LaneRouteStatus;
  scope: LaneRouteRowScope;
  rawJson: Record<string, unknown>;
  manifestEntity: Record<string, unknown>;
  metadata: Record<string, unknown>;
  relatedEntities: Array<{
    relation: string;
    entityId: string;
    entityType: RawDebugEntityType;
    label: string;
    scope: LaneRouteRowScope;
  }>;
};

function formatPayload(payload: Record<string, unknown>) {
  return JSON.stringify(payload, null, 2);
}

function buildTabs(snapshot: RawDebugEntitySnapshot): RawDebugPayloadTab[] {
  return [
    {
      key: "raw_json",
      label: "Raw JSON",
      copyLabel: "Copy Raw JSON",
      content: formatPayload(snapshot.rawJson),
    },
    {
      key: "manifest_entity",
      label: "Manifest entity",
      copyLabel: "Copy Manifest entity",
      content: formatPayload(snapshot.manifestEntity),
    },
    {
      key: "metadata",
      label: "Metadata",
      copyLabel: "Copy Metadata",
      content: formatPayload(snapshot.metadata),
    },
  ];
}

function buildRelatedEntities(
  relatedEntities: RawDebugEntitySnapshot["relatedEntities"],
  scope: TraceScope,
): RawDebugRelatedEntity[] {
  return relatedEntities.map((entity) => ({
    ...entity,
    path: buildRawDebugPath(entity.entityId, scope),
  }));
}

function buildRunSnapshot({
  runId,
  laneId,
  laneLabel,
  methodId,
  methodLabel,
  scope = "official",
  status,
  seed,
  metrics,
  summary,
  artifacts,
  relatedEntities,
}: {
  runId: string;
  laneId: string;
  laneLabel: string;
  methodId: string;
  methodLabel: string;
  scope?: LaneRouteRowScope;
  status: LaneRouteStatus;
  seed: number;
  metrics: Record<string, number>;
  summary: string;
  artifacts: string[];
  relatedEntities: RawDebugEntitySnapshot["relatedEntities"];
}): RawDebugEntitySnapshot {
  const entityId = `run_${runId}`;

  return {
    entityId,
    entityType: "Run",
    label: runId,
    status,
    scope,
    rawJson: {
      runId,
      entityId,
      laneId,
      methodId,
      seed,
      status,
      summary,
      metrics,
      artifacts,
    },
    manifestEntity: {
      id: entityId,
      type: "run",
      label: runId,
      scope,
      defaultVisible: scope === "official",
      verdict: status,
      artifactRefs: artifacts,
      relatedIds: relatedEntities.map((entity) => entity.entityId),
    },
    metadata: {
      sourcePath: `artifacts/mock/runs/${laneId}/${methodId}/${runId}/metadata.json`,
      lane: laneLabel,
      method: methodLabel,
      seed,
      capturedAt: "2026-03-27T10:00:00Z",
    },
    relatedEntities,
  };
}

function buildMethodSnapshot({
  laneId,
  laneLabel,
  methodId,
  methodLabel,
  scope = "official",
  status,
  summary,
  metrics,
  relatedEntities,
}: {
  laneId: string;
  laneLabel: string;
  methodId: string;
  methodLabel: string;
  scope?: LaneRouteRowScope;
  status: LaneRouteStatus;
  summary: string;
  metrics: Record<string, number>;
  relatedEntities: RawDebugEntitySnapshot["relatedEntities"];
}): RawDebugEntitySnapshot {
  const entityId = `method_${methodId}_${laneId}`;

  return {
    entityId,
    entityType: "Method",
    label: methodLabel,
    status,
    scope,
    rawJson: {
      entityId,
      laneId,
      laneLabel,
      methodId,
      methodLabel,
      status,
      summary,
      metrics,
    },
    manifestEntity: {
      id: entityId,
      type: "method",
      label: methodLabel,
      scope,
      defaultVisible: scope === "official",
      verdict: status,
      relatedIds: relatedEntities.map((entity) => entity.entityId),
    },
    metadata: {
      sourcePath: `artifacts/mock/methods/${laneId}/${methodId}.json`,
      lane: laneLabel,
      method: methodLabel,
      classification: status,
      capturedAt: "2026-03-27T10:00:00Z",
    },
    relatedEntities,
  };
}

const RAW_ENTITY_SNAPSHOTS: Record<string, RawDebugEntitySnapshot> = {
  run_distilbert_baseline_seed_13: buildRunSnapshot({
    runId: "distilbert_baseline_seed_13",
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "baseline",
    methodLabel: "Baseline",
    seed: 13,
    status: "mixed",
    summary:
      "Reference run that leaves the robustness gap easy to inspect without mitigation uplift.",
    metrics: {
      worstGroup: 0.416,
      ood: 0.639,
      id: 0.742,
    },
    artifacts: ["report.md", "eval_bundle.json", "metadata.json", "predictions_test.parquet"],
    relatedEntities: [
      {
        relation: "Parent method",
        entityId: "method_baseline_robustness",
        entityType: "Method",
        label: "Baseline",
        scope: "official",
      },
      {
        relation: "Sibling run",
        entityId: "run_distilbert_baseline_seed_42",
        entityType: "Run",
        label: "distilbert_baseline_seed_42",
        scope: "official",
      },
    ],
  }),
  run_distilbert_reweighting_seed_13: buildRunSnapshot({
    runId: "distilbert_reweighting_seed_13",
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    seed: 13,
    status: "mixed",
    summary:
      "Best official robustness run so far, but still paired with OOD and ID regressions.",
    metrics: {
      worstGroup: 0.477,
      ood: 0.621,
      id: 0.734,
    },
    artifacts: ["report.md", "eval_bundle.json", "metadata.json", "predictions_test.parquet"],
    relatedEntities: [
      {
        relation: "Parent method",
        entityId: "method_reweighting_robustness",
        entityType: "Method",
        label: "Reweighting",
        scope: "official",
      },
      {
        relation: "Baseline reference",
        entityId: "run_distilbert_baseline_seed_13",
        entityType: "Run",
        label: "distilbert_baseline_seed_13",
        scope: "official",
      },
      {
        relation: "Sibling run",
        entityId: "run_distilbert_reweighting_seed_42",
        entityType: "Run",
        label: "distilbert_reweighting_seed_42",
        scope: "official",
      },
    ],
  }),
  run_distilbert_temperature_scaling_seed_13: buildRunSnapshot({
    runId: "distilbert_temperature_scaling_seed_13",
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    seed: 13,
    status: "stable",
    summary:
      "Cleanest official calibration run. Error tightens without destabilizing the explanation.",
    metrics: {
      ece: 0.041,
      brier: 0.189,
    },
    artifacts: ["report.md", "eval_bundle.json", "metadata.json", "predictions_val.parquet"],
    relatedEntities: [
      {
        relation: "Parent method",
        entityId: "method_temperature_scaling_calibration",
        entityType: "Method",
        label: "Temperature Scaling",
        scope: "official",
      },
      {
        relation: "Baseline reference",
        entityId: "run_distilbert_baseline_seed_13",
        entityType: "Run",
        label: "distilbert_baseline_seed_13",
        scope: "official",
      },
    ],
  }),
  run_distilbert_group_dro_seed_13: buildRunSnapshot({
    runId: "distilbert_group_dro_seed_13",
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "group_dro",
    methodLabel: "Group DRO",
    seed: 13,
    status: "failure",
    scope: "exploratory",
    summary:
      "Exploratory challenger that regressed the baseline and failed the promotion gate.",
    metrics: {
      worstGroup: 0.201,
      ood: 0.517,
      id: 0.688,
    },
    artifacts: ["report.md", "eval_bundle.json", "metadata.json"],
    relatedEntities: [
      {
        relation: "Parent method",
        entityId: "method_group_dro_robustness",
        entityType: "Method",
        label: "Group DRO",
        scope: "exploratory",
      },
      {
        relation: "Baseline reference",
        entityId: "run_distilbert_baseline_seed_13",
        entityType: "Run",
        label: "distilbert_baseline_seed_13",
        scope: "official",
      },
    ],
  }),
  method_baseline_robustness: buildMethodSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "baseline",
    methodLabel: "Baseline",
    status: "mixed",
    summary:
      "Reference method for the robustness lane. It keeps the gap legible, but does not resolve it.",
    metrics: {
      worstGroup: 0.416,
      ood: 0.639,
      id: 0.742,
    },
    relatedEntities: [
      {
        relation: "Seed 13 run",
        entityId: "run_distilbert_baseline_seed_13",
        entityType: "Run",
        label: "distilbert_baseline_seed_13",
        scope: "official",
      },
    ],
  }),
  method_reweighting_robustness: buildMethodSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "reweighting",
    methodLabel: "Reweighting",
    status: "mixed",
    summary:
      "Official robustness lead, but still mixed because the uplift arrives with real tradeoffs.",
    metrics: {
      worstGroup: 0.477,
      ood: 0.621,
      id: 0.734,
    },
    relatedEntities: [
      {
        relation: "Seed 13 run",
        entityId: "run_distilbert_reweighting_seed_13",
        entityType: "Run",
        label: "distilbert_reweighting_seed_13",
        scope: "official",
      },
      {
        relation: "Baseline reference",
        entityId: "method_baseline_robustness",
        entityType: "Method",
        label: "Baseline",
        scope: "official",
      },
    ],
  }),
  method_temperature_scaling_calibration: buildMethodSnapshot({
    laneId: "calibration",
    laneLabel: "Calibration",
    methodId: "temperature_scaling",
    methodLabel: "Temperature Scaling",
    status: "stable",
    summary:
      "Cleanest official mitigation. Calibration improves without complicating the story.",
    metrics: {
      ece: 0.041,
      brier: 0.189,
    },
    relatedEntities: [
      {
        relation: "Seed 13 run",
        entityId: "run_distilbert_temperature_scaling_seed_13",
        entityType: "Run",
        label: "distilbert_temperature_scaling_seed_13",
        scope: "official",
      },
      {
        relation: "Baseline reference",
        entityId: "method_baseline_robustness",
        entityType: "Method",
        label: "Baseline",
        scope: "official",
      },
    ],
  }),
  method_group_dro_robustness: buildMethodSnapshot({
    laneId: "robustness",
    laneLabel: "Robustness",
    methodId: "group_dro",
    methodLabel: "Group DRO",
    status: "failure",
    scope: "exploratory",
    summary:
      "Exploratory challenger that regressed the baseline and never cleared promotion.",
    metrics: {
      worstGroup: 0.201,
      ood: 0.517,
      id: 0.688,
    },
    relatedEntities: [
      {
        relation: "Seed 13 run",
        entityId: "run_distilbert_group_dro_seed_13",
        entityType: "Run",
        label: "distilbert_group_dro_seed_13",
        scope: "exploratory",
      },
      {
        relation: "Official baseline",
        entityId: "method_baseline_robustness",
        entityType: "Method",
        label: "Baseline",
        scope: "official",
      },
    ],
  }),
};

export function buildRawDebugRouteModel(
  entityId: string | undefined,
  scope: TraceScope,
): RawDebugRouteModel {
  const question = "What artifact backs this entity?" as const;
  const normalizedEntityId = entityId ?? "unknown_entity";
  const snapshot = RAW_ENTITY_SNAPSHOTS[normalizedEntityId];

  if (!snapshot) {
    return {
      state: "missing",
      question,
      entityId: normalizedEntityId,
      message:
        "This entity is not available in the mocked raw-debug contract. Trace back to a supported run or method and reopen raw from there.",
    };
  }

  const relatedEntities = buildRelatedEntities(snapshot.relatedEntities, scope);

  if (snapshot.scope === "exploratory" && scope === "official") {
    return {
      state: "scope-hidden",
      question,
      entityId: snapshot.entityId,
      entityType: snapshot.entityType,
      label: snapshot.label,
      status: snapshot.status,
      scope: snapshot.scope,
      message:
        "This entity is exploratory. Switch scope to include exploratory evidence before opening its raw payloads.",
      recoveryPath: buildRawDebugPath(snapshot.entityId, "all"),
      relatedEntities,
    };
  }

  return {
    state: "ready",
    question,
    entityId: snapshot.entityId,
    entityType: snapshot.entityType,
    label: snapshot.label,
    status: snapshot.status,
    scope: snapshot.scope,
    defaultTab: "raw_json",
    tabs: buildTabs(snapshot),
    relatedEntities,
  };
}

export function getRawDebugTabSlugs() {
  return [RAW_JSON_TAB_SLUG, MANIFEST_ENTITY_TAB_SLUG, METADATA_TAB_SLUG] as const;
}
