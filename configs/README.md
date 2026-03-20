# Configuration Layout

Phase 1 keeps configuration local, versioned, and explicit. The canonical structure is:

```text
configs/
  data/
  model/
  train/
  eval/
  experiments/
```

- `configs/data/` holds dataset-level definitions such as dataset name and split mapping.
- `configs/model/` holds model-specific defaults such as `logistic_tfidf` or `distilbert`.
- `configs/train/` holds training defaults like seeds and output behavior.
- `configs/eval/` holds evaluation defaults such as metric selections.
- `configs/experiments/` holds runnable presets that compose the component configs above.

Experiment presets should stay config-first. CLI flags may override a small set of iterative fields, but
the resolved run snapshot must still be written to disk before execution work begins.

Phase 11 pairs this config layout with the script-first runtime workflow:

- `python scripts/check_environment.py`
- `python scripts/download_data.py`
- `python scripts/run_baseline.py --model logistic_tfidf`
- `python scripts/run_baseline.py --model distilbert`
