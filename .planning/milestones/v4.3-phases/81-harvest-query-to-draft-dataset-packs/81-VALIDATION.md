# Phase 81 Validation

- Unit coverage proves harvested draft packs preserve canonical prompt expectations plus per-case
  provenance.
- CLI coverage proves `failure-lab harvest` works for both query-selected failures and
  comparison-delta selections.
- Existing dataset parsing and query-index tests still pass, proving the harvest contract does not
  regress the current runner or retrieval surfaces.
