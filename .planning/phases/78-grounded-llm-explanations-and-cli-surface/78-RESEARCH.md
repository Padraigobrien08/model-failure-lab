# Phase 78 Research

- The lowest-risk way to add LLM interpretation is to treat heuristic output as the grounding
  scaffold and let the model enrich summaries within that scaffold.
- Reusing the adapter registry avoids creating a second analysis-provider system and inherits the
  same install-hint behavior already proven for Anthropic, OpenAI, and Ollama.
- `compare --explain` should operate on the saved comparison artifact, not a transient in-memory
  structure, so the explanation stays aligned with the persisted report users can inspect later.

