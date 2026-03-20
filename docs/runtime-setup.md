# Runtime Setup Reference

This is the setup companion for `v1.1`.

If you want the full milestone workflow, start with:

- [v1.1 reproducibility walkthrough](v1_1_reproducibility.md)

This reference stays narrower: prerequisites, environment verification, and support-doc routing.

## Prerequisites

- Python 3.11+
- enough disk for CivilComments plus saved artifacts
- network access for the first WILDS download
- network access or a pre-populated local cache for the first `distilbert-base-uncased` run

## Install

```bash
python -m pip install -e .[dev]
```

The editable install is the supported `v1.1` path. Public scripts should run without a manual
`PYTHONPATH=src` export.

## Verify The Environment

```bash
python scripts/check_environment.py
```

Successful output should confirm:

- `matplotlib`, `wilds`, `torch`, and `transformers` are importable
- a writable `MPLCONFIGDIR` is available
- the configured DistilBERT model is `distilbert-base-uncased`
- whether DistilBERT assets are already cached locally or the first run will need network access

If dependencies are missing, use:

```bash
python -m pip install -e .[dev]
```

If the DistilBERT cache is empty, use the prefetch command printed by the checker before the first
transformer run.

## When To Use A Cloud GPU

Use the cloud guide if the local machine cannot sustain the official DistilBERT workflow:

- [Cloud GPU run guide](cloud-gpu-run.md)

For the official `v1.1` evidence path, the DistilBERT baseline was completed with the constrained
tier. The walkthrough explains where that fits in the end-to-end flow.

## Troubleshooting

For environment and download failures, use:

- [Troubleshooting](troubleshooting.md)

## Next Step

Once the environment check is green, continue with:

- [v1.1 reproducibility walkthrough](v1_1_reproducibility.md)
