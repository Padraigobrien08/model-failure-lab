# Security Audit — `model-failure-lab`

> ↩ Part of the release planning set. See [`docs/roadmap.md`](roadmap.md) for how these findings feed the prioritized roadmap.

> Audit date 2026-06-30. Interface/implementation reviewed against a hostile-input threat model.
> Findings cite `file:line`. This is an audit only — no code was changed. Severity reflects impact ×
> reachability in the supported (production) path.

**Threat model:** a local, offline CLI with **no network server / no inbound surface**. "Hostile user
input" therefore means: malicious **dataset / artifact / manifest JSON** opened from elsewhere,
malicious **IDs / run-config / model options**, malicious **model checkpoints** (legacy), and
**untrusted dependencies**.

## Strong existing controls (verified — keep these)
- **No `shell=True`, no `os.system`, no `eval`/`exec`.** All subprocess calls are list-form with
  fixed binaries: `["git","rev-parse","HEAD"]` (`tracking/manifest.py:69`), `["npm","run","dev",…]`
  (`scripts/run_react_ui.py:35`). → **No command injection.**
- **YAML uses `safe_load`** everywhere (`config/loader.py:45`, `governance/gates.py:88`). → No YAML
  object deserialization.
- **No `pickle`/`marshal` in the production path; no archive extraction** (`tarfile`/`zipfile`/
  `extractall` absent). → No zip-slip.
- **Path-segment sanitization blocks traversal:** `_normalize_segment` collapses everything outside
  `[A-Za-z0-9._-]`/`[a-z0-9_]` to `_` and strips leading/trailing `._-` (`storage/layout.py:24`,
  `utils/paths.py:27`), so IDs from artifact files (`run_id`, `dataset_id`, `report_id`, …) can't
  produce `../` or absolute paths.
- **API keys come only from env** (`ANTHROPIC_API_KEY`, `anthropic_adapter.py:66`); not hardcoded,
  not logged, not echoed in errors; the OpenAI key is read by the SDK, not our code.

---

## CRITICAL
**None confirmed in the supported (production) path.** The absence of a network listener,
`shell=True`, production `pickle`, and the working ID sanitizer keeps the reachable critical surface
empty. (The most severe technical issue, pickle-based RCE, is gated behind the optional legacy stack —
rated High below.)

---

## HIGH

### H1 — `torch.load()` without `weights_only=True` → pickle RCE on a hostile checkpoint
**Evidence:** `mitigations/temperature_scaling.py:166` and `perturbations/scoring.py:215`:
`model.load_state_dict(torch.load(checkpoint_path, map_location=device))`.
`torch.load` deserializes via **pickle**; a crafted checkpoint executes arbitrary code on load.
`checkpoint_path` is supplied by config/artifacts, so a user who runs the legacy pipeline against an
attacker-provided checkpoint gets RCE.
**Reachability:** legacy `[legacy]` extra only, not the production CLI — hence High, not Critical.
**Remediation:** pass `weights_only=True` (PyTorch ≥2.6 default, but make it explicit); validate/
checksum checkpoints before loading; document that checkpoints must come from trusted sources.
Long-term, prefer `safetensors` for weights.

### H2 — Unpinned dependencies, no lockfile/hashes (supply-chain)
**Evidence:** `pyproject.toml` declares `PyYAML`, `anthropic`, `torch`, `transformers`, `wilds`,
`streamlit`, `matplotlib`, `pandas`, … with **no version bounds** (only `openai>=1.0.0` has a floor);
there is **no Python lockfile or hash pinning** (`requirements*.txt`/`uv.lock`/`poetry.lock` absent).
`[legacy]` pulls a very large transitive tree (torch/transformers/wilds).
**Impact:** `pip install` silently resolves the *latest* of each — a compromised or breaking upstream
release runs at install/runtime with no review gate. (The numpy 2.x / pandas ABI break seen during
earlier work is a benign symptom of exactly this.)
**Remediation:** add upper bounds / compatible-release pins for runtime deps; ship a lockfile
(`uv.lock`/`pip-tools`) for CI and contributors; enable `--require-hashes` in CI installs; turn on
Dependabot + `pip-audit`/CodeQL. Split the heavy `[legacy]` tree out so the default install surface
stays tiny.

---

## MEDIUM

