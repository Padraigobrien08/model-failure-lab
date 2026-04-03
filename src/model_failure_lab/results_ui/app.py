"""Streamlit app shell for the read-only results explorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[3]
    src_root = repo_root / "src"
    for path in (repo_root, src_root):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

from model_failure_lab.results_ui.load import default_results_ui_index_path, load_results_ui_index
from model_failure_lab.results_ui.views import (
    render_artifacts_view,
    render_cohorts_view,
    render_mitigations_view,
    render_overview_view,
    render_stability_view,
)

NAVIGATION_VIEWS = (
    "Overview",
    "Cohort Analysis",
    "Mitigation Comparison",
    "Stability",
    "Artifacts",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the app parser used by `streamlit run ... -- ...`."""
    parser = argparse.ArgumentParser(description="Render the read-only results explorer UI.")
    parser.add_argument(
        "--index",
        type=Path,
        default=default_results_ui_index_path(),
    )
    parser.add_argument("--include-exploratory", action="store_true")
    return parser


def _import_streamlit() -> Any:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via script tests
        raise RuntimeError(
            "streamlit is not installed. Install the optional UI dependency with "
            "`pip install 'model-failure-lab[ui]'` or, from a checkout, "
            "`python -m pip install '.[ui]'`."
        ) from exc
    return st


def render_app(
    *,
    index_path: Path | None = None,
    include_exploratory: bool = False,
    streamlit_module: Any | None = None,
) -> None:
    """Render the full read-only results explorer app."""
    st = streamlit_module or _import_streamlit()
    index = load_results_ui_index(index_path)

    st.set_page_config(
        page_title="Model Failure Lab Results Explorer",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.sidebar.title("Results Explorer")
    st.sidebar.caption("Read-only benchmark evidence viewer")
    show_exploratory = st.sidebar.checkbox(
        "Include exploratory artifacts",
        value=include_exploratory,
    )
    selected_view = st.sidebar.radio("Navigate", NAVIGATION_VIEWS, index=0)

    if selected_view == "Overview":
        render_overview_view(st, index, include_exploratory=show_exploratory)
    elif selected_view == "Cohort Analysis":
        render_cohorts_view(st, index, include_exploratory=show_exploratory)
    elif selected_view == "Mitigation Comparison":
        render_mitigations_view(st, index, include_exploratory=show_exploratory)
    elif selected_view == "Stability":
        render_stability_view(st, index, include_exploratory=show_exploratory)
    else:
        render_artifacts_view(st, index, include_exploratory=show_exploratory)


def main(argv: list[str] | None = None, *, streamlit_module: Any | None = None) -> int:
    args = build_parser().parse_args(argv)
    render_app(
        index_path=args.index,
        include_exploratory=args.include_exploratory,
        streamlit_module=streamlit_module,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
