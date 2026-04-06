# Milestones

## v5.2 Guided Plan Execution And Outcome Verification (Shipped: 2026-04-06)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added a dedicated saved-plan execution contract with preflight checks, before/after family
  snapshots, persisted checkpoints, and execution receipts.
- Added CLI execution surfaces for plan preflight, stepwise or bounded-batch execution, receipt
  listing, and detailed receipt inspection.
- Added prepared rerun/compare guidance and rollback messaging to saved-plan execution outcomes so
  operators can verify results explicitly.
- Surfaced latest execution context on the existing automation panel and sticky operator summary,
  then closed the milestone with governance, route-suite, and production-build verification.

---

## v5.1 Operator Workflow Clarity And Triage Surfaces (Shipped: 2026-04-06)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Moved governance, escalation, lifecycle, family, and portfolio-priority context into the saved
  comparison inventory with operator-first triage lenses and ordering.
- Added a sticky operator summary rail and decomposed decision surfaces on comparison detail so
  recommendation, action, family state, and supporting evidence stay easier to parse.
- Added URL-backed `/analysis` intent presets plus stronger shell workspace orientation, keeping
  artifact-root trust and workflow entry points visible across routes.
- Closed the milestone with route-suite and build verification, along with the router future-flag
  opt-in and insight-panel duplicate-key stability fixes.

---

## v5.0 Portfolio Prioritization And Guided Lifecycle Planning (Shipped: 2026-04-05)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added deterministic portfolio ranking across existing dataset families with explicit comparison,
  cluster, and lifecycle rationale.
- Added inspectable planning units plus saved dry-run portfolio plans with bounded family actions,
  dependencies, and projected impact.
- Added CLI queue, planning-unit, saved-plan, and explicit plan-promotion workflows under the
  existing dataset command family.
- Surfaced portfolio priority and saved-plan context on the existing automation panel and proved
  the full `queue -> saved plan -> explicit promote/apply -> family state` loop with backend and
  frontend verification.

---

## v4.9 Proactive Escalation And Dataset Lifecycle Management (Shipped: 2026-04-05)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added deterministic escalation statuses and dataset-family lifecycle recommendations over
  recurring clusters, history, and family-health evidence.
- Added explicit CLI lifecycle review/apply flows with persisted lifecycle action records and
  active family-state inspection.
- Surfaced escalation and lifecycle context on existing debugger analysis and comparison routes,
  with family lifecycle history available through the artifact bridge.
- Proved the full `history -> cluster -> escalation -> lifecycle action -> family state` loop with
  Python tests, frontend regressions, build, and real-artifact smoke.

---

## v4.8 Recurring Failure Clusters And Pattern Mining (Shipped: 2026-04-04)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added deterministic recurring cluster identity over saved run failures and comparison deltas.
- Added cluster summaries, detailed history, and direct CLI inspection surfaces for recurring
  patterns.
- Added lightweight debugger cluster surfacing on `/analysis` and comparison enforcement views.
- Proved the full `history -> cluster -> governance -> debugger evidence` loop with Python tests,
  frontend regressions, build, and real-artifact smoke.

---

## v4.7 Model Behavior Tracking And Dataset Health Over Time (Shipped: 2026-04-04)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added a deterministic history layer over saved runs, comparisons, and dataset families using the
  derived local artifact index.
- Added deterministic trend, volatility, recurrence, and dataset-health summaries over that
  history.
- Added `failure-lab history`, history-aware governance recommendations, and bridge payloads for
  time-aware debugger views.
- Proved the full `history -> trend -> governance context` loop with Python tests, frontend route
  regressions, production build, and real-artifact smoke.

---

## v4.6 Regression Governance And Recommendation Layer (Shipped: 2026-04-04)

**Phases completed:** 4 phases, 8 plans

**Key accomplishments:**
- Added deterministic governance recommendations that classify saved comparison signals as
  `create`, `evolve`, or `ignore`.
