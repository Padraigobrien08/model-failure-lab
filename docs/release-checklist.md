# Release Checklist — First Public Release (v0.9.0)

> Concrete, ordered checklist for the first public release. Derived from `docs/release-readiness-v0.9.0.md`
> and `docs/release.md`. Check items off in order. Items marked **(manual)** must be done by a
> maintainer outside this repo (git remote, PyPI, GitHub settings).

## 1. Pre-flight (repo state)
- [ ] All release work merged to `main`; working tree clean. **(manual: git)**
- [ ] Version bumped to `0.9.0` in `pyproject.toml` **and** `src/model_failure_lab/__init__.py`.
- [ ] `CHANGELOG.md` `0.9.0` section finalized (move from *Unreleased* to dated, set the release date).
- [ ] `ruff check .` clean.
- [ ] `pytest -q` green.
- [ ] `python -m build` succeeds; `python -m twine check dist/*` passes.

## 2. Maintainer contact replacement
- [ ] Replace `security@example.com` in `SECURITY.md` with a real, monitored address (or enable GitHub Security Advisories and reference it). **(manual)**
- [ ] Replace `conduct@example.com` in `CODE_OF_CONDUCT.md`. **(manual)**
- [ ] Replace `maintainer@example.com` in `pyproject.toml` `[project.maintainers]`. **(manual)**
- [ ] `grep -rn "@example.com" .` returns nothing outside this checklist.

## 3. Tag cleanup
- [ ] Review existing tags: `git tag -l` (currently `v1.0`–`v5.3`, internal milestones). **(manual)**
- [ ] Namespace or remove the internal tags per `docs/release.md` so they don't outrank the release. **Do not delete tags without confirming no external clones/forks/CI depend on them.** **(manual)**
- [ ] Confirm GitHub "latest release" will resolve to `v0.9.0`.

## 4. PyPI / TestPyPI validation
- [ ] Check name availability/ownership: `curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/project/model-failure-lab/`. **(manual)**
- [ ] `python -m build` then upload to **TestPyPI**: `python -m twine upload --repository testpypi dist/*`. **(manual)**
- [ ] Verify install from TestPyPI in a clean venv (see step 5). **(manual)**
- [ ] Only after the above: publish to PyPI (prefer Trusted Publishing/OIDC; never commit tokens). **(manual)**

## 5. Clean install test (fresh virtualenv)
- [ ] `python3 -m venv /tmp/mfl && . /tmp/mfl/bin/activate`
- [ ] `pip install model-failure-lab==0.9.0` (or the TestPyPI index URL) succeeds.
- [ ] `python -c "import model_failure_lab; print(model_failure_lab.__version__)"` prints `0.9.0`.
- [ ] `failure-lab --help` works; (`failure-lab --version` once that flag exists).
- [ ] `deactivate`

## 6. README demo validation
- [ ] From a fresh clone: `bash examples/regression_demo/run.sh` runs end-to-end offline.
- [ ] `failure-lab compare examples/regression_demo/runs/baseline examples/regression_demo/runs/candidate` prints `Status: regressed`.
- [ ] Every command in the README executes as written (no Ollama/keys needed for the demo path).
- [ ] Confirm the demo is reachable for `pip` users **or** the README scopes it to clones.

## 7. Screenshot / GIF creation
- [ ] Record a ~15s terminal GIF (e.g. `vhs`/`asciinema`) of run → compare(regression) → harvest. **(manual)**
- [ ] Place under `docs/screens/` and embed at the top of the README. **(manual)**
- [ ] Remove/replace any remaining placeholder image references (`docs/product-screens.md`).

## 8. GitHub repo settings **(manual, external)**
- [ ] Set repo description and topics (`llm`, `rag`, `evaluation`, `llm-testing`, `regression-testing`, `cli`).
- [ ] Add a social-preview image.
- [ ] Enable branch protection on `main`; require the `production` CI check.
- [ ] Enable GitHub Security Advisories; enable Dependabot.
- [ ] Confirm issue/PR templates render (`.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`).

## 9. Release notes
- [ ] Tag `v0.9.0` from the release commit. **(manual)**
- [ ] Create the GitHub Release; paste the `0.9.0` CHANGELOG section; link the README demo. **(manual)**
- [ ] Mark as a pre-release if you want beta framing.

## 10. Post-release monitoring
- [ ] Verify `pip install model-failure-lab` (no version) resolves to `0.9.0`.
- [ ] Watch the issue tracker for the first 72h; triage install/onboarding reports fast.
- [ ] Confirm CI is green on `main` post-merge.
- [ ] Note follow-ups (e.g. `--version`, exit-code) for v1.0 in `docs/roadmap.md`.
- [ ] Run `pip-audit` / review Dependabot alerts on the published dependency set. **(manual)**
