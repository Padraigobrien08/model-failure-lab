# 97 Research

- The existing `query_index_v2` schema did not retain enough run metrics or dataset lineage to
  answer longitudinal questions deterministically.
- The cheapest stable seam was to extend the current derived index to `query_index_v3` with:
  - run metric columns
  - dataset-version lineage rows
  - dataset JSON mtime participation in rebuild invalidation
- That keeps the history layer local, rebuildable, and aligned with the established artifact-root
  contract.
