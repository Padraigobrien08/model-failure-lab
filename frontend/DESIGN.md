# Failure Lab operator console — design rules

These rules bind every screen. They come from the design handoff and are not optional.

## Layout

- Shell: fixed 216px left rail + fluid content column. Min app width 1180px; desktop-first.
- Route anatomy: header (breadcrumb + H1 + right-aligned actions) → optional one-row filter
  bar (`bg-panel`) → content. Never a paragraph of explanation between the H1 and the data.
- A table or the primary artifact is always above the fold.
- Selection panels sit on the right at 280–400px, only when something is selected.
- Sibling spacing via flex/grid + `gap`; no margin-only spacing between siblings.
- Padding: 28px route gutters (`px-7`), 20–22px inside panels, 8–12px inside rows/cells.
- Each route owns its own internal scroll (`flex h-full flex-col overflow-hidden` +
  `flex-1 overflow-auto` on the data region).

## Color — semantics before decoration

All colors are theme tokens (see `src/styles/index.css` and `tailwind.config.ts`):
`ground panel raised ink muted-ink line line-soft accent accent-text accent-wash on-accent
bad bad-bg bad-panel bad-line bad-head bad-chip-bg bad-chip-ink good good-bg warn warn-bg
cand-panel cand-head`.

- Red (`bad`) means regression. Only regression. Never for delete, validation, or emphasis.
- Green (`good`) means improvement only. Amber (`warn`) means partial/degraded run state.
- Accent = selection, focus, links, primary action. It never signals health.
- One background per surface. Elevation is a 1px border; shadows only on overlays.

## Type

- Headings: `font-heading` (Barlow Condensed 600 light / Inter 500 dark — handled by tokens).
- Scale: H1 28px · panel title 20px · section label 9.5–10px uppercase tracking .16–.2em muted
  · body 13.5–14px · table cell 12.5–13.5px · table head 10.5px uppercase .1em · meta
  10.5–11px. Nothing below 10px.
- Monospace (`font-mono`) for everything machine-generated: run ids, report ids, case ids,
  dataset ids, paths, failure types, classifier ids, table percentages, confidences, seeds.
- Sentence case headings. Uppercase only for section labels and status chips.

## Shape

- Radius is the theme token `rounded-tok` (0px light, 8px dark) on every box, input, button,
  chip. Status chips are the one exception — always `rounded-full` in both themes.
- Buttons: `ConsoleButton` primary/secondary only. Inputs: `ConsoleInput`.
- Segmented controls: `SegmentedControl`, always exactly one selected option.

## Data display

- Numeric columns right-aligned; ids/labels left-aligned. Deltas always signed
  (`+12.0 pts`, `−2.0%`, use U+2212 minus) and colored only by direction.
- Percentages: one decimal. Scores: three decimals (`severity 0.360`).
- Whole rows are the click target (`cursor-pointer`, `hover:bg-accent-wash`); a trailing
  `open →` is an affordance, not the only hit area.
- Every table has: a count line ("8 runs · newest first"), an empty state naming the path it
  read plus the CLI command to fix it, and a no-match state naming the filter to clear.
- Group headers inside lists carry the group's semantic tint and a count + share
  (`7 cases · 54%`).

## Vocabulary — never invent

- Failure types verbatim from `schemas/taxonomy.py`, monospace, never prettified:
  `no_failure reasoning instruction_following hallucination retrieval safety format tool_use`.
- Transitions from `reporting/compare.py`: `failure_to_no_failure`, `no_failure_to_failure`,
  `failure_type_swap`, `error_cleared`, `new_error`, `error_stage_changed`. Render with the
  engine's own labels.
- Verdicts: `regression` / `improvement` / `neutral` / `incompatible`. Gate: `PASS` / `FAIL`
  with the policy rule and waiver state always shown next to it.
- Run ids keep their raw form; truncate with a leading ellipsis (`…_candidate_9f2a`) only in
  tight contexts (use `truncateRunId`), never in a primary column.

## Copy

- Terse, CLI-adjacent. Labels are nouns; actions are verbs. No "Let's", no reassurance, no
  explanation of what a screen is for.
- One sentence maximum in any panel. The verdict banner gets one headline sentence stating
  the measured change.
- Always name the artifact: paths, ids, and `writes datasets/<id>.json` receipts are content.
- Errors state what failed and which file, then what to run.

## States & interaction

- Hover: accent wash on rows and nav; neutral tint on secondary buttons.
- Focus: global `:focus-visible` accent outline (already in index.css).
- Loading: keep the shell and header; skeleton only the data region
  (`animate-pulse rounded-tok bg-panel` bars). Never a full-page spinner.
- Dialogs: 760px max, ground background, 1px border, header/body/footer split; the footer's
  left slot carries the write receipt.
- Everything is deterministic and local — no network spinners, no relative times without the
  absolute timestamp.

## Assets

- No images. Icons: Lucide at `strokeWidth={1.5}`, 14–16px, muted ink — arrows, chevrons,
  filter, external-link only. Never an icon where a word is shorter. No emoji.