- Added governance review/apply CLI workflows plus dataset-family health inspection over recent
  comparisons.
- Surfaced recommendation status, rationale, and matched-family context directly on debugger
  signal surfaces and comparison detail.
- Proved the full `compare -> recommend -> review/apply -> dataset action` loop with Python tests,
  frontend regressions, production build, and real-artifact smoke.

---

## v4.5 Dataset Evolution And Regression Pack Automation (Shipped: 2026-04-04)

**Phases completed:** 4 phases, 8 plans

**Key accomplishments:**
- Added deterministic regression-pack generation directly from persisted comparison signals.
- Added immutable dataset-family evolution, lineage inspection, and stable duplicate collapse in the
  CLI.
- Added debugger enforcement surfaces for pack generation, family evolution, and version-history
  provenance drillback.
- Proved the full `compare -> signal -> generate/evolve -> run -> compare` enforcement loop with
  Python tests, frontend regressions, build, and real-artifact smoke.

---

## v4.4 Regression Detection And Signal Layer (Shipped: 2026-04-04)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added deterministic comparison signal blocks with verdict, severity, and top-driver metadata.
- Added raw score, summary, alert, and severity-ranked listing surfaces in the CLI.
- Added debugger severity surfacing in comparison inventory/detail routes and `/analysis` signal
  mode.
- Proved signal stability across repeated compare operations, index rebuilds, route regressions,
  production build, and real-artifact smoke.

---

## v4.3 Failure Harvesting And Dataset Pack Generation (Shipped: 2026-04-04)

**Phases completed:** 4 phases, 8 plans

**Key accomplishments:**
- Added query-compatible harvesting from saved runs, analysis results, and comparison delta slices.
- Added deterministic draft review, deduplication, curated promotion, and local harvested dataset
  discovery.
- Added lightweight debugger export from `/analysis` and comparison detail into draft dataset
  packs.
- Proved the full `artifact -> harvest -> curated dataset -> rerun -> compare -> insight` loop.

---

## v4.2 Insight Layer And Grounded Failure Interpretation (Shipped: 2026-04-03)

**Phases completed:** 4 phases, 8 plans

**Key accomplishments:**
- Added grounded heuristic insight reports over case, delta, aggregate, and comparison result sets.
- Added `failure-lab query --summarize` and `failure-lab compare --explain` with heuristic default
  and explicit LLM opt-in.
- Added shared debugger insight panels with clickable evidence drillthrough.

---

## v4.1 Artifact Query And Cross-Run Analysis Layer (Shipped: 2026-04-03)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**
- Added a derived local query index over runs, cases, comparisons, and case deltas.
- Added `failure-lab index rebuild` and `failure-lab query`.
- Added a query-backed `/analysis` debugger route with URL-backed filters and evidence drillthrough.

---

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

## v2.1 Cross-Artifact Drillthrough And Debugger Operability (Shipped: 2026-04-02)

**Phases completed:** 3 phases, 6 plans, 12 tasks

**Key accomplishments:**

- Made run and comparison detail URLs shareable and reload-safe with exact section, lens, and
  case restoration.
- Added lightweight section jumps and mount-aware deep-link landing across both detail routes.
- Added exact comparison-case drillthrough into baseline and candidate run evidence with preserved
  return context.
- Made degraded drillthrough explicit and surfaced compact artifact context on focused evidence
  panels.
- Consolidated route provenance, unified `Active case` cues, and closed the milestone with route
  regressions, build, smoke, and `66-VERIFICATION.md`.

---

## v2.0 React Debugger On Real Artifacts (Shipped: 2026-03-31)

**Phases completed:** 7 phases, 14 plans, 29 tasks

**Key accomplishments:**

- Replaced the legacy manifest-first frontend shell with a runs-first artifact-backed React app
  over real engine outputs.
- Shipped saved runs inventory plus run-detail drilldown with failure shape, notable cases, and
  selected evidence over real report artifacts.
