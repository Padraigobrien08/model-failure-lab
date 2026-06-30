# Adoption & GitHub-Stars Strategy (HN First-Impression Audit)

> ↩ Part of the release planning set. See [`docs/roadmap.md`](roadmap.md) for how these findings feed the prioritized roadmap.

> Audience: a first-time OSS user landing from Hacker News who has ~10 seconds to decide whether to
> keep reading, ~2 minutes to decide whether to `pip install`, and a few hours of goodwill to decide
> whether to star and recommend. This audit ignores internal engineering quality and grades **first
> impressions and adoption mechanics only.** Recommendations are concrete; nothing here is
> implemented.

## TL;DR

The README is clean and honest, the install is lean, and the offline `demo` works — that already puts
it ahead of many launches. But three things will cap stars hard:

1. **No visual.** There is no GIF/screenshot/asciinema. On HN, a terminal GIF in the first screenful
   is the single biggest determinant of "star vs. close tab." (Today `docs/product-screens.md` is
   text placeholders; the README has no image at all.)
2. **The hero example demonstrates nothing.** The README's flagship `compare` output literally reads
   `Status: unchanged` / `Signal verdict: neutral`. The entire pitch is "find what got worse," and
   the showcased example shows nothing got worse. Worse, **you cannot reproduce a regression offline**
   — two `demo` runs are deterministic and identical, so the killer feature requires Ollama or an API
   key on the very first try.
3. **Undifferentiated positioning.** "Local-first evaluation and failure analysis for LLM and RAG
   systems" does not tell a promptfoo/DeepEval user why to switch. The genuinely novel idea —
   *git-native, deterministic regression history you can turn into permanent test datasets* — is
   buried in prose.

Fix those three and the rest is polish. Detail and a concrete plan below.

---

## The 10-second / 2-minute / 1-hour journey

| Moment | What they see today | Verdict |
|---|---|---|
| **First screenful** | Title, two *static* badges, a solid one-liner, the `run → report → compare → harvest → promote` loop, "No server, no account, no cloud." | OK but **no image**; "failure analysis" reads generic. They may bounce. |
| **Skim to decide install** | Clean install block; quickstart; but step 3 needs Ollama, and the example `compare` shows "unchanged." | The payoff isn't visible. Curiosity, not conviction. |
| **Try it** | `pip install` (not on PyPI yet) → `failure-lab demo` works offline → `compare` of two demo runs = identical = "unchanged." | Works, but the *aha* (a caught regression) never happens out of the box. |
| **Decide to star/recommend** | No comparison to tools they know, no community signal, jargon-heavy advanced surface. | Stars only the already-convinced. |

---

## Critique by dimension

| Dimension | Grade | What's wrong (evidence) | Highest-leverage fix |
|---|---|---|---|
| **README hero** | C+ | Static shields only; no demo media; value buried below an abstract one-liner. | Add a 10–15s terminal GIF + a sharper one-liner (below). |
| **Positioning** | C | Generic "evaluation and failure analysis" overlaps promptfoo/DeepEval/Ragas without a wedge. | Lead with the unique claim: *"Git-native LLM regression testing — catch what got worse and turn it into a permanent test, all local."* |
| **Examples** | D+ | Headline `compare` shows `unchanged`/`neutral`; can't show a regression offline; no `examples/` dir; quickstart step 3 needs Ollama. | Ship a deterministic "regressed" demo (e.g. a second demo model or pre-baked run pair) so the **offline** quickstart shows a real delta. |
| **Discoverability** | C | Name is generic and collides conceptually with many tools; PyPI not published; GitHub topics/description likely unset; import name `model_failure_lab` ≠ CLI `failure-lab` ≠ dist `model-failure-lab`. | Publish to PyPI, set topics, add a one-line `pip install` that actually resolves, document/alias the name triple. |
| **Branding** | C− | No logo/wordmark, no color, no social-preview card; "Model Failure Lab" is descriptive but forgettable. | Minimal wordmark + social preview image; consider a punchier tagline/handle (e.g. "FailureLab"). |
| **Competitive framing** | F (absent) | No mention of how it relates to the tools every reader already knows. | Add a comparison table + an explicit "when to use this vs promptfoo/DeepEval/Ragas/LangSmith." |
| **Onboarding** | B− | `pip install` + offline `demo` is genuinely good; fast time-to-first-output. | Make first output a *regression*, not just a run; add a single copy-paste block that does the whole loop. |
| **Screenshots / media** | F | None exist; placeholders only. | At minimum one GIF; ideally GIF + one annotated screenshot of a comparison. |
| **Terminology** | C | Jargon: "harvest," "promote," "regression pack," "signal verdict," "governance," "portfolio," "planning units." Newcomers won't map these to value. | Define the 3 core verbs in one line each up top; relabel advanced/governance surface as "advanced." |
| **Developer experience** | B− | Triple invocation (`failure-lab`/`model-failure-lab`/`python -m`); 13 top-level commands + ~21 `dataset` subcommands overwhelm; no hosted playground. | Pick one canonical command; present **core 4** (`run`/`report`/`compare`/`harvest`) and hide the rest under "advanced." |

---

## Competitive positioning

> Accurate as of the audit; verify current details before publishing any comparison.

