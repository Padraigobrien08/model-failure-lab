# Milestones

## v3.0 Packaged Engine And Ollama Adapter Reach (Shipped: 2026-04-03)

**Phases completed:** 3 phases, 6 plans, 12 tasks  
**Git range:** `b3bb710` -> `a1bfa28`  
**Diff:** 27 files changed, 2219 insertions(+), 164 deletions(-)  
**Timeline:** 2026-04-02 -> 2026-04-03

**Key accomplishments:**
- Standardized the install-first `failure-lab` path with cwd-root artifact defaults and explicit packaged-asset errors.
- Added a temp-venv smoke that proves the installed `failure-lab` console script through `demo`, `run`, `report`, and `compare`.
- Added a built-in Ollama HTTP adapter while preserving the shared run/report/compare artifact contract.
- Exposed explicit Ollama CLI configuration and localhost-stub proof for the full saved-artifact loop.
- Made the debugger honest about configured external artifact roots and protected that contract with route regressions.
- Proved both installed-package and Ollama-backed artifacts through the same debugger workflow and `FAILURE_LAB_ARTIFACT_ROOT` handoff.

**Archive basis:** No standalone `v3.0` milestone audit file was present. Closeout used `roadmap analyze` (`100%`, `6/6` plans complete) plus the verification artifacts from Phases 67-69.

---
