# Screens

Screenshots of the operator console (`frontend/`), captured at 1440×900 against a real
`failure-lab` workspace — the bundled regression demo plus two `demo` model runs.

| File | Screen |
|---|---|
| `runs-inventory.png` | The saved-runs inventory the console opens on: dataset filters, per-run metrics, two-run selection. |
| `run-detail.png` | One saved run: failure rate, coverage, case lenses, and the per-case inspector. |
| `comparison-detail.png` | Baseline vs candidate, verdict first: the CI-gate tile with its block reason, signed delta cards, top drivers with evidence chips, and grouped case transitions. |
| `evidence.png` | Case evidence: baseline and candidate side by side with the classifier's "why it failed" note. |
| `gate-dark.png` | The regression gate in the dark theme, showing a red block (a regression) and an amber one (runs not comparable) at once — red is reserved for regressions only (`frontend/DESIGN.md`). |

To recapture, point the console at a workspace and take 1440px-wide shots:

```bash
FAILURE_LAB_ARTIFACT_ROOT=/path/to/workspace npm --prefix frontend run dev
```

The shell prints the package version, so a screenshot from a stale checkout shows it. After
recapturing, write the new version into `CAPTURED_AT` — `test_version_consistency.py` pins
that file to `pyproject.toml`, because this instruction on its own did not hold: the screens
were recaptured and the version bumped in the very next commit, and every image shipped a
release behind.
