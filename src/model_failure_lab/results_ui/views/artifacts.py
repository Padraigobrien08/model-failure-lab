"""Low-level artifact explorer view."""

from __future__ import annotations

from typing import Any

from model_failure_lab.results_ui.components import render_entity_actions
from model_failure_lab.results_ui.formatters import format_label
from model_failure_lab.results_ui.selectors import get_default_visible_entities


def _render_entity_section(st: Any, *, title: str, entities: list[dict[str, Any]]) -> None:
    st.subheader(title)
    for entity in entities:
        expander = st.expander(
            f"{entity.get('id')} • {format_label(entity.get('experiment_group', ''))}",
            expanded=False,
        )
        expander.markdown(
            f"**Status:** {format_label(entity.get('status'))}  \n"
            f"**Official:** {entity.get('is_official')}  \n"
            f"**Seed:** {entity.get('seed', 'n/a')}"
        )
        render_entity_actions(expander, entity)


def render_artifacts_view(
    st: Any,
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> None:
    """Render the low-level artifact inventory browser."""
    st.title("Artifacts")
    st.caption("Official-first inventory of runs, evaluations, and reports from the manifest.")

    _render_entity_section(
        st,
        title="Runs",
        entities=get_default_visible_entities(
            index,
            "runs",
            include_exploratory=include_exploratory,
        ),
    )
    _render_entity_section(
        st,
        title="Evaluations",
        entities=get_default_visible_entities(
            index,
            "evaluations",
            include_exploratory=include_exploratory,
        ),
    )
    _render_entity_section(
        st,
        title="Reports",
        entities=get_default_visible_entities(
            index,
            "reports",
            include_exploratory=include_exploratory,
        ),
    )
