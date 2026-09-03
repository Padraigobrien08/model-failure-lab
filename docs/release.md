# Release Runbook

This is the runbook for cutting a public OSS release. It covers versioning/tag strategy and a
**TestPyPI dry run** before any real publish. Production publish mechanics (token handling) are the
`make publish` target, documented inline below.

> **No upload is performed by following the "build/check" steps here.** Only the explicit
> `twine upload` / `make publish` commands publish anything, and they require credentials you supply
> yourself. Do not upload to real PyPI until the TestPyPI dry run passes and a maintainer has
> confirmed it is safe.

## Current release state: nothing since `0.1.0` is published

**PyPI holds exactly one release of `model-failure-lab`: `0.1.0`, uploaded 2026-04-27.** Neither
`0.9.0` through `0.15.0` was ever published — verify with
`curl -s https://pypi.org/pypi/model-failure-lab/json | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)['releases']))"`.

Consequences, which the README and `action.yml` are written around until this changes:

- `pip install model-failure-lab` gets `0.1.0`, which predates `init`, `compare --gate`,
  `--html` export and the `openai-compat` adapter. The README therefore leads with the clone
  install and says so; `tests/unit/test_documented_output_is_real.py` asserts it keeps saying so.
- The composite action defaults to installing from **its own checkout**, not from PyPI, so
  `uses: Padraigobrien08/model-failure-lab@main` works with no release. Its earlier default of
  `model-failure-lab>=0.10.1` could not resolve at all.

### Publishing the current tree

`0.16.0` is the current tree: everything through `0.15.0`, plus the fifth audit pass. `0.15.0`
stopped a candidate hiding a regression by deleting the cases it broke; the audit found the
same trick works by deleting them from the *baseline* instead, because the rule had been
written for one of the comparison's two runs. Both directions are covered now, and the attack
suite that missed it is a `RUNS × EDITS` product rather than a hand-written list
(`tests/unit/test_gate_resists_a_motivated_operator.py`). See the CHANGELOG.

**Before writing the notes, run `make release-facts`** and paste the numbers. Every release
from `0.11.0` to `0.15.0` carried at least one figure that was typed from memory and wrong;
the citation rule added in `0.14.0` checks that a bullet names a test, not that its arithmetic
holds. `0.15.0`'s miscount is recorded under Errata in the CHANGELOG rather than edited away.

Publishing this release is what ships the gate fix to anyone not cloning.

Before tagging: bump the version in `pyproject.toml` and `src/model_failure_lab/__init__.py`, add the
matching `CHANGELOG.md` entry with its numbers taken from `make release-facts`, and confirm
`make check` and the frontend build are green.

**After the release lands, in the same follow-up commit:** restore the PyPI-first install block in the
README, drop the "Install from source for now" note, and delete
`test_documented_output_is_real.py::test_readme_does_not_promise_a_pypi_install_that_predates_the_docs`.
That test exists to keep the README honest while the gap is open, not forever.

## Public versioning policy

**Public OSS releases start at `v0.9.0`.** The package version in `pyproject.toml` is `0.16.0`.

Pre-1.0 semantics (also in the README): patch = fixes/docs, minor = CLI-compatible additions,
breaking = CLI or artifact-schema changes. The first stable line is `1.0.0`.

### ⚠️ Existing tags conflict with the public version

The repository currently carries **25 internal milestone tags**, `v1.0` → `v5.3` (created
2026-03-20 → 2026-04-06). These are internal development phase markers, **not** public releases.

The original worry here — that GitHub would show `v5.3` as the "latest release" — is no longer
true, and was worth checking rather than repeating: real GitHub Releases exist for `v0.9.0` and
`v0.10.0`, and GitHub marks the newest *Release*, not the highest tag. Verify before acting:

```bash
gh release list
git tag -l
```

What remains is the real problem: **a new visitor cannot tell which of the 25 tags are releases**,
and the tags outnumber the releases 12 to 1.

### Recommended tag cleanup strategy

> ⚠️ Destructive and history-affecting. **A human maintainer must run these** after confirming no
> external clone/fork/CI depends on the `v1.x`–`v5.x` tags. They are **not** executed by this audit.

