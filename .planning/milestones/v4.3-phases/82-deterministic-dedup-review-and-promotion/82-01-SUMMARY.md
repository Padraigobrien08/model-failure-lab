# 82-01 Summary

- Added deterministic duplicate-group review over harvested draft packs, using normalized prompt
  identity plus authored expectations to avoid collapsing semantically distinct prompt cases.
- Promotion now emits curated dataset packs with stable canonical case ids and explicit promotion
  lineage under `metadata.harvest`.
- Drafts remain immutable review inputs; promotion writes the curated output separately.
