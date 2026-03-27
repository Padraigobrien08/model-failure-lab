import { TraceRoutePlaceholder } from "@/components/routes/TraceRoutePlaceholder";

export function VerdictPlaceholderPage() {
  return (
    <TraceRoutePlaceholder
      routeLabel="Verdict"
      routePattern="/"
      question="Where should I look?"
      previousStep={{
        label: "Artifact sample",
        path: "/debug/raw/run_distilbert_reweighting_seed_13",
      }}
      nextStep={{ label: "Lane sample", path: "/lane/robustness" }}
    />
  );
}
