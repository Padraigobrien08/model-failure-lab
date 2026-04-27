# Artifact Model

Model Failure Lab is built around local filesystem artifacts as a first-class contract.

## Layout

```text
datasets/
runs/<run-id>/
reports/<report-id>/
comparisons/
```

## Datasets

`datasets/` stores canonical and promoted dataset JSON files.

Example:

```json
{
  "dataset_id": "reasoning-failures-v1",
  "cases": [
    {
      "id": "reasoning-001",
      "prompt": "Explain why this argument is invalid."
    }
  ]
}
```

## Runs

Each run writes a deterministic directory in `runs/<run-id>/` with `run.json` and `results.json`.

Example `run.json`:

```json
{
  "run_id": "run-20260427-191200-abc123",
  "dataset_id": "reasoning-failures-v1",
  "model": "demo",
  "metadata": {
    "adapter_id": "demo",
    "status": "completed"
  }
}
```

## Reports

Each report writes under `reports/<report-id>/` with `report.json` and `report_details.json`.

Example `report.json`:

```json
{
  "report_id": "report-20260427-191230-def456",
  "metadata": {
    "report_kind": "run_summary",
    "source_run_id": "run-20260427-191200-abc123"
  },
  "summary": {
    "total_cases": 24,
    "failure_count": 9
  }
}
```

## Comparisons

Comparisons are represented as report artifacts with `report_kind: comparison`.

Example comparison status in `report.json`:

```json
{
  "metadata": {
    "report_kind": "comparison"
  },
  "comparison": {
    "baseline_run_id": "run-a",
    "candidate_run_id": "run-b",
    "compatible": true
  },
  "status": {
    "overall": "improved"
  }
}
```
