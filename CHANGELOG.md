# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Public OSS releases start
at `0.9.0` (see `docs/decisions/0003-public-versioning-starts-at-v0.9.0.md`); earlier `v1.0`–`v5.3`
git tags are internal development milestones, not public releases.

## [0.9.0] - Unreleased

First public beta. Establishes the supported `run → report → compare → harvest → promote` workflow as
the product, with the optional research/ML stack quarantined behind extras.

### Added
- `failure-lab --version` prints the installed package version.
- Offline, deterministic regression demo (`examples/regression_demo/`) showing a real regression
  caught and harvested — no Ollama/OpenAI/Anthropic/network required. The demo ships in the source
  tree and sdist; the offline single-run `failure-lab demo` command works from any install.
- Production CI workflow (Python 3.11 and 3.12, dev-only install) separate from the legacy/full suite.
- Regression guard ensuring the production CLI imports none of the legacy ML dependencies.
- Baseline documentation set under `docs/` (overview, architecture, setup, API, dependencies,
  release, security, scalability, roadmap, and release planning artifacts).
- Community health files: issue/PR templates, `.env.example`, and this changelog.

### Changed
- README rebuilt around the workflow ("catch LLM regressions before your users do") with a real
  regression as the flagship example.
- `pyproject.toml` metadata: advertise Python 3.12, add a maintainer field, publish MIT as a PEP 639
  license expression.
- Version set to `0.9.0` (public beta) in `pyproject.toml` and `src/model_failure_lab/__init__.py`.
- The production test suite runs green without the optional `[legacy]` ML stack installed; legacy
  tests auto-skip when their dependencies are unavailable.

### Notes
- Pre-1.0: CLI flags and artifact schemas may still change before `1.0.0`.
- Before tagging this release, complete `docs/release.md` — including replacing the
  placeholder maintainer/security/conduct contacts and reconciling the internal git tags.

[0.9.0]: https://github.com/Padraigobrien08/model-failure-lab/releases/tag/v0.9.0
