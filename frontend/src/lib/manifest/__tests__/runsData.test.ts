import {
  buildEvidenceSections,
  buildRunDetailModel,
  buildRunLaneModels,
  getRepresentativeRunIdForMethod,
} from "@/lib/manifest/selectors";
import {
  buildFinalRobustnessBundleFixture,
  buildManifestFixture,
} from "@/test/fixtures";

describe("runsData manifest selectors", () => {
  it("groups runs by method lane and seed from manifest entities", () => {
    const manifest = buildManifestFixture();
    const bundle = buildFinalRobustnessBundleFixture();

    const lanes = buildRunLaneModels(manifest, bundle);

    expect(lanes.map((lane) => lane.laneKey)).toEqual([
      "baseline",
      "temperature_scaling",
      "reweighting",
    ]);
    expect(lanes[0]?.seedGroups.map((group) => group.seedLabel)).toEqual([
      "Seed 13",
      "Seed 42",
      "Seed 87",
    ]);
    expect(lanes[1]?.seedGroups[0]?.runs[0]?.runId).toBe("temperature_seed_13");
  });

  it("builds balanced run detail and evidence sections without recomputing metrics", () => {
    const manifest = buildManifestFixture();
    const bundle = buildFinalRobustnessBundleFixture();

    const detail = buildRunDetailModel(manifest, bundle, "reweighting_seed_13");
    const representativeRunId = getRepresentativeRunIdForMethod(manifest, "reweighting", true);
    const sections = buildEvidenceSections(manifest, bundle, true);

    expect(representativeRunId).toBe("reweighting_seed_13");
    expect(detail?.lineage.map((item) => item.label)).toEqual([
      "Parent run",
      "Method lane",
      "Experiment group",
      "Cohort membership",
    ]);
    expect(detail?.metrics.map((metric) => metric.label)).toEqual([
      "Worst Group",
      "OOD",
      "ID",
      "Calibration",
    ]);
    expect(detail?.actionGroups.map((group) => group.title)).toEqual([
      "Run artifacts",
      "Evaluation artifacts",
      "Supporting report",
    ]);
    expect(sections.map((section) => section.key)).toEqual(["reports", "evaluations", "runs"]);
  });
});
