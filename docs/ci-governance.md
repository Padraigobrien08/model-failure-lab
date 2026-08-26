# CI and governance gates

How to fail a build on a regression, and how to get the build green again.

## One gate contract

`compare --gate`, `regressions gate`, and the operator console's gate screen all call
`evaluate_gate_conditions` (`governance/gates.py`). They block on the same four conditions,
in this order, first hit wins:

| Condition | Block reason |
|---|---|
| The runs are not comparable | `runs are not comparable` |
| The signal verdict is a regression | `signal verdict: regression` |
| Execution success or classification coverage dropped | `execution success regressed by -12.5%` |
| The candidate dropped cases the baseline failed | `candidate dropped 2 baseline failing case(s): …` |

The last three are fail-closed: a candidate cannot pass by erroring, by failing to classify,
or by deleting the cases it broke.

Only the second is a *regression*. The console colours the other three amber, not red — see
`frontend/DESIGN.md`.

An active waiver turns any of them into a PASS, on every surface, and the verdict line names
what it suppressed: `Gate: PASS (waived by padraig: JIRA-123) [would block: signal verdict:
regression]`. An expired one is reported as expired rather than ignored.

## Gating a build

The simplest form gates one comparison and exits non-zero on a block:

```bash
failure-lab compare <baseline-run> <candidate-run> --gate
```

`--format markdown` renders a PR-ready verdict table from the same command. The repo ships a
composite GitHub Action (`action.yml`) that wraps both and writes the verdict to the job
summary:

```yaml
- uses: Padraigobrien08/model-failure-lab@main
  with:
    baseline: eval/runs/baseline
    candidate: eval/runs/candidate
```

To gate on every recent comparison in a workspace rather than one pair, use the governance
gate. It reads the derived index, so rebuild it first:

```bash
failure-lab index rebuild
failure-lab regressions gate --strict-exit
```

- Exit `0`: nothing blocks.
- Exit `2`: at least one comparison blocks (only with `--strict-exit`).

## Policy as code

`regressions gate` discovers a committed policy file automatically — `governance/policy.yml`,
then `.yaml`, then `.json` — and falls back to built-in defaults. `--policy-file` overrides
the discovery. Whichever applies is reported as `policy_source`, on the CLI and in the
console, so no screen can claim "built-in defaults" over a policy that is actually in force.

```yaml
# governance/policy.yml
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

The severity floor governs dataset-governance decisions — whether to create or evolve a
family — and never whether CI turns green. The gate contract above is the only thing that
decides that.

## Waivers: getting a red gate green again

The gate evaluates every recent comparison in the workspace and blocks fail-closed, so one
accidental cross-dataset `compare` leaves it red until you say why that should not count.
A waiver records the reason, which deleting the report artifact would not.

```bash
failure-lab regressions waive <comparison-id> \
  --reason "support-assistant v2 regression, fix tracked in JIRA-123" \
  --owner padraig \
  --expires-at 2027-01-01T00:00:00Z
```

That writes `governance/waivers.yml` — the file the gate discovers — sorted by comparison id
so two people waiving different comparisons do not produce a reordering diff:

```yaml
waivers:
- comparison_id: compare_8ba8496a_to_dda18a0e_66320e7c
  reason: support-assistant v2 regression, fix tracked in JIRA-123
  owner: padraig
  expires_at: '2027-01-01T00:00:00Z'
```

`--remove` drops one, so the comparison blocks again. `--expires-at` must be in the future:
a waiver that is inactive the moment it lands looks like it worked and changes nothing.
Expired waivers are inactive, and the console shows them as expired rather than hiding them.

`--waivers <path>` overrides the discovery for a one-off run, on `regressions gate` and on
`compare --gate` alike. All three gate surfaces resolve waivers the same way — a waiver the
console honours and CI ignores would be a green screen over a red build, so
`tests/unit/test_gate_surface_parity.py` asks all three the same question and compares their
answers to each other.

Retiring a dataset family (`dataset lifecycle-apply --action retire`) also stops its
comparisons blocking, and surfaces through this same waiver channel with a stated reason
rather than silently un-blocking.

## PR reliability comment

```bash
failure-lab regressions pr-comment --baseline-run <run-id> --candidate-run <run-id>
```

Outputs a concise reliability diff and top signal drivers, suitable for a PR comment.

## What this repo's own CI runs

`.github/workflows/production.yml` — the workflow the README badge points at:

- `ruff check .` and `pytest -q` on Python 3.11 and 3.12
- a consumer-install job: build the wheel and the sdist, assert the wheel ships no legacy
  module and the sdist carries the walkthrough the README points at, install the wheel into a
  clean environment, and run the README quickstart plus `examples/regression_demo/run.sh`
- the composite action, dogfooded against the bundled regression demo — including an
  assertion that the gate actually *fails the job*, not merely that it detects the regression
- the frontend: typecheck, vitest (with the engine installed, so the bridge tests run rather
  than skip), and the production build

`ci.yml` is the legacy/full benchmark suite and is not part of the supported path.
