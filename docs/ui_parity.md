# UI Parity Guide

This repo currently ships two local UI surfaces over the same artifact contract:

- React failure debugger: primary UI
- Streamlit results explorer: temporary fallback

Both read from the saved manifest at `artifacts/contracts/artifact_index/v1/index.json`. During the
transition, the goal is not perfect visual sameness. The goal is parity of conclusions, rankings,
scope behavior, and drillthrough paths.

## Launch Paths

Primary React UI:

```bash
npm install --prefix frontend
python3 scripts/run_react_ui.py
```

Fallback Streamlit UI:

```bash
python3 -m pip install -e '.[ui]'
python3 scripts/run_results_ui.py
```

## What Should Match

### Overview

Both UIs should communicate the same official story:

- `temperature_scaling` is the stable calibration lane
- `reweighting` remains the best current robustness lane, but still mixed
- dataset expansion remains deferred under explicit reopen conditions

### Comparisons

Both UIs should preserve the same method ordering and interpretation:

- `temperature_scaling` ahead on reliability/calibration
- `reweighting` as the mixed robustness lane
- baseline as the reference lane

### Failure Analysis

Both UIs should keep the same evidence families visible:

- worst-group
- OOD
- ID
- calibration

### Evidence Scope

Both UIs should keep the same scope rule:

- official evidence is the default
- exploratory evidence appears only when explicitly enabled

## Known Differences

- React is the richer debugging surface and includes:
  - ranked comparison canvas
  - four-tab failure explorer
  - grouped run cards
  - reusable evidence drawer
- Streamlit is the legacy fallback and keeps a more report/browser-oriented structure.
- React may organize the same evidence differently, but it should not change the underlying
  conclusions or official-versus-exploratory boundaries.

## Troubleshooting

### React launcher fails immediately

Check:

```bash
npm install --prefix frontend
python3 scripts/run_react_ui.py --help
```

If the launcher still fails, try the direct frontend path:

```bash
npm --prefix frontend run dev
```

### Streamlit fallback fails

Check:

```bash
python3 -m pip install -e '.[ui]'
python3 scripts/run_results_ui.py --help
```

### The UIs seem to disagree

Verify:

1. Both are reading the current manifest at `artifacts/contracts/artifact_index/v1/index.json`
2. Exploratory scope is either off in both or on in both
3. You are comparing the same route family:
   - overview to overview
   - comparison/failure surface to comparison/failure surface

If the disagreement persists, rebuild the React-served manifest copy:

```bash
python3 scripts/sync_react_ui_manifest.py --check
```

Then restart the React UI.
