"""Self-contained deterministic HTML rendering for report and comparison artifacts.

Pure stdlib. Output is fully inline (CSS embedded, no external assets, no JavaScript)
and deterministic: it contains only data already present in the artifacts.
"""

from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence

_STYLE = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial,
       sans-serif; margin: 2rem auto; max-width: 60rem; padding: 0 1rem;
       color: #1f2933; background: #ffffff; line-height: 1.5; }
h1 { font-size: 1.5rem; border-bottom: 2px solid #d9e2ec; padding-bottom: 0.5rem; }
h2 { font-size: 1.15rem; margin-top: 2rem; }
table { border-collapse: collapse; width: 100%; margin: 0.75rem 0; font-size: 0.9rem; }
th, td { border: 1px solid #d9e2ec; padding: 0.4rem 0.6rem; text-align: left;
         vertical-align: top; }
th { background: #f0f4f8; }
code { background: #f0f4f8; padding: 0.1rem 0.3rem; border-radius: 3px;
       font-size: 0.85em; }
.pass { color: #147d3a; font-weight: 600; }
.fail { color: #ba2525; font-weight: 600; }
.neutral { color: #52606d; font-weight: 600; }
dl.meta { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; }
dl.meta dt { font-weight: 600; color: #52606d; }
dl.meta dd { margin: 0; }
""".strip()


def _format_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.1f}%"
    return "n/a"


def _format_signed_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:+.1f}%"
    return "n/a"


def _document(title: str, body_sections: Sequence[str]) -> str:
    body = "\n".join(body_sections)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{escape(title)}</title>\n"
        f"<style>\n{_STYLE}\n</style>\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>\n"
    )


def _meta_list(pairs: Sequence[tuple[str, str]]) -> str:
    rows = "".join(
        f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>" for label, value in pairs
    )
    return f'<dl class="meta">{rows}</dl>'


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        f"<table>\n<thead><tr>{head}</tr></thead>\n"
        f"<tbody>\n{''.join(body_rows)}\n</tbody>\n</table>"
    )


def _verdict_cell(text: str, css_class: str) -> str:
    return f'<span class="{css_class}">{escape(text)}</span>'


def render_run_report_html(
    *,
    report: Any,
    details: Mapping[str, object],
    cases: Sequence[Mapping[str, object]],
) -> str:
    """Render a run report as a self-contained HTML page.

    ``cases`` is a deterministic sequence of mappings with keys ``case_id``,
    ``failure_type``, and ``status`` (one of ``pass``/``fail``/``error``/``unclassified``).
    """
    metrics = report.metrics if isinstance(report.metrics, dict) else {}
    sections = [
        "<h1>Failure Lab Report</h1>",
        _meta_list(
            [
                ("Report ID", str(report.report_id)),
                ("Run ID", str(details.get("source_run_id", "unknown"))),
                ("Dataset", str(details.get("dataset_id", "unknown"))),
                ("Status", str(report.status.get("overall", "unknown"))),
                (
                    "Cases",
                    (
                        f"attempted={metrics.get('attempted_case_count', 0)} "
                        f"classified={metrics.get('classified_case_count', 0)} "
                        f"errors={metrics.get('execution_error_count', 0)}"
                    ),
                ),
                ("Failure rate", _format_rate(metrics.get("failure_rate"))),
                (
                    "Classification coverage",
                    _format_rate(metrics.get("classification_coverage")),
                ),
            ]
        ),
    ]

    failure_counts = report.failure_counts if isinstance(report.failure_counts, dict) else {}
    failure_rates = report.failure_rates if isinstance(report.failure_rates, dict) else {}
    if failure_counts:
        sections.append("<h2>Failure types</h2>")
        sections.append(
            _table(
                ["Failure type", "Count", "Rate"],
                [
                    [
                        escape(failure_type),
                        escape(str(count)),
                        escape(_format_rate(failure_rates.get(failure_type))),
                    ]
                    for failure_type, count in sorted(failure_counts.items())
                ],
            )
        )

    sections.append("<h2>Cases</h2>")
    case_rows = []
    for case in cases:
        status = str(case.get("status", "unclassified"))
        if status == "pass":
            verdict = _verdict_cell("PASS", "pass")
        elif status == "fail":
            verdict = _verdict_cell("FAIL", "fail")
        else:
            verdict = _verdict_cell(status.upper(), "neutral")
        case_rows.append(
            [
                f"<code>{escape(str(case.get('case_id', '')))}</code>",
                escape(str(case.get("failure_type", "n/a"))),
                verdict,
            ]
        )
    sections.append(_table(["Prompt ID", "Failure type", "Result"], case_rows))
    return _document(f"Failure Lab Report {report.report_id}", sections)


def render_comparison_html(*, report: Any, details: Mapping[str, object]) -> str:
    """Render a comparison report as a self-contained HTML page."""
    comparison = report.comparison if isinstance(report.comparison, dict) else {}
    signal = comparison.get("signal")
    if not isinstance(signal, dict):
        maybe_signal = details.get("signal")
        signal = maybe_signal if isinstance(maybe_signal, dict) else {}
    metrics = report.metrics if isinstance(report.metrics, dict) else {}
    delta = metrics.get("delta")
    delta = delta if isinstance(delta, dict) else {}
    verdict = str(signal.get("verdict", "unknown"))
    verdict_class = {"regression": "fail", "improvement": "pass"}.get(verdict, "neutral")

    sections = [
        "<h1>Failure Lab Compare</h1>",
        _meta_list(
            [
                ("Report ID", str(report.report_id)),
                ("Baseline", str(comparison.get("baseline_run_id", "unknown"))),
                ("Candidate", str(comparison.get("candidate_run_id", "unknown"))),
                ("Status", str(report.status.get("overall", "unknown"))),
                ("Compatible", str(comparison.get("compatible", False))),
                ("Failure rate delta", _format_signed_rate(delta.get("failure_rate"))),
                (
                    "Coverage delta",
                    _format_signed_rate(delta.get("classification_coverage")),
                ),
            ]
        ),
        "<h2>Signal</h2>",
        f"<p>Verdict: {_verdict_cell(verdict, verdict_class)}</p>",
        _table(
            ["Regression score", "Improvement score", "Severity", "Net score"],
            [
                [
                    escape(_format_rate(signal.get("regression_score"))),
                    escape(_format_rate(signal.get("improvement_score"))),
                    escape(_format_rate(signal.get("severity"))),
                    escape(_format_signed_rate(signal.get("net_score"))),
                ]
            ],
        ),
    ]

    drivers = signal.get("top_drivers")
    sections.append("<h2>Top drivers</h2>")
    if isinstance(drivers, list) and drivers:
        driver_rows = []
        for driver in drivers:
            if not isinstance(driver, dict):
                continue
            case_ids = driver.get("case_ids")
            evidence = (
                ", ".join(
                    f"<code>{escape(str(case_id))}</code>" for case_id in case_ids
                )
                if isinstance(case_ids, list) and case_ids
                else "&mdash;"
            )
            driver_rows.append(
                [
                    escape(str(driver.get("failure_type", "unknown"))),
                    escape(_format_signed_rate(driver.get("delta"))),
                    escape(str(driver.get("direction", "unknown"))),
                    evidence,
                ]
            )
        sections.append(
            _table(["Failure type", "Delta", "Direction", "Evidence"], driver_rows)
        )
    else:
        sections.append("<p>None.</p>")

    sections.append("<h2>Case transitions</h2>")
    case_deltas = details.get("case_deltas")
    transition_rows = []
    if isinstance(case_deltas, list):
        for case_delta in case_deltas:
            if not isinstance(case_delta, dict) or not case_delta.get("changed"):
                continue
            transition_type = str(case_delta.get("transition_type", ""))
            if transition_type == "no_failure_to_failure":
                change = _verdict_cell("regressed", "fail")
            elif transition_type == "failure_to_no_failure":
                change = _verdict_cell("improved", "pass")
            else:
                change = _verdict_cell(transition_type or "changed", "neutral")
            transition_rows.append(
                [
                    f"<code>{escape(str(case_delta.get('case_id', '')))}</code>",
                    change,
                    escape(str(case_delta.get("baseline_failure_type", "n/a"))),
                    escape(str(case_delta.get("candidate_failure_type", "n/a"))),
                ]
            )
    if transition_rows:
        sections.append(
            _table(
                ["Prompt ID", "Change", "Baseline classification", "Candidate classification"],
                transition_rows,
            )
        )
    else:
        sections.append("<p>No per-case changes.</p>")

    if comparison.get("compatible") is False:
        sections.append(
            "<p><strong>Warning:</strong> comparison is incompatible, "
            "but artifacts were still written.</p>"
        )
    return _document(f"Failure Lab Compare {report.report_id}", sections)
