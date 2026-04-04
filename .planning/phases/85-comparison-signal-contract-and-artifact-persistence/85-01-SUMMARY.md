# 85-01 Summary

- Added a deterministic comparison signal block with verdict, regression score, improvement score,
  severity, and top drivers.
- Persisted the same signal payload into both summary and detail comparison artifacts.
- Extended the SQLite query index to mirror signal verdicts, scores, and ranked driver rows with a
  compatibility fallback for older comparison artifacts that do not yet store signals.
