# Phase 85 Validation

- Build one improved comparison and verify the persisted signal verdict is `improvement`, the
  improvement score is positive, and top drivers include signed failure-type deltas with case ids.
- Build one regressed comparison and verify the persisted signal verdict is `regression`, the
  regression score is positive, and top drivers surface the regressing failure type first.
- Build one incompatible comparison and verify the signal block degrades deterministically to
  `incompatible` with zero scores and no drivers.
- Rebuild the query index and verify the new comparison signal fields survive ingestion.
