# Artifact Model

Model Failure Lab is built around local filesystem artifacts as a first-class contract. Every
command reads and writes JSON under a single workspace root (the current directory, or `--root`).
The dataclasses in [`schemas/contracts.py`](../src/model_failure_lab/schemas/contracts.py) and
[`runner/contracts.py`](../src/model_failure_lab/runner/contracts.py) are the source of truth for
these shapes; the examples below are captured verbatim from a real `demo` run and kept in sync with
those `to_payload()` methods. All artifacts are written with `sort_keys=True`, so keys appear in the
alphabetical order shown here.

## Layout

```text
datasets/            # canonical + promoted dataset packs, and harvested/ drafts
runs/<run-id>/       # run.json + results.json
reports/<report-id>/ # report.json + report_details.json (single-run AND comparison reports)
governance/          # policy.yml, waivers.yml, baselines.json, promotions.json,
                     #   lifecycle_actions/, portfolio_plans/
.failure_lab/        # derived SQLite index (rebuildable; not a source artifact)
```

Comparisons are **not** a separate directory. A comparison is a report artifact under
`reports/<comparison-id>/` whose `metadata.report_kind == "comparison"`.

## Identifiers

IDs contain no randomness, but run and report IDs are **timestamp-prefixed**, so they are stable
in shape rather than byte-reproducible across two identical runs:

