# CI and Governance Gates

This document describes how to run reliability checks in CI and locally.

## Baseline CI Commands

Current CI workflow runs:

- `python3 -m pytest -q`
- `python3 -m ruff check src tests`
- `python3 -m pip install .`
- CLI smoke flow (`demo`, `datasets list`, `run`, `report`, `index validate`)

## Regression Gate Mode

Use gate mode to evaluate whether current saved comparison signals should block a release.

```bash
failure-lab regressions gate --strict-exit
```

- Exit code `0`: gate passes
- Exit code `2`: gate blocked (when `--strict-exit` is set)

## Policy-as-code

You can load policy values from a YAML file:

```bash
failure-lab regressions gate --policy-file .failure_lab/policy.yaml --strict-exit
```

Example policy file:

```yaml
minimum_severity: 0.05
top_n: 10
failure_type: null
family_id: null
family_case_cap: 200
max_duplicate_ratio: 0.6
recurrence_window: 5
recurrence_threshold: 2
strategy: exact_suggested_family_then_health_guards
```

## Waivers

Waivers allow temporary exceptions by comparison ID.

```bash
failure-lab regressions gate --waivers .failure_lab/waivers.json --strict-exit
```

Example waiver file:

```json
{
  "waivers": [
    {
      "comparison_id": "report_20260427_123000_candidate_vs_baseline",
      "reason": "Known issue under active remediation",
      "owner": "ml-platform",
      "expires_at": "2026-12-31T23:59:59Z"
    }
  ]
}
```

Expired waivers are treated as inactive.

## PR Reliability Comment

Generate markdown suitable for PR discussion:

```bash
failure-lab regressions pr-comment --baseline-run <run-id> --candidate-run <run-id>
```

This outputs a concise reliability diff and top signal drivers.
