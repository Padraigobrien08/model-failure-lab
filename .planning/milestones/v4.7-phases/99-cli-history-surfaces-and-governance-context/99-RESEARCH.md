# 99 Research

- The cleanest operator surface is a dedicated history command with scoped queries:
  `--dataset`, `--model`, and `--family`.
- Governance already had a deterministic threshold model; adding recurrence window/threshold fields
  was enough to make it time-aware without changing the action space.
- The frontend already consumed governance payloads from the query bridge, so exposing history there
  avoids duplicated client logic.
