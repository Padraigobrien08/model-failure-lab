import { TraceRoutePlaceholder } from "@/components/routes/TraceRoutePlaceholder";

const DEFAULT_LANE_ID = "robustness";
const DEFAULT_METHOD_ID = "reweighting";
const DEFAULT_ENTITY_ID = "run_distilbert_reweighting_seed_13";

export function RunPlaceholderPage() {
  return (
    <TraceRoutePlaceholder
      routeLabel="Run"
      routePattern="/run/:runId"
      question="What happened in this run?"
      previousStep={{
        label: "Method",
        path: `/lane/${DEFAULT_LANE_ID}/${DEFAULT_METHOD_ID}`,
      }}
      nextStep={{ label: "Artifact sample", path: `/debug/raw/${DEFAULT_ENTITY_ID}` }}
    />
  );
}
