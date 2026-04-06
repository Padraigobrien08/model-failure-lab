# 96 Research

- Existing governance unit tests already prove recommendation logic, family matching, and
  deterministic skip behavior over the fixture workspace.
- Existing CLI signal tests already prove persisted comparison signals and repeat-compare stability.
- The missing proof is a single integrated loop that starts with a fresh `compare` artifact,
  exercises the governance CLI surfaces against that new comparison, and confirms the resulting
  dataset-family state.
- The frontend smoke already verifies overview, inventories, detail routes, and analysis query
  endpoints from a real artifact root; extending it to assert governance payload presence is the
  lowest-cost debugger proof.
