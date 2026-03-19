"""Deterministic synthetic text perturbation generators."""

from __future__ import annotations

import hashlib
import random
import re
from typing import Any, Callable

from .schema import PerturbationSuite, PerturbedSample, build_perturbed_sample_id

DEFAULT_SLANG_MAPPING = {
    "are": "r",
    "before": "b4",
    "because": "cuz",
    "great": "gr8",
    "message": "msg",
    "people": "ppl",
    "please": "plz",
    "really": "rlly",
    "thanks": "thx",
    "you": "u",
    "your": "ur",
}
_SEVERITY_RATIOS = {"low": 0.03, "medium": 0.06, "high": 0.1}
_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def _seed_for_sample(base_seed: int, *parts: str) -> int:
    digest = hashlib.sha256("|".join([str(base_seed), *parts]).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _replacement_character(character: str) -> str:
    if not character.isalpha():
        return "x"
    index = _ALPHABET.index(character.lower()) if character.lower() in _ALPHABET else 0
    replacement = _ALPHABET[(index + 1) % len(_ALPHABET)]
    return replacement.upper() if character.isupper() else replacement


def apply_typo_noise(text: str, *, severity: str, seed: int) -> tuple[str, list[dict[str, Any]]]:
    """Apply seeded character-level typo noise."""
    if not text:
        return text, []

    rng = random.Random(seed)
    chars = list(text)
    eligible_count = max(sum(1 for char in chars if char.isalpha()), 1)
    op_count = max(1, int(round(eligible_count * _SEVERITY_RATIOS[severity])))
    operations: list[dict[str, Any]] = []

    for _ in range(op_count):
        eligible_positions = [index for index, char in enumerate(chars) if char.isalpha()]
        if not eligible_positions:
            break

        operation_type = rng.choice(["insert", "delete", "substitute"])
        position = rng.choice(eligible_positions)
        original = chars[position]
        replacement = _replacement_character(original)

        if operation_type == "insert":
            chars.insert(position, replacement)
            operations.append(
                {
                    "type": "insert",
                    "position": position,
                    "value": replacement,
                }
            )
            continue

        if operation_type == "delete" and len(eligible_positions) > 1:
            removed = chars.pop(position)
            operations.append(
                {
                    "type": "delete",
                    "position": position,
                    "value": removed,
                }
            )
            continue

        chars[position] = replacement
        operations.append(
            {
                "type": "substitute",
                "position": position,
                "from": original,
                "to": replacement,
            }
        )

    return "".join(chars), operations


def apply_format_degradation(
    text: str,
    *,
    severity: str,
    seed: int,
) -> tuple[str, list[dict[str, Any]]]:
    """Apply deterministic punctuation, casing, and whitespace degradation."""
    del seed
    updated = text
    operations: list[dict[str, Any]] = []

    normalized_whitespace = " ".join(updated.split())
    if normalized_whitespace != updated:
        operations.append({"type": "whitespace_collapse"})
        updated = normalized_whitespace

    lowered = updated.lower()
    if lowered != updated:
        operations.append({"type": "lowercase"})
        updated = lowered

    if severity in {"medium", "high"}:
        no_punctuation = re.sub(r"[^\w\s]", "", updated)
        if no_punctuation != updated:
            operations.append({"type": "strip_punctuation"})
            updated = no_punctuation

    if severity == "high":
        boundaries = [match.start() for match in re.finditer(r"\s+", updated)]
        if boundaries:
            merged = "".join(
                character
                for index, character in enumerate(updated)
                if index not in boundaries[::2]
            )
            if merged != updated:
                operations.append({"type": "merge_token_boundaries"})
                updated = merged

    return updated, operations


def apply_slang_rewrite(
    text: str,
    *,
    severity: str,
    seed: int,
    slang_mapping: dict[str, str] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Apply fixed rule-based slang replacements."""
    mapping = slang_mapping or DEFAULT_SLANG_MAPPING
    tokens = re.findall(r"\w+|\W+", text)
    candidate_positions = [
        index
        for index, token in enumerate(tokens)
        if token.isalnum() and token.lower() in mapping
    ]
    if not candidate_positions:
        return text, []

    if severity == "low":
        limit = 1
    elif severity == "medium":
        limit = min(2, len(candidate_positions))
    else:
        limit = len(candidate_positions)

    rng = random.Random(seed)
    shuffled_positions = list(candidate_positions)
    rng.shuffle(shuffled_positions)
    selected_positions = sorted(shuffled_positions[:limit])

    operations: list[dict[str, Any]] = []
    for position in selected_positions:
        original = tokens[position]
        replacement = mapping[original.lower()]
        tokens[position] = replacement
        operations.append(
            {
                "type": "slang_rewrite",
                "token_index": position,
                "from": original,
                "to": replacement,
            }
        )
    return "".join(tokens), operations


def _require_source_field(sample: dict[str, Any], field_name: str) -> Any:
    if field_name not in sample:
        raise ValueError(f"Source sample is missing required field: {field_name}")
    return sample[field_name]


def generate_perturbation_suite(
    source_samples: list[dict[str, Any]],
    *,
    source_run_id: str,
    model_name: str,
    families: list[str],
    severities: list[str],
    selection_seed: int,
    perturbation_seed: int,
    slang_mapping: dict[str, str] | None = None,
) -> PerturbationSuite:
    """Expand selected source samples into one variant per family and severity."""
    generators: dict[str, Callable[..., tuple[str, list[dict[str, Any]]]]] = {
        "typo_noise": apply_typo_noise,
        "format_degradation": apply_format_degradation,
        "slang_rewrite": lambda text, *, severity, seed: apply_slang_rewrite(
            text,
            severity=severity,
            seed=seed,
            slang_mapping=slang_mapping,
        ),
    }
    if not source_samples:
        raise ValueError("At least one source sample is required to build a perturbation suite")

    suite_samples: list[PerturbedSample] = []
    for sample in source_samples:
        source_sample_id = str(_require_source_field(sample, "sample_id"))
        source_text = str(_require_source_field(sample, "text"))
        source_split = str(_require_source_field(sample, "split"))
        source_group_id = str(_require_source_field(sample, "group_id"))
        dataset_name = str(_require_source_field(sample, "dataset_name"))
        true_label = int(_require_source_field(sample, "label"))
        source_is_id = bool(_require_source_field(sample, "is_id"))
        source_is_ood = bool(_require_source_field(sample, "is_ood"))

        for family in families:
            generator = generators[family]
            for severity in severities:
                seeded_value = _seed_for_sample(
                    perturbation_seed,
                    source_sample_id,
                    family,
                    severity,
                )
                perturbed_text, operations = generator(
                    source_text,
                    severity=severity,
                    seed=seeded_value,
                )
                suite_samples.append(
                    PerturbedSample(
                        perturbed_sample_id=build_perturbed_sample_id(
                            source_sample_id,
                            family,
                            severity,
                            perturbation_seed,
                            perturbed_text,
                        ),
                        source_sample_id=source_sample_id,
                        perturbation_family=family,
                        severity=severity,
                        perturbation_seed=seeded_value,
                        text=perturbed_text,
                        true_label=true_label,
                        source_split=source_split,
                        source_group_id=source_group_id,
                        source_is_id=source_is_id,
                        source_is_ood=source_is_ood,
                        dataset_name=dataset_name,
                        applied_operations=operations,
                        source_metadata={
                            "raw_split": sample.get("raw_split"),
                            "raw_index": sample.get("raw_index"),
                            "group_attributes": sample.get("group_attributes", {}),
                            "source_text": source_text,
                        },
                    )
                )

    return PerturbationSuite(
        source_run_id=source_run_id,
        model_name=model_name,
        dataset_name=str(source_samples[0]["dataset_name"]),
        source_split=str(source_samples[0]["split"]),
        selection_seed=int(selection_seed),
        perturbation_seed=int(perturbation_seed),
        families=[str(item) for item in families],
        severities=[str(item) for item in severities],
        source_sample_count=len(source_samples),
        samples=suite_samples,
    )