- Run ID: `<YYYYMMDD_HHMMSS_us>_<dataset-slug>_<model>_<classifier>_<model>_seed_<n>_<sha256[:8]>`,
  e.g. `20260824_083526_830993_reasoning_failures_v1_demo_heuristic_v1_demo_seed_13_aac85ca2`. The
  leading timestamp is wall-clock. The trailing digest is **configuration**-derived — it covers
  `dataset_id : adapter_id : classifier_id : model : run_seed : run_config`
  (`runner/identity.py`), and deliberately **not** the dataset's cases. Two runs over materially
  different versions of the same dataset ID therefore share the same digest.
  Dataset *content* provenance is recorded separately, as `metadata.dataset_content_digest` on
  the run. It is **recorded, not enforced** — no command reads it, and nothing about it makes
  two runs comparable or not. What actually refuses an unsound comparison is a per-case
  content fingerprint computed at compare time
  (`reporting/compare.py:_prompt_content_fingerprint`): two runs sharing a case id whose
  prompt, tags or expectations differ are `incompatible_cases`, so a dataset mutated under a
  stable id cannot be silently compared across. That check is finer-grained than the
  run-level digest, which is why the digest stayed a provenance record rather than becoming a
  gate. Separately, a promoted dataset carries its own `metadata.integrity.content_digest`,
  which *is* verified on load, and whose promotion is recorded outside the pack in
  `governance/promotions.json` (see [Datasets](#datasets) below).
- Single-run report ID: `<run-id>_report`.
- Comparison report ID: `compare_<baseline-digest>_to_<candidate-digest>_<pair-digest>` — derived
  purely from the **two run IDs** (`reporting/compare.py:build_comparison_report_id`), not from
  the comparison's content. Re-comparing the same two runs is therefore idempotent, which is the
  useful property; the caveat is that editing a run in place and re-comparing writes to the same
  comparison ID, replacing the previous verdict. Run IDs produced by `failure-lab run` are
  timestamped and effectively unique, so this only bites hand-authored run IDs (as in
  `examples/regression_demo/`).

Artifact **content** (outputs, classifications, metrics, deltas) is deterministic given the fixed
run seed; artifact **identity** and `created_at` are point-in-time. For real (non-`demo`) adapters,
`execution.latency_ms` and any `usage` fields also carry wall-clock measurements — these are the
sanctioned nondeterministic fields. The `demo` adapter pins `latency_ms` to `0.0`.

## Datasets

`datasets/` stores canonical and promoted dataset JSON packs. Harvested drafts awaiting promotion
live under `datasets/harvested/`.

```json
{
  "dataset_id": "reasoning-failures-v1",
  "name": "Reasoning Failures",
  "description": "Bundled reasoning-failure probes ...",
  "version": "1",
  "metadata": { "default_scope": "core", "target_failure_type": "reasoning" },
  "cases": [
    {
      "id": "reasoning-core-001",
      "prompt": "Solve the two-step arithmetic problem: ...",
      "tags": ["core", "multi_step"],
      "expectations": { "expected_failure": "reasoning", "reference_answer": "10" }
    }
  ]
}
```

### Integrity of a promoted version

`dataset promote` and `dataset evolve` stamp a content digest into the pack they write:

```json
"metadata": {
  "integrity": { "algorithm": "sha256", "content_digest": "72ce1d4735123776", "case_count": 4 }
}
```

The digest covers the dataset's `dataset_id`, `version`, and its ordered cases — each case's
`id`, `prompt`, sorted `tags`, and `expectations`. It deliberately **excludes** `created_at`,
`source`, and `metadata`, so re-stamping provenance does not invalidate a pack whose cases are
unchanged.

`load_dataset` verifies the digest, which is what makes "immutable" checkable rather than
decorative:

- editing a promoted pack makes every consumer fail loudly — `failure-lab run` exits 1 and
  `failure-lab index validate` exits 1, naming the file and both digests;
- `dataset promote` **refuses** to write over an existing curated dataset; add the new cases as
  the next version with `dataset evolve`, promote under a different `--dataset-id`, or pass
  `--force` to replace it deliberately;
- packs written before digests existed carry none and load unchanged — only a *mismatch* is an
  error, so upgrading does not invalidate an existing workspace.

Drafts under `datasets/harvested/` are not versioned and carry no digest; they are meant to be
reviewed and promoted.

## Runs

Each run writes `runs/<run-id>/` with `run.json` and `results.json`.

`run.json` (from `Run.to_payload`) — top-level keys: `config`, `created_at`, `dataset`, `metadata`,
`model`, `run_id`. Note the field is `dataset` (the canonical dataset ID), not `dataset_id`; run
`status` lives in `metadata`, and authoritatively in `results.json` (below).

```json
{
  "config": { "dataset_scope": "core", "dataset_source": "bundled" },
  "created_at": "2026-08-24T08:35:26.830993Z",
  "dataset": "reasoning-failures-v1",
  "metadata": {
    "adapter_id": "demo",
    "classifier_id": "heuristic_v1",
    "dataset_content_digest": "9f3dea421e145876",
    "dataset_version": "1",
    "error_count": 0,
    "run_seed": 13,
    "status": "completed",
    "total_cases": 8
  },
  "model": "demo",
  "run_id": "20260824_083526_830993_reasoning_failures_v1_demo_heuristic_v1_demo_seed_13_aac85ca2"
}
```

`results.json` — top-level keys: `adapter_id`, `cases`, `classifier_id`, `dataset_id`,
`error_count`, `run_id`, `status`, `total_cases`. Each entry in `cases` carries `case_id`,
`classification`, `error` (null on success), `execution`, `expectation`, `output`, and the source
`prompt`:

```json
{
  "case_id": "reasoning-core-001",
  "classification": { "confidence": 0.85, "explanation": "...", "failure_type": "reasoning" },
  "error": null,
  "execution": {
    "adapter_id": "demo", "case_seed": 1250314958, "classifier_id": "heuristic_v1",
    "latency_ms": 0.0, "model": "demo", "run_seed": 13
  },
  "expectation": {
    "expectation_verdict": "matched_expected",
    "expected_failure": { "failure_type": "reasoning" },
    "observed_failure": { "failure_type": "reasoning" }
  },
  "output": { "text": "[demo:stable] ... :: 436f8ec0e882" },
  "prompt": { "id": "reasoning-core-001", "prompt": "...", "tags": ["core"], "expectations": {} }
}
```

## Reports (single run)

`reports/<report-id>/` with `report.json` and `report_details.json`.

`report.json` (from `Report.to_payload`) — top-level keys: `created_at`, `failure_counts`,
`failure_rates`, `metadata`, `metrics`, `report_id`, `run_ids`, `status`, `total_cases`. There is
no `summary` object; the aggregate lives in `metrics`, `failure_counts`, and `failure_rates`.

```json
{
  "report_id": "20260824_083526_..._report",
  "run_ids": ["20260824_083526_..."],
  "created_at": "2026-08-24T08:35:26.900000Z",
  "total_cases": 8,
  "failure_counts": { "reasoning": 5 },
  "failure_rates": { "reasoning": 0.625 },
  "metrics": {
    "attempted_case_count": 8, "classification_coverage": 1.0, "classified_case_count": 8,
    "execution_error_count": 0, "execution_success_rate": 1.0, "failure_case_count": 5,
    "failure_rate": 0.625, "successful_model_invocation_count": 8, "unclassified_count": 0
  },
  "metadata": { "report_kind": "single_run", "source_run_id": "...", "run_status": "completed" },
  "status": { "overall": "completed" }
}
```

`report_details.json` (single run) — the payload the operator console depends on. Top-level keys:
`dataset_id`, `execution_errors`, `expectation_mismatches`, `expectation_verdict_breakdown`,
`expectation_verdict_counts`, `failure_type_breakdown`, `metrics`, `notable_cases`, `report_id`,
`report_kind`, `source_run_id`, `tag_breakdown`, `unclassified_cases`.

## Comparisons

A comparison report is written the same way, with `metadata.report_kind == "comparison"`.

`report.json` adds a `comparison` block and a `status.overall` of `improved` / `regressed` /
`unchanged` / `incompatible`:

```json
{
  "comparison": {
    "baseline_run_id": "...", "candidate_run_id": "...", "compatible": true,
    "dataset_id": "reasoning-failures-v1", "shared_case_count": 8,
    "metrics_computed_on": "shared_cases_only",
    "baseline_only_case_count": 0, "candidate_only_case_count": 0,
    "signal": { "verdict": "neutral", "regression_score": 0.0, "improvement_score": 0,
                "net_score": 0.0, "severity": 0.0, "top_drivers": [] }
  },
  "status": { "overall": "unchanged" },
  "metadata": { "report_kind": "comparison", "comparison_mode": "baseline_to_candidate" }
}
```

`report_details.json` (comparison) — top-level keys: `baseline_failure_breakdown`,
`baseline_full_metrics`, `baseline_only_case_ids`, `baseline_shared_metrics`,
`candidate_failure_breakdown`, `candidate_full_metrics`, `candidate_only_case_ids`,
`candidate_shared_metrics`, `case_deltas`, `case_transition_counts`, `case_transition_summary`,
`comparison_mode`, `compatibility`, `dropped_baseline_failure_case_ids`, `failure_count_deltas`,
`failure_rate_deltas`, `report_id`, `report_kind`, `shared_case_ids`, `signal`.

The `signal` block is the governance verdict (see
[`reporting/signals.py`](../src/model_failure_lab/reporting/signals.py)):

```json
{ "verdict": "regression|improvement|neutral|incompatible",
  "regression_score": 0.0, "improvement_score": 0.0, "net_score": 0.0,
  "severity": 0.0, "top_drivers": [] }
```

`compatibility.metrics_computed_on` is `shared_cases_only` — deltas are computed only over cases
present in **both** runs, which is why adding new passing cases cannot mask a regression.
`case_transition_counts` reports `improvements`, `regressions`, `failure_type_swaps`, and
`error_changes` over those shared cases.

## Verifying artifacts

`failure-lab index rebuild` performs strict field-level ingestion validation as it projects
artifacts into the SQLite index; that rebuild is where malformed source artifacts are rejected.
`failure-lab index validate` forces that same strict rebuild against the source artifacts and then
checks the derived index's schema and table set, so a run, report, or comparison artifact that
violates the contract is reported as an error rather than silently passing.
