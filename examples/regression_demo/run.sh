#!/usr/bin/env bash
# Offline, deterministic regression demo. No Ollama / OpenAI / Anthropic / network.
#
#   bash examples/regression_demo/run.sh
#
# Shows the core loop: compare two model versions -> detect a regression ->
# harvest the regressed cases into a reusable dataset.
set -euo pipefail

cd "$(dirname "$0")"

# Use the module form so it works whether or not the console script is on PATH.
FL() { python3 -m model_failure_lab "$@"; }

echo "==> 1/3  compare baseline (v1) vs candidate (v2)"
FL compare runs/baseline runs/candidate

echo
echo "==> 2/3  index the artifacts so the regression can be harvested"
FL index rebuild >/dev/null

echo
echo "==> 3/3  harvest the regressed cases into a reusable dataset"
REPORT_ID="$(FL compare runs/baseline runs/candidate --score \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['report_id'])")"
FL harvest --comparison "$REPORT_ID" --delta regression --out regression-pack.json

echo
echo "Done. The 4 regressed cases were written to:"
echo "  examples/regression_demo/regression-pack.json"
echo "Promote it to a permanent dataset with: failure-lab dataset promote ..."