| Tool | Shape | License | Strength | Where it leaves a gap MFL can own |
|---|---|---|---|---|
| **promptfoo** | Node CLI + web view, config-driven evals & red-teaming | OSS (MIT) | Best-in-class DX, `npx` start, huge mindshare | Not git-native artifact history; Node, not Python-native |
| **DeepEval** | Python, "Pytest for LLMs," metric library | OSS | Pytest integration, many model-graded metrics | Metric/assertion focus, not a *regression→dataset* loop; nudges toward its paid cloud |
| **Ragas** | Python metrics library (RAG) | OSS | Research-backed RAG metrics | A library, not a workflow/CLI; no run history/compare |
| **LangSmith** | Hosted platform (observability + evals) | Proprietary | Polished UI, datasets, tracing | Requires account + cloud; not local/OSS; vendor lock-in |

**The wedge (say this explicitly):** *Local-first, git-native LLM regression testing.* MFL's
defensible story is the combination promptfoo/DeepEval don't center on:

- **No account, no cloud** — runs on your laptop / in CI; artifacts are plain JSON you commit & diff.
- **Regression → durable test** — a comparison that got worse is `harvest`ed and `promote`d into a
  permanent dataset version. This "turn the bug into a test" loop is the memorable idea.
- **Deterministic, reproducible artifacts** — the same inputs produce byte-identical outputs.

Honest weaknesses to acknowledge (and not hide): smaller metric library than DeepEval, no shipped web
UI (the React debugger isn't packaged), no community/social proof yet, Python-only, pre-1.0.

---

## Concrete plan to maximize stars

> Ordered by impact-per-effort. Items marked **[blocker]** should be done before any HN post.

### A. Before you post (the make-or-break set)
1. **[blocker] Record a 10–15s terminal GIF of the core loop** (use `vhs` or `asciinema` + `agg`):
   run → a failing case → `compare` showing a **real regression** → `harvest`/`promote` turning it
   into a test. Put it directly under the title. This is the highest-leverage single change.
2. **[blocker] Make the offline quickstart show a regression.** Provide a deterministic "regressed"
   path with zero external deps — e.g. a second bundled demo model, or a pre-baked pair of runs the
   quickstart compares — so the first `compare` a user runs prints a non-trivial delta. Replace the
   "unchanged/neutral" example output with that real delta.
3. **[blocker] Rewrite the one-liner** to the wedge. Candidate:
   > **Model Failure Lab — git-native LLM & RAG regression testing. Catch what got worse between two
   > model versions and turn it into a permanent test. 100% local, no account.**
4. **[blocker] Add a comparison table** (above) so readers anchor it against tools they know.
5. **[blocker] Publish to PyPI** so `pip install model-failure-lab` actually works when HN tries it.
   (And finish the P0 items in `docs/oss-readiness.md` — placeholder contacts, tag cleanup. Shipping
   with `security@example.com` and a "v5.3 latest release" tag visibly undercuts trust.)
6. **One copy-paste block** that does the whole loop offline in <30s, before the per-command breakdown.

### B. Strong supporting moves
7. **Define the 3 core verbs** (`run`, `compare`, `harvest`) in one line each at the top; move
   governance/portfolio/`dataset` subcommands under an "Advanced" heading or a separate doc.
8. **GitHub repo metadata:** description + topics (`llm`, `rag`, `evaluation`, `llm-testing`,
   `regression-testing`, `prompt-engineering`, `cli`), and a **social-preview image** so shared links
   render a card.
9. **Live CI/PyPI badges** (replace static shields) — green CI + a version badge signal "alive."
10. **One annotated screenshot** of a comparison report alongside the GIF.
11. **A 60-second "Why" section** that names the pain ("you changed a prompt and silently broke 8% of
    cases") before the mechanics.
12. **A minimal logo/wordmark** and a consistent accent color in the GIF/screenshots.

### C. HN launch craft
- **Title:** `Show HN: Model Failure Lab – git-native, local LLM regression testing` (lead with the
  wedge, not the name). "Show HN" + a clear, non-hype noun phrase.
- **First comment from the author:** the origin story (the specific regression that motivated it),
  what it deliberately does *not* do, and an explicit, gracious comparison to promptfoo/DeepEval/
  Ragas/LangSmith. HN rewards humility and specificity.
- **Timing:** post ~08:00–10:00 ET on a weekday; be present to answer comments for the first 2–3
  hours (response latency strongly affects ranking and conversion).
- **Have the repo ready for the spike:** working `pip install`, the GIF, a runnable offline demo, an
  issue template, and a CONTRIBUTING that doesn't contradict the workflow.
- **Don't** ask for stars, don't use vote rings — HN penalizes both; let the artifact do the work.

### D. After launch (retain the spike)
- A `CHANGELOG.md` and a real GitHub Release for `v0.1.0` so the spike sees momentum.
- Label 3–5 **good first issues** to convert visitors into contributors.
- A short blog post / `examples/` walkthrough you can link in replies.
- Engage every substantive comment and issue within 24h during launch week.

---

## Suggested README hero (drop-in shape)

```
# Model Failure Lab

<10-15s terminal GIF: run → caught regression → harvested into a test>

Git-native LLM & RAG regression testing. Catch what got worse between two model
versions and turn it into a permanent test. 100% local — no account, no cloud.

[CI badge] [PyPI badge] [License badge]

pip install model-failure-lab
failure-lab demo        # see a real failure + regression in ~10s, fully offline
```

Then: the one copy-paste loop → the comparison table → the 3 core verbs → "Advanced" → docs.

## Reality check

The biggest adoption risk is not the README wording — it's that **the headline capability isn't
demonstrable out of the box** and **there's no visual proof it works.** Those two ('A1' and 'A2'
above) are worth more than every other item combined. Also: do not launch with the P0 blockers
(`docs/oss-readiness.md`) still open — a "v5.3" latest release and `@example.com` security contact are
exactly the details an HN audience notices and comments on.
