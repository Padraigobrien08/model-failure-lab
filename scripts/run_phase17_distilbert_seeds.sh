#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
MPL_DIR="${MPLCONFIGDIR:-/tmp/model_failure_lab_mpl}"
LOG_DIR="${LOG_DIR:-logs/phase17_distilbert}"
RUN_INDEX_PATH="${RUN_INDEX_PATH:-$LOG_DIR/run_ids.txt}"
EXPERIMENT_GROUP="${EXPERIMENT_GROUP:-baselines_v1_2_distilbert}"
TIER="${TIER:-constrained}"

mkdir -p "$MPL_DIR" "$LOG_DIR"

SEEDS=(13 42 87)

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

latest_run_dir() {
  ls -td artifacts/baselines/distilbert/* 2>/dev/null | head -1 || true
}

echo "# Phase 17 DistilBERT seeded baseline runner" | tee "$RUN_INDEX_PATH"
echo "# started $(timestamp_utc)" | tee -a "$RUN_INDEX_PATH"
echo "# experiment_group=$EXPERIMENT_GROUP tier=$TIER" | tee -a "$RUN_INDEX_PATH"
echo | tee -a "$RUN_INDEX_PATH"

for seed in "${SEEDS[@]}"; do
  run_log="$LOG_DIR/seed_${seed}.log"
  before_latest="$(latest_run_dir)"

  {
    echo "[$(timestamp_utc)] starting seed $seed"
    echo "[$(timestamp_utc)] before_latest=${before_latest:-<none>}"
  } | tee "$run_log"

  MPLCONFIGDIR="$MPL_DIR" "$PYTHON_BIN" scripts/run_baseline.py \
    --model distilbert \
    --tier "$TIER" \
    --seed "$seed" \
    --experiment-group "$EXPERIMENT_GROUP" \
    --tag official \
    --tag v1.2_baseline \
    --tag distilbert \
    --tag "seed_${seed}" \
    2>&1 | tee -a "$run_log"

  after_latest="$(latest_run_dir)"
  if [[ -z "$after_latest" ]]; then
    echo "No DistilBERT run directory found after seed $seed completed." | tee -a "$run_log"
    exit 1
  fi

  run_id="$(basename "$after_latest")"
  metadata_path="$after_latest/metadata.json"
  if [[ ! -f "$metadata_path" ]]; then
    echo "Missing metadata for seed $seed at $metadata_path" | tee -a "$run_log"
    exit 1
  fi

  if ! grep -q '"status": "completed"' "$metadata_path"; then
    echo "Seed $seed did not finish with status completed: $metadata_path" | tee -a "$run_log"
    exit 1
  fi

  {
    echo "[$(timestamp_utc)] completed seed $seed"
    echo "[$(timestamp_utc)] run_id=$run_id"
    echo "[$(timestamp_utc)] metadata=$metadata_path"
  } | tee -a "$run_log"

  printf 'seed=%s run_id=%s metadata=%s\n' "$seed" "$run_id" "$metadata_path" | tee -a "$RUN_INDEX_PATH"
done

echo | tee -a "$RUN_INDEX_PATH"
echo "# finished $(timestamp_utc)" | tee -a "$RUN_INDEX_PATH"
echo "All Phase 17 DistilBERT seeds completed." | tee -a "$RUN_INDEX_PATH"
