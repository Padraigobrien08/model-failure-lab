import { loadFinalRobustnessBundle } from "@/lib/manifest/reportData";
import { parseArtifactJson } from "@/lib/manifest/load";
import { buildManifestFixture } from "@/test/fixtures";

describe("comparisonsData manifest bridge", () => {
  it("loads the final robustness bundle from manifest-linked payload refs", async () => {
    const manifest = buildManifestFixture();
    const requestedPaths: string[] = [];
    const fetchMock = vi.fn(async (path: string) => {
      requestedPaths.push(path);

      if (path.endsWith("/report_data.json")) {
        return {
          ok: true,
          text: async () =>
            JSON.stringify({
              official_method_summaries: [],
              exploratory_method_summaries: [],
              worst_group_summary: [],
              ood_summary: [],
              id_summary: [],
              calibration_summary: [],
            }),
        } as Response;
      }

      return {
        ok: true,
        text: async () =>
          JSON.stringify({
            headline_findings: [],
            official_methods: [],
            exploratory_methods: [],
          }),
      } as Response;
    });

    const bundle = await loadFinalRobustnessBundle(manifest, fetchMock as typeof fetch);

    expect(bundle.report.report_scope).toBe("phase26_robustness_final");
    expect(requestedPaths).toContain("/artifacts/reports/phase26/report_data.json");
    expect(requestedPaths).toContain("/artifacts/reports/phase26/report_summary.json");
  });

  it("parses report payload JSON even when report artifacts contain NaN tokens", () => {
    const payload = parseArtifactJson<{ worst_group_summary: Array<{ std: number | null }> }>(
      '{"worst_group_summary":[{"std":NaN}]}',
      "/artifacts/reports/phase26/report_data.json",
    );

    expect(payload.worst_group_summary[0]?.std).toBeNull();
  });
});
