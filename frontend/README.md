# Failure Lab operator console

A local-first React UI over the engine's saved artifacts. It renders what the CLI wrote —
runs, comparison reports, datasets, governance records — and never invents data: every number
on screen traces to a JSON artifact under the active workspace.

```bash
FAILURE_LAB_ARTIFACT_ROOT=/path/to/your/workspace npm --prefix frontend run dev
```

## Architecture

```
vite dev/preview server ──▶ scripts/query_bridge.py ──▶ model_failure_lab (Python)
        │                            │
        │   /__failure_lab__/artifacts/*.json                │ reads workspace artifacts:
        ▼                            ▼                       │ runs/ reports/ datasets/
React app (src/)              JSON over stdout               │ governance/ .failure_lab/
```

- **`server/artifactBridge.ts`** is the artifact bridge: each
  `/__failure_lab__/artifacts/*.json` endpoint shells into `scripts/query_bridge.py` against
  `FAILURE_LAB_ARTIFACT_ROOT` (default: repo root), and `comparison-detail` / `run-detail`
  are composed here from the saved artifacts. It checks the request's `Host` and, for the
  three write endpoints, requires a same-origin POST. `vite.config.ts` mounts it on both the
  dev and the preview server, so the built app works too.
  `server/__tests__/artifactBridge.test.ts` drives it over real HTTP.
- **`src/lib/artifacts/`** is the typed contract layer: `load.ts` + `extended.ts` validate
  every payload field-by-field and throw with a field path on drift. UI code never touches
  raw JSON.
- **`src/app/routes/`** one file per screen; **`src/components/console/`** shared primitives
  (buttons, chips, segmented controls, empty states, formatters) and the harvest dialog;
  **`src/components/layout/ConsoleShell.tsx`** the 216px rail + content column shell.
- **`src/styles/index.css`** carries both theme token sets (light/dark) behind
  `[data-theme]`; `tailwind.config.ts` maps them to utility names. Radius is a theme token
  (0px light, 8px dark). Design rules live in [`DESIGN.md`](DESIGN.md).

## Routes

| Route | Screen |
| --- | --- |
| `/` | Saved runs inventory + two-run comparison selection |
| `/runs/:runId` | Run detail: metrics, lenses, case table, case inspector |
| `/comparisons` | Comparison inventory |
| `/comparisons/:reportId` | Verdict-first comparison: gate banner, delta cards, drivers, transitions/matrix, governance |
| `/comparisons/:reportId/evidence` | Case evidence: rail + baseline/candidate side-by-side |
| `/evidence` | Cross-artifact explorer over the derived SQLite index (cases/deltas/aggregates/signals/clusters) |
| `/datasets` | Dataset families |
| `/datasets/:familyId` | Family detail: versions, health, lifecycle, portfolio, plans, executions, outcomes |
| `/gate` | Regression gate: policy + per-comparison decisions and waivers |

State that matters is URL-addressable (`q`, `dataset`, `model`, `status`, `mode`, `section`,
`caseId`, `transition`, `lens`, `clusterId`), so a CI link can deep-link into a failing case.
Writes are limited to the three deterministic dataset endpoints (harvest draft, regression
pack, evolve); everything else is read-only. The bridge is a localhost development surface:
it answers only for loopback hosts, and its write endpoints require a same-origin POST.

## Commands

```bash
npm --prefix frontend run dev        # dev server (port 5174)
npm --prefix frontend run build      # typecheck + vite build
npm --prefix frontend test           # vitest
npm --prefix frontend run smoke:real-artifacts   # end-to-end against a real workspace
```
