# 88 Validation

## Must Prove

- Repeating the same comparison preserves the same persisted signal payload.
- Rebuilding the query index keeps the comparison signal query surface stable and queryable.
- The debugger route bundle and production build still pass with signal severity features enabled.
- The real-artifacts smoke verifies comparison signals and `/analysis?mode=signals` through the
  live middleware path.
