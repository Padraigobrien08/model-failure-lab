# 87 Research

- The persisted signal contract from Phase 85 was sufficient for debugger use; no additional
  backend schema change was required.
- The main frontend risk was shape drift between raw bridge payloads and client-side typed state,
  especially for nested `top_drivers` rows.
- Existing detail-route deep-link state made signal-to-evidence handoff cheap once driver case ids
  were persisted.
