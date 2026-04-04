# 101 Validation

- Rebuilding the query index twice must yield the same ordered cluster ids and payloads.
- Cluster ids must distinguish `run_case` and `comparison_delta` scopes.
- Recurring clusters must be filtered by distinct artifact scope count rather than raw row count.
