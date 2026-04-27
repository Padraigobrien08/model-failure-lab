# Architecture

This document explains how Model Failure Lab works internally at a system level.

## Core Flow

The product loop is:

`run -> report -> compare -> harvest -> promote -> rerun`

At a high level:

1. `failure-lab run` executes a dataset with a model adapter and classifier, then writes run artifacts.
2. `failure-lab report` summarizes one run into report artifacts.
3. `failure-lab compare` computes baseline vs candidate deltas and signal drivers.
4. `failure-lab harvest` selects failure/regression cases into a draft pack.
5. `failure-lab dataset promote` creates an immutable curated dataset version.
6. A rerun against promoted datasets closes the reliability loop.

## Main Components

- `src/model_failure_lab/cli.py`
  - CLI command surface and orchestration.
- `src/model_failure_lab/runner/`
  - Run execution and artifact writing.
- `src/model_failure_lab/reporting/`
  - Run reports, comparison reports, robustness/stability summaries.
- `src/model_failure_lab/index/`
  - Query index build/query/contract validation.
- `src/model_failure_lab/governance/`
  - Policy recommendations, gate decisions, lifecycle actions, portfolio workflows.
- `src/model_failure_lab/harvest/`
  - Regression/failure case harvesting and review/promotion seams.
- `src/model_failure_lab/datasets/`
  - Dataset loading, versioning, evolution, and bundled packs.

## Data and Artifact Model

Primary local artifact directories:

- `datasets/`
- `runs/`
- `reports/`
- `.failure_lab/` (derived query index and related metadata)

See `docs/artifact-model.md` for concrete artifact payload examples.

## Query Index and Analytics

The query index is a derived SQLite projection over local artifacts.

- Build/rebuild: `failure-lab index rebuild`
- Contract validation: `failure-lab index validate`
- Query surfaces consume this index for:
  - case/delta search
  - comparison signal listings
  - recurring cluster summaries
  - governance/policy review

## Governance and Reliability Control

Governance transforms comparison signals into deterministic actions:

- recommendation: `failure-lab regressions recommend`
- review/apply: `failure-lab regressions review|apply`
- gate mode: `failure-lab regressions gate`
- root-cause patterns: `failure-lab regressions patterns`
- baseline registry: `failure-lab baselines list|set`

Policy defaults come from code, and can be overridden through CLI flags or policy files.

## Extension Seams

- model adapters: register custom model invocation backends
- classifiers: register custom failure classifiers
- artifact-root handoff: React debugger consumes the same local workspace via `FAILURE_LAB_ARTIFACT_ROOT`
