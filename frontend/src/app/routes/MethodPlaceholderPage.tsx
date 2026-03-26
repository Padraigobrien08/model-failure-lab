import { useParams } from "react-router-dom";

import { TraceRoutePlaceholder } from "@/components/routes/TraceRoutePlaceholder";

const DEFAULT_LANE_ID = "robustness";
const DEFAULT_RUN_ID = "distilbert_reweighting_seed_13";

export function MethodPlaceholderPage() {
  const { laneId = DEFAULT_LANE_ID } = useParams();

  return (
    <TraceRoutePlaceholder
      routeLabel="Method"
      routePattern="/lane/:laneId/:methodId"
      question="Why is this method judged this way?"
      previousStep={{ label: "Lane", path: `/lane/${laneId}` }}
      nextStep={{ label: "Run sample", path: `/run/${DEFAULT_RUN_ID}` }}
    />
  );
}
