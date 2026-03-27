import { useParams } from "react-router-dom";

import { TraceRoutePlaceholder } from "@/components/routes/TraceRoutePlaceholder";

const DEFAULT_LANE_ID = "robustness";
const DEFAULT_METHOD_ID = "reweighting";

export function LanePlaceholderPage() {
  const { laneId = DEFAULT_LANE_ID } = useParams();

  return (
    <TraceRoutePlaceholder
      routeLabel="Lane"
      routePattern="/lane/:laneId"
      question="Why is this lane in focus?"
      previousStep={{ label: "Verdict", path: "/" }}
      nextStep={{ label: "Method sample", path: `/lane/${laneId}/${DEFAULT_METHOD_ID}` }}
    />
  );
}
