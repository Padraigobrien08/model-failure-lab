# Phase 81 Research

- Current dataset loading already tolerates canonical envelopes, so extending the dataset contract
  is lower risk than introducing a second draft-pack loader.
- The query index is intentionally lossy relative to full prompt expectations, so harvest must
  rehydrate prompt cases from saved run artifacts after selection.
- The deterministic insight fixture workspace already covers both cross-run failure queries and
  comparison deltas, making it the right backbone for harvest validation.
