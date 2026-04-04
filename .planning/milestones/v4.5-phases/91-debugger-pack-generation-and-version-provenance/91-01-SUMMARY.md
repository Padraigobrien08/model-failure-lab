# 91-01 Summary

- Extended [`query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py),
  [`vite.config.ts`](/Users/padraigobrien/model-failure-lab/frontend/vite.config.ts), and
  [`load.ts`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts) with
  regression-pack, dataset-evolve, and dataset-versions endpoints.
- Added strongly typed loader contracts in
  [`types.ts`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/types.ts) for the
  new automation payloads.
- Kept the existing artifact-root bridge contract intact while expanding the dataset-automation
  surface.
