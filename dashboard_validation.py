from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from agents.dashboard_planner import DashboardChartSpec, DashboardPlan
from agents.metric_code_planner import PandasMetricPlan


IssueSeverity = Literal["info", "warning", "error"]
IssueComponent = Literal["metric_output", "kpi", "chart"]


class ValidationIssue(BaseModel):
    severity: IssueSeverity
    component: IssueComponent
    item_title: str
    source_output_key: str | None = None
    message: str
    suggested_fix: str


class DashboardValidationReport(BaseModel):
    status: Literal["passed", "passed_with_warnings", "failed"]
    issues: list[ValidationIssue] = Field(default_factory=list)
    rejected_chart_titles: list[str] = Field(default_factory=list)
    rejected_kpi_titles: list[str] = Field(default_factory=list)


def output_to_dataframe(output: Any) -> pd.DataFrame:
    if isinstance(output, pd.DataFrame):
        return output.copy()
    if isinstance(output, pd.Series):
        return output.reset_index()
    if isinstance(output, dict):
        return pd.DataFrame([output])
    if isinstance(output, (list, tuple)):
        return pd.DataFrame(output)
    return pd.DataFrame({"value": [output]})


def _numeric_columns(table: pd.DataFrame) -> set[str]:
    return set(table.select_dtypes(include="number").columns.astype(str))


def _categorical_columns(table: pd.DataFrame) -> list[str]:
    categorical: list[str] = []
    for column in table.columns:
        if column in _numeric_columns(table):
            continue
        if table[column].nunique(dropna=True) > 1:
            categorical.append(str(column))
    return categorical


def _count_columns(table: pd.DataFrame) -> list[str]:
    return [
        str(column)
        for column in table.columns
        if str(column).lower() in {"count", "n", "sample_size", "record_count", "review_count"}
        and column in _numeric_columns(table)
    ]


def _looks_like_average_metric(column: str | None) -> bool:
    if not column:
        return False
    lowered = column.lower()
    return any(token in lowered for token in ["avg", "average", "mean", "rating", "points", "score"])


def _has_long_text_column(table: pd.DataFrame) -> bool:
    for column in table.select_dtypes(include="object").columns:
        sample = table[column].dropna().astype(str).head(100)
        if not sample.empty and sample.str.len().mean() > 80:
            return True
    return False


def _numeric_range(table: pd.DataFrame, columns: list[str]) -> tuple[float, float] | None:
    values: list[float] = []
    for column in columns:
        if column not in table.columns:
            continue
        numeric = pd.to_numeric(table[column], errors="coerce").dropna()
        values.extend(float(value) for value in numeric.tolist())
    if not values:
        return None
    return min(values), max(values)


def _needs_explicit_scale(table: pd.DataFrame, columns: list[str]) -> bool:
    numeric_range = _numeric_range(table, columns)
    if numeric_range is None:
        return False

    min_value, max_value = numeric_range
    if min_value <= 0 or max_value <= 0 or min_value == max_value:
        return False

    value_span = max_value - min_value
    max_abs = max(abs(min_value), abs(max_value), 1.0)
    return value_span / max_abs <= 0.18 and min_value / max(max_value, 1.0) >= 0.55


def _has_declared_scale(spec: DashboardChartSpec) -> bool:
    return (
        spec.value_axis_min is not None
        and spec.value_axis_max is not None
        and bool(spec.scale_note and spec.scale_note.strip())
    )


def _issue(
    severity: IssueSeverity,
    component: IssueComponent,
    item_title: str,
    message: str,
    suggested_fix: str,
    source_output_key: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        severity=severity,
        component=component,
        item_title=item_title,
        source_output_key=source_output_key,
        message=message,
        suggested_fix=suggested_fix,
    )


