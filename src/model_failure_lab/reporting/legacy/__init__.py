"""Reporting surfaces for the legacy DistilBERT/CivilComments benchmark stack.

These modules import the optional `[legacy]` extra (pandas / numpy / matplotlib /
scikit-learn) and read the `utils/paths.py` artifact layout, not the production
`storage/layout.py` one. They are kept for reference (`docs/legacy.md`) and are excluded
from the wheel, so `pip install model-failure-lab` ships only the supported
run -> report -> compare -> harvest workflow -- which is what `pyproject.toml` has always
claimed and, until this package existed, was not true: `reporting/` was a single package,
so setuptools could exclude it whole or not at all, and eleven torch/pandas-importing
modules shipped alongside the seven production ones.

The production reporting surface is the parent package: `core`, `compare`, `signals`,
`artifacts`, `load`, `html`, `markdown`.
"""

from __future__ import annotations
