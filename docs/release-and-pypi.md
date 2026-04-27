# Release and PyPI Guide

This guide covers packaging checks and optional publish.

**Do not put your PyPI token in the repository.** Never commit it, add it to `README`, or paste it into issues. Use one of:

- **Your machine:** `export TWINE_PASSWORD=...` in the shell before `make publish`, or a local file named `.env` (ignored by git—see `.gitignore`) that you load yourself; do not check in `.env`.
- **CI (e.g. GitHub Actions):** store the token as an encrypted [repository secret](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) and pass it to the job as `TWINE_PASSWORD`.

## 1) Build artifacts

```bash
make build
```

Expected output:

- `dist/model_failure_lab-<version>.tar.gz`
- `dist/model_failure_lab-<version>-py3-none-any.whl`

## 2) Verify package metadata and files

```bash
make verify-dist
```

This runs `twine check` on all distribution artifacts.

## 3) Test install from wheel (optional)

```bash
python3 -m pip install dist/model_failure_lab-<version>-py3-none-any.whl
python3 -m model_failure_lab demo
```

## 4) Publish to PyPI (optional)

Set token:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<pypi-token>
```

Then publish:

```bash
make publish
```

If credentials are missing, `make publish` fails fast with guidance.

## 5) Post-release checks

- Verify install path from clean environment.
- Confirm `failure-lab demo` succeeds.
- Tag release in Git and publish release notes.
