# Future ideas and backlog

Parking lot for directions we might take after the current v1 freeze. Not commitments—just captured intent so nothing obvious gets lost.

## Distribution and release

- Publish `model-failure-lab` to PyPI for real `pip install` (release flow is documented in `docs/release-and-pypi.md`; upload uses a token, never committed).
- Optional GitHub Action: build + upload on tag, using repository secrets for `TWINE_PASSWORD`.
- Optional `make publish-test` (or equivalent) targeting Test PyPI before production PyPI.
- Version bump + changelog discipline when cutting releases.

## Product clarity

- Replace screenshot placeholders under `docs/screens/` with real captures or a short GIF of the React debugger (see `docs/product-screens.md`).
- One short blog or post describing the failure → report → compare → harvest → promote loop for a team audience.

## Data and evaluation

- Additional high-quality bundled packs (domains beyond reasoning / RAG / support-style prompts).
- Optional “real world” dataset import patterns (CSV, JSONL) with docs and one example.

## Operations and observability

- Minimal telemetry or structured logging hooks (local-only or opt-in) for runs, report generation, and compare—without sending data off-machine by default.

## Deeper product (v2+)

- Tighter integration between governance gates, baselines, and CI comments in more host providers.
- UI polish and parity notes where the React debugger and legacy surfaces diverge.

When picking up any of these, prefer small, shippable slices over a big-bang release.
