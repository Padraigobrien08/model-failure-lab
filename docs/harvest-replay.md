# Harvest Replay

Use harvest replay to turn observed regressions into reusable datasets.

## Loop

```bash
failure-lab compare <baseline-run-id> <candidate-run-id>
failure-lab harvest --comparison <comparison-id> --delta regression --out datasets/harvested/regression-pack.json
failure-lab dataset review datasets/harvested/regression-pack.json
failure-lab dataset promote datasets/harvested/regression-pack.json --dataset-id reasoning-regressions-v1
failure-lab run --dataset reasoning-regressions-v1 --model demo
```

## Notes

- Keep harvested packs in source control when they become long-lived regression suites.
- Use `dataset review` before promotion to inspect duplicates and quality.
