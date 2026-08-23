# Screens

Screenshots of the operator console (`frontend/`), captured against a real
`failure-lab` workspace (the bundled regression demo plus a `demo` model run).

- `comparison-detail.png` — baseline-vs-candidate comparison report: verdict,
  failure-rate delta, governance recommendation, and matched dataset family.
- `run-detail.png` — a saved run opened in the run detail view: failure rate,
  coverage, and the staged investigation flow.
- `runs-inventory.png` — the saved-runs inventory the UI opens on.

To recapture: point the UI at a workspace and take 1440px-wide screenshots.

```bash
FAILURE_LAB_ARTIFACT_ROOT=/path/to/workspace npm --prefix frontend run dev
```
- `evidence.png` — case evidence: baseline/candidate side-by-side with the classifier's "why it failed" note.
