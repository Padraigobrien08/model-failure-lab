import { TraceRoutePlaceholder } from "@/components/routes/TraceRoutePlaceholder";

const DEFAULT_RUN_ID = "distilbert_reweighting_seed_13";

export function RawDebugPlaceholderPage() {
  return (
    <TraceRoutePlaceholder
      routeLabel="Artifact"
      routePattern="/debug/raw/:entityId"
      question="What artifact backs this entity?"
      previousStep={{ label: "Run", path: `/run/${DEFAULT_RUN_ID}` }}
      nextStep={{ label: "Verdict", path: "/" }}
    />
  );
}
