# Cloud GPU Run Guide

This guide is the safest way to move the current `v1.1` Phase 12 work to a cloud GPU and complete
the real DistilBERT baseline.

The repo is script-first. You do not need to convert it into a notebook project. On Colab, the
notebook is just a shell for running the existing scripts.

## Recommended Path

Use a GPU VM if you can. It matches the repo's script workflow better and is less fragile for a
long DistilBERT run.

If Colab is the only interface you know, use a blank notebook with a GPU runtime and run the shell
commands from notebook cells. That works too, but the session is more fragile.

## Before You Move Anything

This local repo currently has Phase 12 changes that are not committed yet. The cloud machine needs
those files, not just the last tagged release.

Recommended handoff:

1. create a temporary branch locally
2. commit the current Phase 12 code and config changes
3. push that branch
4. clone that branch on the cloud machine

Do not include large local artifacts unless you actually want to copy them:

- `artifacts/`
- `data/`
- `.planning/`

If you do not want to push a branch yet, the fallback is to zip the repo source and upload it, but
git is the cleaner path.

## Option A: GPU VM

### 1. Clone The Repo

```bash
git clone <your-repo-url>
cd model-failure-lab
git checkout <your-phase-12-branch>
```

### 2. Create The Python Environment

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

### 3. Check The Runtime

```bash
python scripts/check_environment.py
```

You want this to show:

- `wilds: ok`
- `torch: ok`
- `transformers: ok`
- a writable Matplotlib runtime dir

If the DistilBERT cache is empty, run the prefetch command printed by the checker before starting
training.

### 4. Materialize CivilComments

```bash
python scripts/download_data.py
```

If the WILDS download hits SSL issues, use the repo's documented fallback:

```bash
curl -L -k -o data/wilds/civilcomments_v1.0/archive.tar.gz "https://worksheets.codalab.org/rest/bundles/0x8cd3de0634154aeaad2ee6eb96723c6e/contents/blob/"
tar -xzf data/wilds/civilcomments_v1.0/archive.tar.gz -C data/wilds/civilcomments_v1.0
python scripts/download_data.py --skip-download
```

### 5. Run The Official DistilBERT Baseline

For the current `v1.1` milestone, use the constrained tier unless you know the GPU can comfortably
handle the canonical tier.

```bash
python scripts/run_baseline.py --model distilbert --seed 13 --tier constrained --experiment-group baselines_v1_1 --tag v1.1_baseline
```

When it finishes, note the run id under:

```bash
artifacts/baselines/distilbert/<run_id>/
```

### 6. Evaluate The Saved Run

```bash
python scripts/run_shift_eval.py --run-id <distilbert_run_id>
```

### 7. Build The Shared Baseline Report

This assumes the logistic baseline and its evaluation bundle already exist in the same artifact
cohort, or you have copied those artifacts over as well.

```bash
python scripts/build_report.py --experiment-group baselines_v1_1
```

### 8. Copy The Results Back

At minimum, copy these paths back to your local machine:

- `artifacts/baselines/distilbert/<run_id>/`
- `artifacts/baselines/distilbert/<run_id>/evaluations/<eval_id>/`
- `artifacts/reports/comparisons/baselines_v1_1/`

## Option B: Colab

This is the easiest way to stay in familiar notebook tooling while still using the repo scripts.

### 1. Start A GPU Runtime

In Colab:

1. open a blank notebook
2. switch the runtime to GPU
3. confirm a GPU is visible

First cell:

```python
!nvidia-smi
```

### 2. Get The Repo Into Colab

Preferred:

```bash
!git clone <your-repo-url>
%cd /content/model-failure-lab
!git checkout <your-phase-12-branch>
```

Fallback if you do not want to push a branch:

- zip the repo source locally
- upload it to Colab or Drive
- unzip it under `/content/model-failure-lab`

### 3. Install The Project

```bash
!python -m pip install --upgrade pip
!python -m pip install -e '.[dev]'
```

### 4. Check The Runtime

```bash
!python scripts/check_environment.py
```

### 5. Download The Data

```bash
!python scripts/download_data.py
```

If that fails with SSL issues, use:

```bash
!mkdir -p data/wilds/civilcomments_v1.0
!curl -L -k -o data/wilds/civilcomments_v1.0/archive.tar.gz "https://worksheets.codalab.org/rest/bundles/0x8cd3de0634154aeaad2ee6eb96723c6e/contents/blob/"
!tar -xzf data/wilds/civilcomments_v1.0/archive.tar.gz -C data/wilds/civilcomments_v1.0
!python scripts/download_data.py --skip-download
```

### 6. Run DistilBERT

```bash
!python scripts/run_baseline.py --model distilbert --seed 13 --tier constrained --experiment-group baselines_v1_1 --tag v1.1_baseline
```

### 7. Evaluate It

```bash
!python scripts/run_shift_eval.py --run-id <distilbert_run_id>
```

### 8. Export Results

Zip the resulting artifacts before the Colab session ends:

```bash
!zip -r distilbert_run_bundle.zip artifacts/baselines/distilbert/<run_id>
```

Then download the zip from Colab.

## Colab vs VM

Use a GPU VM when:

- you want the least friction for a long script run
- you want easy file persistence
- you are comfortable with terminal-first workflow

Use Colab when:

- you want the fastest path from notebook experience to a working GPU
- you are okay with notebook session limits
- you remember to download artifacts before the runtime expires

## Minimal Success Path For Phase 12

If you want the shortest route to unblock the milestone:

1. move the current Phase 12 code to a GPU machine
2. run `python scripts/check_environment.py`
3. run `python scripts/download_data.py`
4. run the constrained DistilBERT baseline
5. run `python scripts/run_shift_eval.py --run-id <distilbert_run_id>`
6. copy the DistilBERT run and eval artifacts back locally
7. run `python scripts/build_report.py --experiment-group baselines_v1_1`

## What To Ask For Next

If you want tighter help, the next useful ask is:

- "help me prepare the temporary git branch for the cloud run"
- "give me the exact Colab cells for this repo"
- "give me the exact VM commands assuming Ubuntu"
