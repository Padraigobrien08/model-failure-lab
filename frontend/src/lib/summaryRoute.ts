export type SummaryRouteLaneId = "robustness" | "calibration";

export type SummaryRouteMethodId =
  | "baseline"
  | "reweighting"
  | "temperature_scaling"
  | "group_dro";

export type SummaryRouteVerdictStatus = "stable" | "mixed";

export type SummaryRouteLaneStatus = "stable" | "mixed";

export type SummaryRouteMethodStatus = "stable" | "mixed" | "failure";

export type SummaryRouteRowScope = "official" | "exploratory";

export type SummaryRouteMetric = {
  label: string;
  value: number;
  deltaVsBaseline?: number | null;
  lowerIsBetter?: boolean;
};

export type SummaryRouteMethodPreviewRow = {
  methodId: SummaryRouteMethodId;
  label: string;
  status: SummaryRouteMethodStatus;
  summary: string;
  scope: SummaryRouteRowScope;
  headlineMetric: SummaryRouteMetric;
};

export type SummaryRouteLanePanel = {
  laneId: SummaryRouteLaneId;
  label: string;
  status: SummaryRouteLaneStatus;
  summary: string;
  metrics: SummaryRouteMetric[];
  methodPreviewRows: SummaryRouteMethodPreviewRow[];
};

export type SummaryRouteVerdictStrip = {
  status: SummaryRouteVerdictStatus;
  implication: string;
};

export type SummaryRouteSnapshot = {
  verdict: SummaryRouteVerdictStrip;
  laneOrder: SummaryRouteLaneId[];
  lanes: Record<SummaryRouteLaneId, SummaryRouteLanePanel>;
};

export const summaryRouteSnapshot: SummaryRouteSnapshot = {
  verdict: {
    status: "mixed",
    implication:
      "Calibration is stable, but robustness still needs scrutiny before widening the default story.",
  },
  laneOrder: ["robustness", "calibration"],
  lanes: {
    robustness: {
      laneId: "robustness",
      label: "Robustness",
      status: "mixed",
      summary: "Reweighting helps the worst-group story, but the official lane still carries OOD tradeoffs.",
      metrics: [
        {
          label: "Worst-group F1",
          value: 0.477,
          deltaVsBaseline: 0.061,
        },
        {
          label: "OOD Macro F1",
          value: 0.621,
          deltaVsBaseline: -0.018,
        },
      ],
      methodPreviewRows: [
        {
          methodId: "baseline",
          label: "Baseline",
          status: "mixed",
          summary: "Reference point for the lane; stable enough to show the remaining robustness gap clearly.",
          scope: "official",
          headlineMetric: {
            label: "Worst-group F1",
            value: 0.416,
            deltaVsBaseline: 0,
          },
        },
        {
          methodId: "reweighting",
          label: "Reweighting",
          status: "mixed",
          summary: "Best current robustness lane, but not clean enough to call a stable win.",
          scope: "official",
          headlineMetric: {
            label: "Worst-group F1",
            value: 0.477,
            deltaVsBaseline: 0.061,
          },
        },
        {
          methodId: "group_dro",
          label: "Group DRO",
          status: "failure",
          summary: "Exploratory scout regressed the official baseline and stayed outside the promoted path.",
          scope: "exploratory",
          headlineMetric: {
            label: "Worst-group F1",
            value: 0.201,
            deltaVsBaseline: -0.215,
          },
        },
      ],
    },
    calibration: {
      laneId: "calibration",
      label: "Calibration",
      status: "stable",
      summary: "Temperature scaling stays the cleanest, stable lane and keeps calibration risk contained.",
      metrics: [
        {
          label: "ECE",
          value: 0.041,
          deltaVsBaseline: -0.036,
          lowerIsBetter: true,
        },
        {
          label: "Brier",
          value: 0.189,
          deltaVsBaseline: -0.022,
          lowerIsBetter: true,
        },
      ],
      methodPreviewRows: [
        {
          methodId: "baseline",
          label: "Baseline",
          status: "mixed",
          summary: "Reference point before calibration corrections tighten the confidence story.",
          scope: "official",
          headlineMetric: {
            label: "ECE",
            value: 0.077,
            deltaVsBaseline: 0,
            lowerIsBetter: true,
          },
        },
        {
          methodId: "temperature_scaling",
          label: "Temperature Scaling",
          status: "stable",
          summary: "The most reliable official mitigation and the reason calibration is the clean lane to trust.",
          scope: "official",
          headlineMetric: {
            label: "ECE",
            value: 0.041,
            deltaVsBaseline: -0.036,
            lowerIsBetter: true,
          },
        },
        {
          methodId: "reweighting",
          label: "Reweighting",
          status: "mixed",
          summary: "Keeps some calibration gains, but not as cleanly or consistently as temperature scaling.",
          scope: "official",
          headlineMetric: {
            label: "ECE",
            value: 0.058,
            deltaVsBaseline: -0.019,
            lowerIsBetter: true,
          },
        },
      ],
    },
  },
};
