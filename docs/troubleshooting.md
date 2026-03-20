# Troubleshooting

## `wilds` Is Missing

Symptom:

- `python scripts/check_environment.py` reports `wilds: missing`
- `python scripts/download_data.py` fails with a message about the `wilds` package

Fix:

```bash
python -m pip install -e .[dev]
python scripts/check_environment.py
```

Do not continue to `download_data.py` until the environment check reports `wilds` as available.

## `MPLCONFIGDIR` Or Matplotlib Cache Errors

Symptom:

- report generation fails while trying to initialize Matplotlib
- the runtime mentions `MPLCONFIGDIR`

What the repo does:

- report commands configure a writable `MPLCONFIGDIR` automatically through the shared runtime helper

What to check:

```bash
python scripts/check_environment.py
```

If the environment is unusual and Matplotlib still cannot write its cache directory, rerun the
environment check and confirm the reported runtime dir is writable on your machine.

## DistilBERT Asset Or Cache Failures

Symptom:

- DistilBERT setup fails while loading `distilbert-base-uncased`
- the error mentions local cache or network access

Why it happens:

- the first DistilBERT run needs either network access or a pre-populated local cache for
  `distilbert-base-uncased`

What to do:

```bash
python scripts/check_environment.py
```

If dependencies are missing, follow the install command printed by the checker:

```bash
python -m pip install -e .[dev]
```

Interpretation:

- if the check reports local cache available, retry the run
- if the check reports no local cache, the first DistilBERT run will require network access or a
  manually prepared local cache

The checker also prints a cache prefetch command. You can run it before the first transformer
baseline to avoid paying the model download cost inside `run_baseline.py`.

## CivilComments Download Hits SSL Verification Errors

Symptom:

- `python scripts/download_data.py` fails while downloading the WILDS CivilComments archive
- the error mentions SSL verification or a missing local issuer certificate

What to do:

```bash
curl -L -k -o data/wilds/civilcomments_v1.0/archive.tar.gz "https://worksheets.codalab.org/rest/bundles/0x8cd3de0634154aeaad2ee6eb96723c6e/contents/blob/"
tar -xzf data/wilds/civilcomments_v1.0/archive.tar.gz -C data/wilds/civilcomments_v1.0
python scripts/download_data.py --skip-download
```

Why this works:

- it fetches the same WILDS archive directly
- it leaves the project-local manifest and validation path to `download_data.py`
- it avoids repeating the SSL verification failure inside the Python downloader

## Script Runs Assume Hidden Path State

Symptom:

- old instructions suggest `PYTHONPATH=src`

Current supported flow:

```bash
python -m pip install -e .[dev]
python scripts/check_environment.py
```

The public scripts now bootstrap repo paths directly, so manual `PYTHONPATH` exports should not be
part of the normal workflow.
