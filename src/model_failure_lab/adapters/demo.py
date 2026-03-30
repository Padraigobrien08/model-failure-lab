"""Deterministic local adapter used for tests and demo flows."""

from __future__ import annotations

import hashlib

from .contracts import ModelMetadata, ModelRequest, ModelResult

_DEMO_VARIANTS = ("stable", "repeatable", "controlled", "deterministic")


class DemoAdapter:
    """Pure, deterministic adapter with zero external I/O."""

    def generate(self, request: ModelRequest) -> ModelResult:
        digest = self._digest(request)
        variant = _DEMO_VARIANTS[int(digest[0], 16) % len(_DEMO_VARIANTS)]
        prompt_excerpt = " ".join(request.prompt.split())[:72]
        text = f"[demo:{variant}] {prompt_excerpt} :: {digest[:12]}"
        metadata = ModelMetadata(
            model=request.model,
            latency_ms=0.0,
            raw={
                "adapter": "demo",
                "seed": request.seed,
                "digest": digest[:16],
                "options": dict(request.options),
            },
        )
        return ModelResult(text=text, metadata=metadata)

    @staticmethod
    def _digest(request: ModelRequest) -> str:
        payload = "::".join(
            [
                request.model,
                request.prompt,
                request.system_prompt or "",
                str(request.seed),
                repr(sorted(request.options.items())),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
