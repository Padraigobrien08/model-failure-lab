# API Documentation

> The CLI surface table below is pinned to `cli.py` by
> `tests/unit/test_cli_surface_documented.py` — a command added without a row here fails the
> suite. It drifted silently before that test existed: `init` and `baselines` shipped
> undocumented.

## Service boundaries

**There is no network/HTTP API and no running service.** Model Failure Lab is a local CLI plus a
static-artifact React UI. "APIs" here means: (1) the **CLI command surface**, (2) **internal Python
interfaces** (adapter/classifier protocols, registries), and (3) the **filesystem artifact contract**
that is the integration boundary between commands and between the CLI and the React UI.

## 1. CLI surface

Entry points (all equivalent): `failure-lab`, `model-failure-lab`, `python3 -m model_failure_lab`
(`pyproject.toml [project.scripts]`, `__main__.py`). Implemented in `src/model_failure_lab/cli.py`
(15 top-level commands, 45 `_handle_*` handlers).

| Top-level command | Subcommands | Purpose |
|---|---|---|
| `run` | — | Execute one dataset through the failure-analysis engine |
| `report` | — | Build a compact report from one saved run |
| `compare` | — | Compare two saved runs (baseline → candidate) |
| `demo` | — | Deterministic demo flow emitting normal artifacts |
| `init` | — | Scaffold a starter prompt dataset in the active workspace |
| `datasets` | `list` | Inspect bundled datasets |
| `dataset` | `review`, `promote`, `versions`, `families`, `lifecycle-review`, `lifecycle-apply`, `portfolio`, `planning-units`, `plan-create`, `plans`, `plan-show`, `plan-preflight`, `plan-execute`, `executions`, `execution-show`, `follow-ups`, `follow-up-show`, `follow-up-link`, `follow-up-attest`, `plan-promote`, `evolve` | Curated dataset lifecycle, evolution, portfolio planning/execution |
| `index` | `rebuild`, `validate` | Manage the derived SQLite query index |
| `query` | — | Structured cross-run queries over the index |
| `history` | — | Run / comparison / dataset-family history |
| `clusters` | — | List recurring failure clusters |
| `cluster` | `show`, `history` | Inspect one cluster |
| `regressions` | `generate`, `recommend`, `review`, `apply`, `gate`, `patterns`, `pr-comment` | Governance over comparison signals |
| `baselines` | `list`, `set` | Shared baseline registry entries |
| `harvest` | — | Harvest saved cases into a draft dataset pack |

> Subcommand lists are read from `argparse --help` output and `cli.py`. The `dataset` group is the
> largest surface (governance/portfolio lifecycle).
>
> **Scope note.** The README calls `run` / `compare` / `harvest` / `promote` the whole core loop,
> and that is accurate: `index`/`query`/`clusters`/`history` are the search layer, `regressions`
> and `baselines` are the CI-gate layer, and the `dataset` group's twelve
> `plan-*` / `execution*` / `follow-up-*` subcommands are a portfolio-planning and
> outcome-attestation surface that the supported loop never requires. They are documented here
> because they exist and are reachable, not because a new user needs them.

### Verified example (`demo`)

```
$ python3 -m model_failure_lab demo
Failure Lab Demo
Dataset: demo-failure-cases-v1
Run ID: 20260629_..._demo_...
Status: completed
Cases: attempted=4 classified=4 errors=0
Failure rate: 75.0%
Artifacts: datasets/..., runs/<id>/run.json, runs/<id>/results.json, reports/<id>/report.json, ...
```

## 2. Internal Python interfaces

### Model adapter protocol — `adapters/contracts.py`

```python
@runtime_checkable
class ModelAdapter(Protocol):
    def generate(self, request: ModelRequest) -> ModelResult: ...
```

| Type | Key fields |
|---|---|
| `ModelRequest` | `prompt: str`, `system_prompt: str \| None`, … |
| `ModelResult` | `text: str`, `metadata: ModelMetadata \| None` |
| `ModelMetadata` | `model: str`, `latency_ms: float`, `usage: ModelUsage \| None`, `raw: JsonValue \| None` |
| `ModelUsage` | `prompt_tokens`, `completion_tokens`, `total_tokens` (all `int \| None`) |

All adapter value objects are `@dataclass(slots=True, frozen=True)` with `to_payload()` /
`from_payload()` for deterministic JSON round-tripping.

**Registry** — `adapters/registry.py`:

| Function | Purpose |
|---|---|
| `ensure_builtin_models()` | Register `demo`, `openai`, `anthropic`, `ollama` (optional ones guarded by import availability) |
| `register_model(model_id, factory)` | Register a custom adapter factory (raises if duplicate) |
| `available_models() -> tuple[str, ...]` | Registered IDs, deterministic order |
| `resolve_model(model_id) -> ModelAdapter` | Instantiate by ID; raises `UnknownModelAdapterError` |

Built-in adapters: `DemoAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `OllamaAdapter`. See
`docs/adapter-extension-guide.md`.

### Classifier interface — `classifiers/contracts.py`

```python
Classifier: TypeAlias = Callable[[ClassifierInput], ClassifierResult]
```

| Type | Key fields |
|---|---|
| `ClassifierInput` | output text + `expectations: ClassifierExpectations \| None` |
| `ClassifierExpectations` | expected labels / forbidden / required strings (tuple fields) |
| `ClassifierResult` | failure label + confidence (validated in `__post_init__`) |

**Registry** — `classifiers/registry.py`: `ensure_builtin_classifiers()` registers `heuristic_v1`
(`classifiers/heuristic.py`); `register_classifier`, `available_classifiers`, `resolve_classifier`
mirror the adapter registry. Raises `UnknownClassifierError`.

### Core schema dataclasses — `schemas/contracts.py`

`Run`, `Result`, `Report`, `PromptCase`, `PromptExpectations`, `PromptContextExpectations`, with
`PayloadValidationError` for invalid payloads. Failure taxonomy in `schemas/taxonomy.py`
(`FailureLabel`).

### Query index API — `index/__init__.py`

Lazy-exported functions (read model over SQLite): `ensure_query_index`, `rebuild_query_index`,
`query_index_path`, `aggregate_case_query`, `aggregate_delta_query`, `artifact_overview_summary`,
`count_case_query`, `count_delta_query`, `list_run_inventory`, `list_comparison_inventory`,
`list_query_facets`, `query_cases`, `query_case_deltas`, `query_comparison_signals`,
`list_failure_clusters`, `get_failure_cluster_detail`, `list_clusters_for_comparison`,
`QueryFilters`. Used by the CLI and by `scripts/query_bridge.py`.

## 3. Filesystem artifact contract

Production artifacts (relative to CWD or `--root`):

| Artifact | Path | Schema source |
|---|---|---|
| Dataset | `datasets/<id>.json` | `datasets/contracts.py` (`FailureDataset`) |
| Run | `runs/<run_id>/run.json`, `results.json` | `runner/contracts.py`, `schemas/contracts.py` |
| Report | `reports/<report_id>/report.json`, `report_details.json` | `reporting/core.py` |
| Governance | `governance/**` | `storage/layout.py` + `governance/*` |
| Query index | `.failure_lab/query_index.sqlite3` | `index/builder.py` |

The **React UI** consumes these read-only via `FAILURE_LAB_ARTIFACT_ROOT`. The frontend's own
artifact/manifest types live in `frontend/src/lib/artifacts/` and `frontend/src/lib/manifest/`. See
`docs/artifact-model.md` for payload examples.

> No request/response (HTTP) formats exist. The "request/response" of this system is JSON-on-disk.
