# Pre-Mortem — Why This Project Failed (Imagined, 18 Months Post-Release)

> ↩ Part of the release planning set. See [`docs/roadmap.md`](roadmap.md) for how these findings feed the prioritized roadmap.

> A pre-mortem: we assume failure has already happened (repo mostly inactive, stars stalled, issues
> unanswered) and work backwards to the causes. Ten most-likely reasons, ranked by probability, each
> with **why it happened** and **what to do today to prevent it.** Honest, not kind. Several causes
> compound — the root cluster is called out at the end.

---

### 1. Bus factor of one → maintainer burnout (probability: very high)
**Why it happened:** the project shipped as a 140-file package with a 4,000-line `cli.py`, a legacy ML
stack, brittle payload-coupled tests, and **no plugin system** — so every adapter, scorer, and fix had
to go through the single maintainer. Contributors never arrived because the contribution surface was
high-friction; the maintainer absorbed all of it and quit. This is the #1 way OSS projects die.
**Prevent today:** lower the contribution cost *before* growth — decompose `cli.py`, add entry-point
plugins so adapters/scorers live out-of-core, snapshot-test instead of hand-asserting payloads, and
label good-first-issues. Recruit a second maintainer early; a project with bus factor 1 is already
failing.

### 2. Never differentiated enough from promptfoo / DeepEval (probability: very high)
**Why it happened:** the pitch was "also does local eval," and the one real wedge (regression →
permanent dataset) was thin and easy to copy. promptfoo had momentum and a web view; DeepEval had
metrics and pytest. Users nodded and kept their existing tool. "Better at a job you already solve" is
not a reason to switch.
**Prevent today:** pick the *one* job — git-native regression CI — and be unmistakably the best at it
(PR comments, exit codes, durable test datasets). Stop overlapping; lead every surface with the wedge,
not "evaluation toolkit."

### 3. No distribution — nobody heard of it (probability: high)
**Why it happened:** no launch, no GIF, no content, no community presence. A good tool with zero
marketing dies in obscurity; stars require reach, and reach requires deliberate distribution.
**Prevent today:** plan a real launch (Show HN + a 15s demo GIF + an honest comparison), publish a
couple of "regression caught in CI" write-ups, and be present for the spike. Treat distribution as a
first-class workstream, not an afterthought.

### 4. Onboarding leaked the entire top of funnel (probability: high)
**Why it happened:** the flagship demo wasn't in the `pip` wheel, there was no visual, the CLI exposed
13 commands + 21 `dataset` subcommands, and jargon (harvest/promote/governance) greeted newcomers.
People `pip install`ed, hit friction, and left within two minutes.
**Prevent today:** ship the offline demo *in* the package (`failure-lab demo`), add the GIF, hide the
advanced surface behind "advanced," and define the 3 core verbs up front. Make time-to-first-"aha"
under 60 seconds.

### 5. The core workflow was never actually CI-usable (probability: high)
**Why it happened:** the entire promise was "catch regressions before your users do," but `compare`
had no exit code and no GitHub Action / pytest integration, so it couldn't gate CI — the one place the
value lived. It stayed a manual curiosity.
**Prevent today:** ship `compare --exit-code` and a GitHub Action + pytest plugin that comment
regressions on PRs. Until the wedge is automated where engineers work, it isn't real.

### 6. The heuristic classifier capped credibility (probability: medium-high)
**Why it happened:** failure "detection" was authored rules, not model-graded or user-defined scoring.
Serious teams didn't trust it for their app, and there was no way to plug in their own check, so they
used a tool with real metrics.
**Prevent today:** ship a **pluggable scorer interface** (exact/regex/JSON-schema/bring-your-own
judge, plus Ragas/DeepEval interop) — as an extension point, not a metric zoo. Make "what counts as a
failure" the user's decision.

### 7. Built for the wrong audience (probability: medium)
**Why it happened:** the governance/portfolio/lifecycle surface signaled heavyweight enterprise
process, but the people who star and adopt early are individual engineers who wanted something light.
The product courted mature teams and alienated its actual early-adopter base.
**Prevent today:** target the individual LLM engineer first — fast, local, CI-friendly. Keep
governance as an optional advanced layer, not the front door.

### 8. Unnecessary complexity and unfocused scope (probability: medium)
**Why it happened:** at launch it already carried a legacy DistilBERT/WILDS benchmark stack, a
21-command dataset namespace, a governance/portfolio system, and a half-shipped React UI. It looked
unfocused and was expensive to maintain — reinforcing #1 and #4.
**Prevent today:** cut or spin out the legacy stack, consolidate the CLI, and resist adding surface.
Ship a small, sharp tool; scope discipline is survival.

### 9. Trust eroded from release-quality and stability issues (probability: medium)
**Why it happened:** unpinned dependencies (numpy/pandas ABI breakage), version/tag chaos (a `v5.3`
tag outranking the public release), and a published-state mismatch produced flaky installs and "is
this maintained?" impressions. Early bug reports went unfixed (see #1) and people left.
**Prevent today:** pin deps + lockfile, fix the version/tag story, automate releases, and triage the
first wave of issues fast. First impressions of reliability compound.

### 10. Forgettable name and weak identity (probability: medium-low)
**Why it happened:** "Model Failure Lab" was generic and academic, the `model_failure_lab` /
`model-failure-lab` / `failure-lab` triple confused users, and nothing became a verb people could
recommend. Word-of-mouth — the cheapest growth — never caught.
**Prevent today:** pick a short, memorable, brandable name and one canonical command before the
audience forms; renaming after traction is far costlier.

---

## The root cluster

Three causes dominate and reinforce each other:
- **#1 (bus factor / maintenance burden)** — no contributors, one exhausted maintainer.
- **#2 (no differentiation)** + **#5 (not CI-usable)** — the wedge was real but never made undeniable.
- **#3/#4 (no distribution + onboarding leak)** — the few who arrived didn't convert, and few arrived.

A project can survive a weak name (#10) or the wrong initial audience (#7). It does not survive a
single maintainer drowning in a tool nobody can contribute to, that isn't clearly better at one job,
that nobody hears about. 

## The single highest-leverage action today
**Make the project contributable and the wedge automated.** Concretely: a plugin system (adapters +
scorers) so the community shares the load (#1, #6), and a CI integration with an exit code so the
core promise is real where engineers work (#2, #5). Everything else — name, docs, marketing — amplifies
a project that has those two; without them, amplification just attracts people to something that can't
sustain or differentiate itself.
