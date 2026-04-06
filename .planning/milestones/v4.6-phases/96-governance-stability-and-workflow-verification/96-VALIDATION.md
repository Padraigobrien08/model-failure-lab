# 96 Validation

## Must Pass

1. A newly created comparison artifact can be recommended, reviewed, and applied without any manual
   fixture editing.
2. Re-running governance apply on the same local artifacts stays deterministic and does not create
   duplicate dataset versions.
3. Dataset-family health reflects the applied governance action and points back to the source
   comparison.
4. Frontend smoke over a real artifact root verifies governance recommendation payloads on both the
   comparison detail payload and analysis signal query payloads.

## Automated Proof

- python governance workflow tests over fresh comparison artifacts
- CLI governance and recommendation regression tests
- frontend smoke over demo artifacts
