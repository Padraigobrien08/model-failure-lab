# 88 Research

- Existing signal tests already covered artifact construction and CLI rendering; the main remaining
  gap was end-to-end stability across repeated compare operations and index rebuilds.
- The real-artifacts smoke script already enforced latency budgets and artifact-root correctness, so
  extending it to `signals` provided milestone-level proof without a second custom harness.