**Option A — Re-namespace internal tags (preferred; preserves history).** Move each `vX.Y` milestone
tag under an `internal/` prefix so it stops competing with public releases, then create the real
release tag:

```bash
# For each internal tag (review the list first: `git tag -l`):
git tag internal/v5.3 v5.3      # create namespaced copy
git tag -d v5.3                 # delete the bare semver tag locally
git push origin internal/v5.3   # push the namespaced tag
git push origin :refs/tags/v5.3 # delete the bare tag on the remote
```

GitHub does not surface `internal/*` tags as releases, so `v0.9.0` becomes the only release.

**Option B — Delete the internal tags outright** (simplest; loses the milestone markers):

```bash
git tag -d v1.0 v1.1 ... v5.3
git push origin --delete v1.0 v1.1 ... v5.3
```

**Then, in either case, cut the public release** (substitute the version being released):

```bash
git tag -a v0.16.0 -m "Both ends of the comparison, and numbers with a command behind them"
git push origin v0.16.0
```

> Until a maintainer performs the cleanup, **do not** create a GitHub Release from any `vX.Y` tag.

### The published `v0.10.0` notes contain claims the tree has since disproved

`v0.10.0` is still the newest GitHub Release, and its notes assert three things that were not true
at that tag: that red means regression on every screen (four screens broke it — `3a32c92`), that
promoted dataset families are immutable (nothing checked it — `f135d73`), and that "the legacy
manifest stack … [is] deleted" (`scripts/sync_react_ui_manifest.py` survived until `0.12.0`). It
also states a test count two releases stale.

Nothing in the repo pins release-note claims the way `test_documented_output_is_real.py` pins the
README, which is why they drifted unnoticed while the README did not. **When cutting the next
release, add a one-line errata to `v0.10.0` pointing at the release that fixed each claim** —
a superseded release page is still the first thing a visitor reads.

## TestPyPI dry run (do this before real PyPI)

### 1. Check name availability

The distribution name is `model-failure-lab` (`pyproject.toml`).

```bash
# Real PyPI — 404 means the name is free; 200 means it is taken.
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/project/model-failure-lab/

# TestPyPI
curl -s -o /dev/null -w "%{http_code}\n" https://test.pypi.org/project/model-failure-lab/
```

If the name is already taken by someone else, choose a new `name` before any upload.

### 2. Build and check

```bash
make build            # or: python3 -m build
python3 -m twine check dist/*
```

Both must pass before uploading anywhere.

### 3. Upload to TestPyPI

Requires a TestPyPI account + API token (https://test.pypi.org/manage/account/token/). **Only run if
your credentials are already configured and you intend to publish to TestPyPI.**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-testpypi-token>
python3 -m twine upload --repository testpypi dist/*
```

### 4. Verify install from TestPyPI

Install in a clean virtualenv. TestPyPI does not mirror real dependencies, so pull deps from real
PyPI via `--extra-index-url`:

```bash
python3 -m venv /tmp/mfl-testpypi && source /tmp/mfl-testpypi/bin/activate
python3 -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  model-failure-lab

# Smoke-test the installed package (note: import name is model_failure_lab):
python3 -c "import model_failure_lab; print('import OK')"
failure-lab demo
deactivate
```

If the smoke test passes, proceed to the real publish — **only after** the tag cleanup above is done
and a maintainer signs off.

## Real PyPI publish

`make publish` runs `verify-dist` (build + `twine check`) and then `twine upload dist/*`. It requires
`TWINE_USERNAME` (`__token__`) and `TWINE_PASSWORD` (a PyPI API token) in the environment; the token
is never persisted. Publish only after the tag is pushed and the TestPyPI dry run passed.

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-pypi-token>
make publish
```

## Pre-release checklist

- `make check` and `npm --prefix frontend run build` are green.
- Version bumped in `pyproject.toml` + `src/model_failure_lab/__init__.py`, with a matching
  `CHANGELOG.md` entry.
- Community-health files (`SECURITY.md`, `CODE_OF_CONDUCT.md`) point at real, monitored contacts —
  no `*@example.com` placeholders.