### M1 — SSRF / prompt exfiltration via unvalidated `base_url`
**Evidence:** `adapters/ollama_adapter.py:82` `_base_url_from_options` accepts **any string** as
`base_url` (no scheme/host allow-list, no block of internal IPs or `file://`/`gopher://`), then POSTs
the prompt to `{base_url}/api/generate` (`:111`). The value flows from `run_config["model_options"]`
(`runner/execute.py:196`). `--anthropic-base-url` similarly redirects the Anthropic client
(`anthropic_adapter.py`).
**Impact:** if model options ever come from an untrusted source (a shared run-config, a future
"options in dataset" feature), an attacker redirects requests — containing your prompts and, for
Anthropic, your API key — to an arbitrary or internal endpoint. Today it's reachable only via the
user's own CLI, which limits it to Medium.
**Remediation:** validate `base_url` (require `http(s)://`, reject non-loopback/private ranges unless
explicitly opted in); never source endpoint URLs from untrusted files; warn when a non-default
endpoint is used with a real API key.

### M2 — Trusting filesystem paths embedded in manifest/metadata JSON
**Evidence:** `reporting/discovery.py` reads `metadata_path` values and artifact paths out of metadata
JSON and opens them (`_read_json(metadata_path)`, `:120/130`); relocation uses
`metadata_path.parent / path.name` (`:58`). The artifact-index manifest similarly drives the React/
results UI over a user-chosen `FAILURE_LAB_ARTIFACT_ROOT` workspace.
**Impact:** opening an **untrusted artifact workspace** lets the manifest steer which files are read.
Basename-only relocation mitigates classic `../` traversal, but the tool still reads paths it was told
to by data it may not control (information disclosure / confused-deputy).
**Remediation:** resolve every manifest-referenced path and assert it stays within the artifact root
(`Path.resolve()` + `is_relative_to(root)`); reject absolute paths and symlinks that escape the root;
treat opening a foreign workspace as a trust decision and document it.

### M3 — Published package without provenance
**Evidence:** `model-failure-lab` resolves on PyPI, but the README provides **no PyPI link,
signature, or attestation**, and there's no build provenance.
**Impact:** installers can't verify they're getting the real project (name-confusion / typosquat
risk), and there's no tamper-evidence on releases.
**Remediation:** publish via Trusted Publishing (OIDC) with PEP 740 attestations; add a verified PyPI
badge/link; document the canonical install string.

---

## LOW

| # | Finding | Evidence | Remediation |
|---|---|---|---|
| L1 | **Plaintext data at rest** — prompts and model outputs are written to `runs/`/`reports/` JSON; if a prompt contains a secret it lands on disk (umask-dependent perms). API keys themselves are **not** persisted. | artifact model (`runner/artifacts.py`, `results.json`) | Note in docs that artifacts may contain sensitive content; consider restrictive file modes; never put secrets in prompts. |
| L2 | **Endpoint override can redirect key + prompts** if a user is socially-engineered into `--anthropic-base-url`/custom `base_url`. | `anthropic_adapter.py:55+`, `ollama_adapter.py:82` | Warn when a real key is sent to a non-official base URL. |
| L3 | **`--out`/`--root` write to arbitrary user-chosen paths** (by design); artifact IDs are sanitized so embedded IDs can't traverse, but `--out` is a raw path. | `cli.py` harvest `--out` | Acceptable; optionally confirm/abort on overwrite outside the workspace. |
| L4 | **PATH-relative binaries** — `git`/`npm`/`python` invoked by name; a hostile `PATH` could shadow them. | `tracking/manifest.py:69`, `scripts/run_react_ui.py` | Low for a local dev tool; document the assumption. |
| L5 | **Reliability/DoS via unpinned ABI** (numpy/pandas mismatch) | observed during earlier work | Subsumed by H2 pinning. |

---

## Summary

| Severity | Count | Headline |
|---|---|---|
| Critical | 0 | No reachable RCE/injection in the supported path |
| High | 2 | Legacy `torch.load` pickle RCE; unpinned/un-hashed dependency supply chain |
| Medium | 3 | `base_url` SSRF/exfil; manifest-driven path reads; no release provenance |
| Low | 5 | Plaintext artifacts, endpoint redirects, raw `--out`, PATH binaries, ABI DoS |

The production CLI has a **deliberately small, defensible attack surface** (offline, no `shell=True`,
`safe_load`, sanitized IDs, env-only secrets). The real exposure concentrates in the **optional/legacy
stack** (`torch.load` RCE, heavy unpinned deps) and in **trusting data from untrusted workspaces**
(`base_url`, manifest paths). Prioritize: pin/lock + `weights_only=True` (H1/H2), then `base_url`
validation and root-confinement of manifest paths (M1/M2).
