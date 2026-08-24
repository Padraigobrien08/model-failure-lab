# Release Runbook

This is the runbook for cutting a public OSS release. It covers versioning/tag strategy and a
**TestPyPI dry run** before any real publish. Production publish mechanics (token handling) are the
`make publish` target, documented inline below.

> **No upload is performed by following the "build/check" steps here.** Only the explicit
> `twine upload` / `make publish` commands publish anything, and they require credentials you supply
> yourself. Do not upload to real PyPI until the TestPyPI dry run passes and a maintainer has
> confirmed it is safe.

## Current release: 0.10.1 (security patch)

`0.10.1` is the first release to include the regression-gate and dev-server-bridge hardening (see the
CHANGELOG). The `0.10.0` tag on PyPI predates those fixes, so cutting and publishing `0.10.1` is what
actually ships the hardening to consumers. The composite action (`action.yml`) already floors the
installed package at `>=0.10.1`; that floor only takes effect once `0.10.1` is on PyPI.

Before tagging: bump the version in `pyproject.toml` and `src/model_failure_lab/__init__.py`, add the
matching `CHANGELOG.md` entry, and confirm `make check` and the frontend build are green.

## Public versioning policy

**Public OSS releases start at `v0.9.0`.** The package version in `pyproject.toml` is `0.10.1`.

Pre-1.0 semantics (also in the README): patch = fixes/docs, minor = CLI-compatible additions,
breaking = CLI or artifact-schema changes. The first stable line is `1.0.0`.

### ⚠️ Existing tags conflict with the public version

The repository currently carries **25 internal milestone tags**, `v1.0` → `v5.3` (created
2026-03-20 → 2026-04-06). These are internal development phase markers, **not** public releases. They
conflict with a `v0.9.0` public release in two ways:

1. GitHub shows the highest semver tag (`v5.3`) as the "latest release," which directly contradicts a
   `0.9.0` package on PyPI and a v0.1 announcement.
2. A new visitor cannot tell which tags (if any) are real releases.

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
git tag -a v0.10.1 -m "Gate and dev-server-bridge hardening"
git push origin v0.10.1
```

> Until a maintainer performs the cleanup, **do not** create a GitHub Release from any `vX.Y` tag.

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
