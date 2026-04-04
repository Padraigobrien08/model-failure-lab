# 81-01 Summary

- Extended the canonical dataset envelope with optional `created_at`, `lifecycle`, and `source`
  fields so harvested draft packs remain first-class dataset files.
- Added the new `model_failure_lab.harvest` pipeline that selects cases through the derived query
  index, rehydrates canonical prompt content from saved run artifacts, and writes draft dataset
  packs with explicit provenance metadata.
- Kept draft case ids deterministic and source-specific so repeated harvest runs over the same
  artifact root are stable without prematurely collapsing duplicates before Phase 82 review.
