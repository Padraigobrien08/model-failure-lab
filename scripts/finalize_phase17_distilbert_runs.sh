#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="${LOG_DIR:-logs/phase17_distilbert}"
EVAL_INDEX_PATH="${EVAL_INDEX_PATH:-$LOG_DIR/eval_ids.txt}"
EXPERIMENT_GROUP="${EXPERIMENT_GROUP:-baselines_v1_2_distilbert}"
FORCE_EVAL="${FORCE_EVAL:-0}"

mkdir -p "$LOG_DIR"

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

discover_official_run_ids() {
  "$PYTHON_BIN" - "$EXPERIMENT_GROUP" <<'PY'
import json
import sys
from pathlib import Path

expected_group = sys.argv[1]
required_tags = {"official", "v1.2_baseline", "distilbert"}
rows = []
for metadata_path in Path("artifacts/baselines/distilbert").glob("*/metadata.json"):
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("status") != "completed":
        continue
    if payload.get("experiment_group") != expected_group:
        continue
    tags = set(payload.get("tags") or [])
    if not required_tags.issubset(tags):
        continue
    seed_tag = next((tag for tag in tags if tag.startswith("seed_")), None)
    if seed_tag is None:
        continue
    try:
        seed_value = int(seed_tag.split("_", 1)[1])
    except (IndexError, ValueError):
        seed_value = 10**9
    rows.append((seed_value, str(payload["run_id"])))

for _, run_id in sorted(rows):
    print(run_id)
PY
}

describe_run() {
  local metadata_path="$1"
  "$PYTHON_BIN" - "$metadata_path" "$EXPERIMENT_GROUP" <<'PY'
import json
import sys
from pathlib import Path

metadata_path = Path(sys.argv[1])
expected_group = sys.argv[2]
payload = json.loads(metadata_path.read_text(encoding="utf-8"))
tags = set(payload.get("tags") or [])
required_tags = {"official", "v1.2_baseline", "distilbert"}
seed_tag = next((tag for tag in tags if tag.startswith("seed_")), "")

if payload.get("status") != "completed":
    raise SystemExit(f"Run is not completed: {metadata_path}")
if payload.get("experiment_group") != expected_group:
    raise SystemExit(
        f"Run group mismatch for {metadata_path}: "
        f"{payload.get('experiment_group')} != {expected_group}"
    )
if not required_tags.issubset(tags):
    raise SystemExit(
        f"Run tags missing official v1.2 distilbert markers: {metadata_path}"
    )
if not seed_tag:
    raise SystemExit(f"Run does not expose a seed_<n> tag: {metadata_path}")

print("|".join([str(payload["run_id"]), seed_tag]))
PY
}

latest_completed_eval_id() {
  local run_dir="$1"
  "$PYTHON_BIN" - "$run_dir" <<'PY'
import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
eval_root = run_dir / "evaluations"
rows = []
for metadata_path in eval_root.glob("*/metadata.json"):
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("status") != "completed":
        continue
    rows.append(metadata_path.parent.name)

if rows:
    print(sorted(rows)[-1])
PY
}

if (($# > 0)); then
  RUN_IDS=("$@")
else
  RUN_IDS=()
  while IFS= read -r run_id; do
    [[ -n "$run_id" ]] || continue
    RUN_IDS+=("$run_id")
  done < <(discover_official_run_ids)
fi

if ((${#RUN_IDS[@]} == 0)); then
  echo "No completed official DistilBERT v1.2 runs found under $EXPERIMENT_GROUP." >&2
  echo "Import the run directories first or pass explicit run IDs." >&2
  exit 1
fi

echo "# Phase 17 DistilBERT eval finalizer" | tee "$EVAL_INDEX_PATH"
echo "# started $(timestamp_utc)" | tee -a "$EVAL_INDEX_PATH"
echo "# experiment_group=$EXPERIMENT_GROUP force_eval=$FORCE_EVAL" | tee -a "$EVAL_INDEX_PATH"
echo | tee -a "$EVAL_INDEX_PATH"

PROCESSED_SEEDS=()

for run_id in "${RUN_IDS[@]}"; do
  run_dir="artifacts/baselines/distilbert/$run_id"
  metadata_path="$run_dir/metadata.json"

  if [[ ! -f "$metadata_path" ]]; then
    echo "Missing run metadata: $metadata_path" >&2
    exit 1
  fi

  run_summary="$(describe_run "$metadata_path")"
  IFS='|' read -r normalized_run_id seed_tag <<<"$run_summary"
  if [[ "$normalized_run_id" != "$run_id" ]]; then
    echo "Run ID mismatch for $metadata_path: expected $run_id got $normalized_run_id" >&2
    exit 1
  fi

  existing_eval_id="$(latest_completed_eval_id "$run_dir")"
  if [[ -n "$existing_eval_id" && "$FORCE_EVAL" != "1" ]]; then
    echo "[$(timestamp_utc)] skipping $run_id ($seed_tag); completed eval already exists: $existing_eval_id" | tee -a "$EVAL_INDEX_PATH"
  else
    echo "[$(timestamp_utc)] evaluating $run_id ($seed_tag)" | tee -a "$EVAL_INDEX_PATH"
    "$PYTHON_BIN" scripts/run_shift_eval.py --run-id "$run_id"
    existing_eval_id="$(latest_completed_eval_id "$run_dir")"
  fi

  if [[ -z "$existing_eval_id" ]]; then
    echo "No completed evaluation bundle found for $run_id after finalize step." >&2
    exit 1
  fi

  PROCESSED_SEEDS+=("$seed_tag")
  printf 'seed=%s run_id=%s eval_id=%s metadata=%s\n' \
    "$seed_tag" \
    "$run_id" \
    "$existing_eval_id" \
    "$metadata_path" | tee -a "$EVAL_INDEX_PATH"
done

echo | tee -a "$EVAL_INDEX_PATH"
for expected_seed in seed_13 seed_42 seed_87; do
  if [[ " ${PROCESSED_SEEDS[*]} " != *" $expected_seed "* ]]; then
    echo "# warning missing_from_this_finalize=$expected_seed" | tee -a "$EVAL_INDEX_PATH"
  fi
done

echo "# finished $(timestamp_utc)" | tee -a "$EVAL_INDEX_PATH"
echo "Phase 17 DistilBERT eval finalization complete." | tee -a "$EVAL_INDEX_PATH"
