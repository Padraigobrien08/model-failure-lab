# Operator Quickstart (5 Minutes)

This is the fastest path from first run to a CI-style gate decision.

## 1) Install and sanity check

```bash
make install
make demo
```

Expected result:

- a demo run is created under `runs/`
- a demo report is created under `reports/`

## 2) Run a baseline and candidate

```bash
failure-lab run --dataset reasoning-failures-v1 --model demo
failure-lab run --dataset reasoning-failures-v1 --model demo
```

Copy both run IDs from command output.

## 3) Compare and inspect signal

```bash
failure-lab compare <baseline-run-id> <candidate-run-id>
failure-lab regressions --direction all --last-n 5
```

Expected result:

- one saved comparison signal
- a verdict (`regression`, `improvement`, `neutral`, or `incompatible`)

## 4) Validate index/contracts

```bash
failure-lab index rebuild
failure-lab index validate
```

Expected result:

- contract validation passes
- required query-index tables exist

## 5) Evaluate governance gate

```bash
failure-lab regressions gate --strict-exit
echo $?
```

Interpretation:

- `0`: gate passes
- `2`: gate blocked by qualifying regression recommendation

## 6) (Optional) Use policy and waiver files

```bash
failure-lab regressions gate --policy-file .failure_lab/policy.yaml --strict-exit
failure-lab regressions gate --policy-file .failure_lab/policy.yaml --waivers .failure_lab/waivers.json --strict-exit
```

Use this when you need deterministic team policy behavior in CI.

## 7) Generate PR-ready reliability comment

```bash
failure-lab regressions pr-comment --baseline-run <baseline-run-id> --candidate-run <candidate-run-id>
```

Paste output into PR discussion/check summary.