def validate_metric_outputs(
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for spec in metric_plan.analysis_outputs:
        if spec.key not in analysis_outputs:
            issues.append(
                _issue(
                    "error",
                    "metric_output",
                    spec.key,
                    "Declared metric output was not produced by the executed code.",
                    "Repair the metric plan so every declared output key is populated.",
                    spec.key,
                )
            )
            continue

        if spec.output_type == "scalar" or spec.semantic_role == "scalar":
            continue

        if isinstance(analysis_outputs[spec.key], dict):
            output_keys = set(analysis_outputs[spec.key].keys())
            missing_columns = [
                column
                for column in spec.columns
                if column not in output_keys and column not in {"description", "variety"}
            ]
            if missing_columns:
                issues.append(
                    _issue(
                        "warning",
                        "metric_output",
                        spec.key,
                        f"Dictionary output does not include declared fields: {missing_columns}.",
                        "Update the output spec to list produced dictionary fields, or render this as a text summary.",
                        spec.key,
                    )
                )
            continue

        table = output_to_dataframe(analysis_outputs[spec.key])
        if table.empty:
            issues.append(
                _issue(
                    "warning",
                    "metric_output",
                    spec.key,
                    "Metric output is empty.",
                    "Use this output only as a table with a clear empty-state note, or repair the metric calculation.",
                    spec.key,
                )
            )
            continue

        missing_columns = [column for column in spec.columns if column not in table.columns]
        if missing_columns:
            issues.append(
                _issue(
                    "error",
                    "metric_output",
                    spec.key,
                    f"Metric output is missing expected columns: {missing_columns}.",
                    "Repair the metric plan output spec or generated pandas code so they match.",
                    spec.key,
                )
            )
    return issues


def validate_chart_spec(
    spec: DashboardChartSpec,
    analysis_outputs: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if spec.source_output_key not in analysis_outputs:
        return [
            _issue(
                "error",
                "chart",
                spec.title,
                "Chart references an analysis output that does not exist.",
                "Choose a source_output_key from the executed metric outputs.",
                spec.source_output_key,
            )
        ]

    table = output_to_dataframe(analysis_outputs[spec.source_output_key])
    if table.empty:
        return [
            _issue(
                "warning",
                "chart",
                spec.title,
                "Chart data is empty.",
                "Render a table or empty-state note instead of a chart.",
                spec.source_output_key,
            )
        ]

    x = spec.x or spec.dimension
    y = spec.y or spec.metric
    protected_columns = {column for column in [x, y, spec.color] if column}
    protected_columns.update(spec.metrics)

    if spec.chart_type in {"line", "multi_line", "bar", "scatter", "histogram"}:
        if x and x not in table.columns and spec.chart_type != "histogram":
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    f"X-axis column '{x}' is not present in the output.",
                    "Repair the dashboard plan to use an available output column.",
                    spec.source_output_key,
                )
            )
        if y and y not in table.columns:
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    f"Y-axis column '{y}' is not present in the output.",
                    "Repair the dashboard plan to use an available output column.",
                    spec.source_output_key,
                )
            )
        for metric in spec.metrics:
            if metric not in table.columns:
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        f"Metric column '{metric}' is not present in the output.",
                        "Repair the dashboard plan to use available metric columns.",
                        spec.source_output_key,
                    )
                )

    if spec.chart_type in {"line", "multi_line"}:
        has_y_values = bool(y or spec.metrics)
        if not x or not has_y_values:
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    "Line charts require x and y fields or a metrics list.",
                    "Use a table, provide explicit x/y columns, or provide metrics for a wide-form line chart.",
                    spec.source_output_key,
                )
            )
        elif x in table.columns and (not y or y in table.columns):
            if table[x].nunique(dropna=True) < 2:
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        "Timeline chart has fewer than two x-axis values.",
                        "Use a KPI/table, or repair the metric output to include a real timeline.",
                        spec.source_output_key,
                    )
                )

            if spec.color and spec.color in table.columns:
                series_count = int(table[spec.color].nunique(dropna=True))
                visible_series_limit = spec.top_n if spec.top_n else series_count
                if visible_series_limit > 12:
                    issues.append(
                        _issue(
                            "error",
                            "chart",
                            spec.title,
                            f"Line chart has too many series ({series_count}).",
                            "Filter to a ranked set of entities or aggregate before plotting.",
                            spec.source_output_key,
                        )
                    )

            duplicate_grain = table.duplicated(subset=[column for column in [x, spec.color] if column in table.columns]).any()
            ignored_dimensions = [
                column
                for column in _categorical_columns(table)
                if column not in protected_columns
            ]
            if duplicate_grain and ignored_dimensions:
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        f"Chart ignores additional dimensions with multiple values: {ignored_dimensions}.",
                        "Aggregate or filter those dimensions before plotting, or include the correct entity as color.",
                        spec.source_output_key,
                    )
                )

            y_columns = [y] if y else []
            if spec.metrics:
                y_columns.extend(metric for metric in spec.metrics if metric in table.columns)
            if _needs_explicit_scale(table, y_columns) and not _has_declared_scale(spec):
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        "Line values are tightly clustered, so a zero-baseline chart hides the meaningful differences.",
                        "Repair the chart spec with value_axis_min, value_axis_max, and a scale_note that discloses the narrowed axis.",
                        spec.source_output_key,
                    )
                )

    if spec.chart_type == "bar":
        if not x or not y:
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    "Bar charts require x and y fields.",
                    "Use a table or provide explicit categorical and metric columns.",
                    spec.source_output_key,
                )
            )
        elif x in table.columns and y in table.columns:
            if spec.color and spec.color in table.columns:
                color_values = int(table[spec.color].nunique(dropna=True))
                color_values_after_limit = (
                    min(color_values, spec.top_n) if spec.top_n else color_values
                )
                if "type" in spec.color.lower() and color_values > 1:
                    issues.append(
                        _issue(
                            "error",
                            "chart",
                            spec.title,
                            f"Bar chart mixes multiple analytical grains through '{spec.color}'.",
                            "Split the output into separate charts/tables or aggregate to one comparable grain.",
                            spec.source_output_key,
                        )
                    )
                elif color_values_after_limit > 8:
                    issues.append(
                        _issue(
                            "warning",
                            "chart",
                            spec.title,
                            f"Bar chart may produce a crowded color legend ({color_values} groups).",
                            "Use fewer groups, remove color, or render a table.",
                            spec.source_output_key,
                        )
                    )

            if _looks_like_average_metric(y):
                count_columns = _count_columns(table)
                if not count_columns and table[x].nunique(dropna=True) > 50:
                    issues.append(
                        _issue(
                            "error",
                            "chart",
                            spec.title,
                            "Average/rating ranking has many categories but no sample-size column.",
                            "Repair the metric output to include count and filter to a defensible minimum sample size.",
                            spec.source_output_key,
                        )
                    )
                elif count_columns:
                    sort_column = spec.sort_by if spec.sort_by in table.columns else y
                    ascending = spec.sort_order == "ascending"
                    visible_rows = (
                        table.sort_values(sort_column, ascending=ascending).head(spec.top_n)
                        if spec.top_n
                        else table
                    )
                    if visible_rows[count_columns[0]].min(skipna=True) < 5:
                        issues.append(
                            _issue(
                                "error",
                                "chart",
                                spec.title,
                                "Top average/rating results include categories with fewer than 5 records.",
                                "Filter rankings to groups with at least 5 records or display the result as a table with count.",
                                spec.source_output_key,
                            )
                        )
            if _needs_explicit_scale(table, [y]) and not _has_declared_scale(spec):
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        "Bar values are tightly clustered, so a zero-baseline chart hides the meaningful differences.",
                        "Repair the chart spec with value_axis_min, value_axis_max, and a scale_note that discloses the narrowed axis.",
                        spec.source_output_key,
                    )
                )
            if x in table.columns and table[x].nunique(dropna=True) > 25 and not spec.top_n:
                issues.append(
                    _issue(
                        "warning",
                        "chart",
                        spec.title,
                        "Bar chart has many categories and no top_n limit.",
                        "Use a ranked top_n value or render a table.",
                        spec.source_output_key,
                    )
                )
        elif x in table.columns and table[x].nunique(dropna=True) > 25 and not spec.top_n:
            issues.append(
                _issue(
                    "warning",
                    "chart",
                    spec.title,
                    "Bar chart has many categories and no top_n limit.",
                    "Use a ranked top_n value or render a table.",
                    spec.source_output_key,
                )
            )

    if spec.chart_type == "table":
        if spec.top_n and spec.top_n > 25:
            issues.append(
                _issue(
                    "warning",
                    "chart",
                    spec.title,
                    f"Table requests {spec.top_n} visible rows, which is too dense for the dashboard.",
                    "Use top_n of 25 or less, or move the detail to a drill-down view.",
                    spec.source_output_key,
                )
            )
        if len(table) > 1000 and spec.top_n is None:
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    f"Table has {len(table)} rows and no display limit.",
                    "Summarize, sample, or set a small top_n value before rendering.",
                    spec.source_output_key,
                )
            )
        if len(table) > 100 and _has_long_text_column(table):
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    "Table contains many long text rows, which is not readable as a dashboard component.",
                    "Replace with summary metrics, text-quality statistics, or a small labeled sample.",
                    spec.source_output_key,
                )
            )

    if spec.chart_type == "scatter":
        if not x or not y or x not in table.columns or y not in table.columns:
            issues.append(
                _issue(
                    "error",
                    "chart",
                    spec.title,
                    "Scatter plots require valid x and y numeric fields.",
                    "Choose two numeric columns from the same validated output.",
                    spec.source_output_key,
                )
            )
        else:
            numeric_columns = _numeric_columns(table)
            if x not in numeric_columns or y not in numeric_columns:
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        "Scatter plot axes are not both numeric.",
                        "Use numeric columns for scatter plots or switch to a table/bar chart.",
                        spec.source_output_key,
                    )
                )
            if table[x].nunique(dropna=True) < 3 or table[y].nunique(dropna=True) < 3:
                issues.append(
                    _issue(
                        "error",
                        "chart",
                        spec.title,
                        "Scatter plot has collapsed or near-constant axes.",
                        "Use a table or repair the metric output to preserve meaningful variance.",
                        spec.source_output_key,
                    )
                )
            if spec.color and spec.color in table.columns and table[spec.color].nunique(dropna=True) > 20:
                issues.append(
                    _issue(
                        "warning",
                        "chart",
                        spec.title,
                        "Scatter plot has a very large color legend.",
                        "Remove color, group categories, or use a smaller validated sample.",
                        spec.source_output_key,
                    )
                )

    return issues