- Shipped saved comparison inventory and comparison-detail exploration with grouped directional
  deltas and run-linked context.
- Recovered richer debugger guidance and detail density without reopening the old benchmark route
  model.
- Closed missing planning evidence and validation gaps so the milestone audit passed cleanly with
  all requirements satisfied.

---

## v1.9 Failure Dataset Packs And Report Quality (Shipped: 2026-03-30)

**Phases completed:** 5 phases, 10 plans, 20 tasks

**Key accomplishments:**

- Canonicalized prompt expectations and failure taxonomy so authored datasets, classifiers, runner
  artifacts, and reports all speak one contract.
- Shipped bundled reasoning, hallucination, and RAG dataset packs plus registry-driven dataset
  discovery through `failure-lab datasets list`.
- Made single-run reports explain themselves with mismatch-aware summaries, tag slices, and bounded
  notable examples.
- Made directional comparisons surface grouped case-transition deltas instead of only aggregate
  metric movement.
- Rewrote the repo entrypoint around the engine-first quickstart so users can install, demo,
  discover datasets, run one, and inspect the output quickly.

---

## v1.8 Core Failure Analysis Engine (Shipped: 2026-03-30)

**Phases completed:** 8 phases, 16 plans, 26 tasks

**Key accomplishments:**

- Turned the repo into a real CLI-first failure analysis engine with canonical schemas, local JSON
  artifact storage, and deterministic runner/reporting contracts.
- Added deterministic demo and OpenAI adapter seams, one heuristic classifier path, and explicit
  model/classifier registries.
- Shipped `failure-lab demo`, `failure-lab run`, `failure-lab report`, and
  `failure-lab compare`, all backed by the same saved artifact model.
- Closed post-audit cleanup around validation hygiene, reporting import weight, runtime warning
  noise, and run identity collisions.

---

## v1.7 Trace-First Failure Debugger Rebuild (Shipped: 2026-03-27)

**Phases completed:** 8 phases, 16 plans, 32 tasks

**Key accomplishments:**

- Reset the React frontend around a strict trace chain with dedicated `Summary`, `Lane`, `Method`,
  `Run`, and `Raw` routes plus shared `Official` / `All` scope state.
- Built a compact verdict-first summary page and a table-first lane workspace that preserve
  baseline anchoring, grouped runs, and deterministic inspector-driven drilldown.
- Added focused method and run detail routes with structured explanation, lineage, artifact
  summaries, and explicit forward handoff into raw evidence.
- Added a real raw-debug route with monospaced payload tabs, related-entity traversal, copy
  support, and one shared inspector contract across lane, method, and run.
- Completed trustworthy official-versus-exploratory scope semantics and a final audit pass that
  reduced dashboard drift without reopening the route architecture.

---

## v1.5 React Failure Debugger UI (Shipped: 2026-03-25)

**Phases completed:** 4 phases, 8 plans, 16 tasks

**Key accomplishments:**

- Built a dedicated React workspace with Vite, TypeScript, Tailwind, shadcn, and a deterministic
  manifest sync bridge over the existing artifact index.
- Added a real Overview launchpad, ranked `Comparisons`, and four-tab `Failure Explorer` routes
  backed by saved report payloads rather than client-side recomputation.
- Added grouped `Runs`, reusable evidence-drawer drillthrough, and an official-first `Evidence`
  browser so users can inspect lineage, summaries, and raw artifacts in one connected workflow.
- Preserved official-versus-exploratory scope boundaries across the React shell with explicit
  controls and warnings.
- Handed the repo off to React as the primary UI with a root-level launcher, updated README, and a
  documented Streamlit fallback/parity path.

---

## Earlier Milestones

- `v1.4` Final Robustness Attempt Before Expansion
- `v1.3` Artifact-Driven Results UI And Robustness Consolidation
- `v1.2` Seed Stability And Reweighting Validation
- `v1.1` Live Benchmark Validation And Research Packaging
- `v1.0` MVP
