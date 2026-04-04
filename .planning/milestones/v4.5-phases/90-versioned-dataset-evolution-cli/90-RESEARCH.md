# 90 Research

- The cleanest family-history representation is metadata inside the canonical dataset envelope rather
  than a sidecar registry file.
- Version listing can stay filesystem-native by scanning canonical dataset files and reading the
  explicit `metadata.versioning` block.
- The replay loop should continue to consume versioned datasets through the normal `datasets list`
  and `run --dataset ...` path instead of a special evolution-only runner path.