def validate_dashboard_plan(
    dashboard_plan: DashboardPlan,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
) -> DashboardValidationReport:
    issues = validate_metric_outputs(metric_plan, analysis_outputs)
    rejected_chart_titles: list[str] = []
    rejected_kpi_titles: list[str] = []

    for kpi in dashboard_plan.kpis:
        if kpi.source_output_key not in analysis_outputs:
            issues.append(
                _issue(
                    "error",
                    "kpi",
                    kpi.title,
                    "KPI references an analysis output that does not exist.",
                    "Choose a KPI source from the executed metric outputs.",
                    kpi.source_output_key,
                )
            )
            rejected_kpi_titles.append(kpi.title)

    charts = dashboard_plan.overview_charts + [
        question_view.chart for question_view in dashboard_plan.question_views
    ]
    if len(dashboard_plan.overview_charts) > 2:
        issues.append(
            _issue(
                "warning",
                "chart",
                "Dashboard overview",
                f"Dashboard has {len(dashboard_plan.overview_charts)} overview charts.",
                "Keep no more than 2 overview charts in the MVP dashboard.",
            )
        )
    if len(dashboard_plan.question_views) > 3:
        issues.append(
            _issue(
                "warning",
                "chart",
                "Dashboard question views",
                f"Dashboard has {len(dashboard_plan.question_views)} question views.",
                "Keep no more than 3 supporting question views in the MVP dashboard.",
            )
        )
    for chart in charts:
        chart_issues = validate_chart_spec(chart, analysis_outputs)
        issues.extend(chart_issues)
        if any(issue.severity == "error" for issue in chart_issues):
            rejected_chart_titles.append(chart.title)

    if any(issue.severity == "error" for issue in issues):
        status: Literal["passed", "passed_with_warnings", "failed"] = "failed"
    elif any(issue.severity == "warning" for issue in issues):
        status = "passed_with_warnings"
    else:
        status = "passed"

    return DashboardValidationReport(
        status=status,
        issues=issues,
        rejected_chart_titles=list(dict.fromkeys(rejected_chart_titles)),
        rejected_kpi_titles=list(dict.fromkeys(rejected_kpi_titles)),
    )


def chart_is_rejected(report: DashboardValidationReport | None, title: str) -> bool:
    return bool(report and title in report.rejected_chart_titles)


def kpi_is_rejected(report: DashboardValidationReport | None, title: str) -> bool:
    return bool(report and title in report.rejected_kpi_titles)
