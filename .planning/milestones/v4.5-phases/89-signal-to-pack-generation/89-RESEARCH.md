# 89 Research

- The saved comparison signal contract already contains the minimum stable ingredients needed for
  deterministic pack composition: verdict, severity, ranked drivers, and case ids.
- Existing harvest work in `v4.3` proved that canonical dataset envelopes can carry provenance
  without breaking runner compatibility.
- The cleanest addition is a new dataset-evolution module that reuses saved artifacts and index
  selection instead of teaching the existing harvest module about signal-family semantics.
