# Scalability Review — `model-failure-lab`

> ↩ Part of the release planning set. See [`docs/roadmap.md`](roadmap.md) for how these findings feed the prioritized roadmap.

> Reviewed 2026-06-30 against the implementation. Estimates are order-of-magnitude reasoning from the
> code paths (not benchmarks) and are labelled as estimates. Guidance follows "avoid premature
> optimization": nothing below is needed at small scale, and each recommendation is tagged with the
> scale at which it becomes justified.

## TL;DR

The **core loop scales fine**: `run`, `report`, and `compare` touch only the one or two runs
involved, so their cost is independent of how many runs exist. The **cross-run analytics (the SQLite
query index) do not scale**, because of *how the index is built and refreshed*, not because of SQLite:

1. **`rebuild_query_index` is a full re-scan + re-parse of every artifact, accumulated in memory**
   (`index/builder.py:66`). O(total runs + cases) time and memory, every rebuild.
2. **`ensure_query_index` checks freshness with an `rglob` over every file under `runs/` and
   `reports/`** on *every* index-backed command (`index/builder.py:454`), even when nothing changed.
3. **Storage is a single flat `runs/<id>/` directory** (`storage/layout.py`), so the directory
   becomes the bottleneck long before SQLite does.

SQLite itself, with the existing indexes, is the *right* tool and is not the problem.

## What the code actually does (evidence)

| Operation | Cost vs. total run count `N` | Evidence |
|---|---|---|
| `run` | O(cases in this run) — **independent of N** | `runner/execute.py` |
| `report` | loads 1 run — **independent of N** | `cli._handle_report` → `load_saved_run_artifacts` |
| `compare` | loads 2 runs — **independent of N** | `cli._load_saved_run_reference` ×2 |
| `query` / `clusters` / `regressions` | indexed SQL, mostly `LIMIT`-bounded | `index/query.py` (`ORDER BY … LIMIT ?`) |
| `index rebuild` | **O(N runs + total cases)** time **and memory**; reads every JSON, builds Python row lists, then `executemany` | `index/builder.py:66–135, 293–379` |
| `ensure_query_index` (freshness) | **O(total files)** `rglob`+`stat` on **every** index-backed call | `index/builder.py:418`, `_latest_artifact_mtime:454` |
| run/comparison inventory listing | some queries have **no `LIMIT`** → O(N) rows into memory | `index/query.py:list_run_inventory` |
| artifact storage | 1 dir + 2 files per run in a **flat** `runs/` | `storage/layout.py:run_directory/run_file/results_file` |

Indexes present (good): `cases(failure_type)`, `cases(created_at)`, `cases(model,dataset)`,
`comparisons(created_at/severity/verdict)`, `case_deltas(...)`, `cluster_occurrences(...)`,
`dataset_versions(family_id)` (`index/builder.py:622+`). `runs.run_id` is the PRIMARY KEY; **no index
on `runs.created_at`**, so run-inventory sorting does a full table sort. No `PRAGMA`/WAL tuning.

## Behavior estimates

Assuming ~2 files and ~8 cases per run.

| Dimension | **100 runs** (~200 files, ~800 cases) | **10,000 runs** (~20k files, ~80k cases) | **1,000,000 runs** (~2M files, ~8M cases) |
|---|---|---|---|
| **`index rebuild`** | <1 s | ~10–60 s (reads 20k JSON, single-threaded) | **minutes–tens of minutes**; reparses 2M files |
| **Rebuild peak memory** | trivial (<50 MB) | hundreds of MB (80k case dicts in lists) | **multiple GB → OOM/swap risk** (8M+ dicts held before insert) |
| **`ensure` freshness check (per command)** | <10 ms | ~0.2–2 s (`stat` 20k files) | **minutes** (`stat` ~2M files) on *every* query |
| **SQLite file size** | <1 MB | ~10–50 MB | ~1–10 GB |
| **Indexed query latency** | <1 ms | <10 ms | ~10–100 ms — **still fine** |
| **Unbounded inventory listing** | trivial | a few MB | loads **all** runs into memory — large |
| **`compare` / `report`** | instant | instant | **instant** (scale-free) |
| **Flat `runs/` directory** | fine | borderline (10k subdirs; `git status`, tab-complete slow) | **degrades/breaks** (1M subdirs; `iterdir`, backup, VCS crawl) |
| **JSON loading** | n/a | fine per-file; the cost is rebuild reading *all* of them | same, dominant during rebuild |

### Narrative
- **100 runs:** everything is instant. No action needed — optimizing here would be premature.
- **10,000 runs:** the read/compare path is still instant, but **rebuild takes tens of seconds and the
  per-command `rglob` freshness check adds visible lag to every `query`/`clusters` call**. Annoying,
  not broken.
- **1,000,000 runs:** the **single-run paths still work**, but **rebuild risks OOM and takes many
  minutes**, the **freshness `rglob` makes every analytics command take minutes**, and the **flat
  `runs/` directory degrades filesystem/VCS/backup operations**. The analytics + storage model
  effectively collapses; SQLite query latency is *not* the cause.

## Justified improvements (and the scale that justifies them)

> Ordered by impact. Each is a fix to the discovery/refresh/storage model, not a database swap.

1. **Incremental indexing — justified at ≥ ~10k.** Don't rebuild the whole index on every change.
   Track which run/report dirs are already ingested (by name + mtime, or write index rows when an
   artifact is written) and ingest only new/changed ones. Turns rebuild from O(N) into O(Δ).
   *Biggest single win; removes the rebuild bottleneck and most of the memory pressure.*
2. **O(1) freshness check — justified at ≥ ~10k.** Replace `_latest_artifact_mtime`'s `rglob` with a
   cheap signal: a monotonically increasing counter / a small manifest updated on each write, or skip
   the check entirely once indexing is incremental. *This is the most insidious cost because it hits
   read-only commands.*
3. **Streaming/batched ingest — justified at ≥ ~100k.** Insert rows in batches inside a single
   transaction instead of building full Python lists (`run_rows`, `case_rows`, …) first. Bounds peak
   memory and avoids OOM at 1M. Pair with `PRAGMA journal_mode=WAL` + `synchronous=NORMAL` for rebuild
   throughput.
4. **Bound the inventory queries — justified at ≥ ~10k.** Add `LIMIT`/pagination to
   `list_run_inventory` (and add an index on `runs(created_at)`), so listing doesn't pull all rows.
5. **Shard the artifact directory — justified only at ≥ ~100k.** Store runs under
   `runs/<prefix>/<id>/` (e.g. first chars of the id, or `runs/<yyyy-mm>/`) to keep any one directory
   small. This changes the on-disk contract, so do it only if that scale is a real target.

## Do **not** do prematurely
- **Don't replace SQLite** with Postgres/DuckDB/Parquet/a server. With its indexes, SQLite serves
  millions of indexed rows with low-ms latency; the bottleneck is the rebuild/discovery model, not the
  store. A swap would add operational weight without addressing the actual cost.
- **Don't shard directories or add caching at small scale** — pure overhead below ~100k runs.
- **Don't parallelize/optimize `compare`/`report`** — they're already O(1) in `N`.

## Bottom line
The single-run workflow (`run → report → compare`) is architecturally scale-free and needs nothing.
The investment, *if and when* run counts reach 10k+, is **incremental indexing + a cheap freshness
signal** (items 1–2); at 100k+ add **streaming ingest and directory sharding** (items 3, 5). Until
then, the current full-rebuild design is an acceptable, simple choice.
