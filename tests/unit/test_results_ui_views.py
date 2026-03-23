from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from model_failure_lab.results_ui.app import NAVIGATION_VIEWS, render_app


@dataclass
class _Call:
    name: str
    value: Any = None


class _RecorderBase:
    def __init__(self, calls: list[_Call], *, selected_view: str = "Overview") -> None:
        self._calls = calls
        self._selected_view = selected_view

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def _record(self, name: str, value: Any = None) -> None:
        self._calls.append(_Call(name=name, value=value))

    def title(self, value: str) -> None:
        self._record("title", value)

    def subheader(self, value: str) -> None:
        self._record("subheader", value)

    def caption(self, value: str) -> None:
        self._record("caption", value)

    def markdown(self, value: str) -> None:
        self._record("markdown", value)

    def metric(self, label: str, value: str) -> None:
        self._record("metric", (label, value))

    def dataframe(self, value: Any, **_: Any) -> None:
        self._record("dataframe", value)

    def bar_chart(self, value: Any, **_: Any) -> None:
        self._record("bar_chart", value)

    def expander(self, label: str, expanded: bool = False):
        self._record("expander", (label, expanded))
        return _RecorderBase(self._calls, selected_view=self._selected_view)

    def columns(self, count: int):
        self._record("columns", count)
        return [_RecorderBase(self._calls, selected_view=self._selected_view) for _ in range(count)]

    def checkbox(self, label: str, value: bool = False) -> bool:
        self._record("checkbox", (label, value))
        return value

    def radio(self, label: str, options: tuple[str, ...], index: int = 0) -> str:
        self._record("radio", (label, options, index))
        return self._selected_view

    def link_button(self, label: str, uri: str) -> None:
        self._record("link_button", (label, uri))


class _FakeSidebar(_RecorderBase):
    pass


@dataclass
class _FakeStreamlit(_RecorderBase):
    selected_view: str = "Overview"
    calls: list[_Call] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__init__(self.calls, selected_view=self.selected_view)
        self.sidebar = _FakeSidebar(self.calls, selected_view=self.selected_view)

    def set_page_config(self, **kwargs: Any) -> None:
        self._record("set_page_config", kwargs)


@pytest.mark.usefixtures("results_ui_manifest")
def test_results_ui_app_shell_defaults_to_overview(results_ui_manifest: Path):
    fake_st = _FakeStreamlit(selected_view="Overview")

    render_app(index_path=results_ui_manifest, streamlit_module=fake_st)

    radio_calls = [call for call in fake_st.calls if call.name == "radio"]
    title_calls = [call.value for call in fake_st.calls if call.name == "title"]
    markdown_calls = [call.value for call in fake_st.calls if call.name == "markdown"]

    assert radio_calls
    assert NAVIGATION_VIEWS == radio_calls[0].value[1]
    assert "Model Failure Lab" in title_calls
    assert any("temperature scaling" in text.lower() for text in markdown_calls)
    assert any("dataset expansion" in text.lower() for text in markdown_calls)


@pytest.mark.usefixtures("results_ui_manifest")
def test_results_ui_cohort_view_renders_aggregate_first_sections(results_ui_manifest: Path):
    fake_st = _FakeStreamlit(selected_view="Cohort Analysis")

    render_app(index_path=results_ui_manifest, streamlit_module=fake_st)

    subheaders = [call.value for call in fake_st.calls if call.name == "subheader"]
    expanders = [call.value[0] for call in fake_st.calls if call.name == "expander"]

    assert "Logistic TF-IDF Baseline" in subheaders
    assert "DistilBERT Baseline" in subheaders
    assert "Show per-seed breakdown" in expanders


@pytest.mark.usefixtures("results_ui_manifest")
def test_results_ui_mitigation_view_shows_seeded_and_milestone_labels(results_ui_manifest: Path):
    fake_st = _FakeStreamlit(selected_view="Mitigation Comparison")

    render_app(index_path=results_ui_manifest, streamlit_module=fake_st)

    markdown_calls = [call.value for call in fake_st.calls if call.name == "markdown"]
    subheaders = [call.value for call in fake_st.calls if call.name == "subheader"]

    assert any("seeded comparison summary" in text.lower() for text in markdown_calls)
    assert any("phase 20 milestone label" in text.lower() for text in markdown_calls)
    assert "Reweighting" in subheaders


@pytest.mark.usefixtures("results_ui_manifest")
def test_results_ui_stability_view_shows_defer_recommendation(results_ui_manifest: Path):
    fake_st = _FakeStreamlit(selected_view="Stability")

    render_app(index_path=results_ui_manifest, streamlit_module=fake_st)

    markdown_calls = [call.value for call in fake_st.calls if call.name == "markdown"]
    assert any("dataset expansion recommendation" in text.lower() for text in markdown_calls)
    assert any("defer" in text.lower() for text in markdown_calls)


@pytest.mark.usefixtures("results_ui_manifest")
def test_results_ui_artifacts_view_exposes_link_actions(results_ui_manifest: Path):
    fake_st = _FakeStreamlit(selected_view="Artifacts")

    render_app(index_path=results_ui_manifest, streamlit_module=fake_st)

    link_buttons = [call.value for call in fake_st.calls if call.name == "link_button"]
    assert link_buttons
    assert any(
        label in {"View Metadata", "View Report", "Open Report Bundle", "Open Run Bundle"}
        for label, _ in link_buttons
    )
