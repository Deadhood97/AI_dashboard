from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from contracts.base import schema_extra


Aggregation = Literal["sum", "mean", "median", "count", "nunique", "min", "max"]
ChartType = Literal[
    "bar",
    "line",
    "multi_line",
    "histogram",
    "scatter",
    "table",
    "kpi",
    "text",
]
SortOrder = Literal["ascending", "descending"]
Orientation = Literal["vertical", "horizontal"]


class DashboardKpiSpec(BaseModel):
    title: str = Field(description="Short user-facing KPI title.")
    source_output_key: str = Field(
        description="Metric plan analysis_outputs key used to render the KPI."
    )
    value_column: str | None = Field(
        default=None,
        description="Column or dictionary field to use when the output is not scalar.",
    )
    aggregation: Aggregation | None = Field(
        default=None,
        description="Optional aggregation to use when the output is tabular.",
    )
    rationale: str = Field(description="Why this KPI belongs on the dashboard.")


class DashboardChartSpec(BaseModel):
    title: str = Field(description="Short chart title.")
    chart_type: ChartType = Field(description="Allowed Plotly chart type.")
    source_output_key: str = Field(
        description="Metric plan analysis_outputs key used as the chart data source."
    )
    x: str | None = Field(default=None, description="X-axis column.")
    y: str | None = Field(default=None, description="Y-axis column.")
    color: str | None = Field(
        default=None,
        description="Optional series/color column for grouped or multi-line views.",
    )
    metrics: list[str] = Field(
        default_factory=list,
        description="Optional list of metric columns for wide-form multi-metric charts.",
    )
    dimension: str | None = Field(
        default=None,
        description="Deprecated compatibility field for grouping, x-axis, or categories.",
    )
    metric: str | None = Field(
        default=None,
        description="Deprecated compatibility field for metric, y-axis, or distribution.",
    )
    aggregation: Aggregation | None = Field(
        default=None,
        description="Aggregation to apply when a chart needs grouped values.",
    )
    top_n: int | None = Field(
        default=10,
        description="Optional row/category limit for readability.",
    )
    sort_by: str | None = Field(default=None, description="Column to sort by before rendering.")
    sort_order: SortOrder = Field(default="descending", description="Sort direction.")
    orientation: Orientation = Field(default="vertical", description="Chart orientation.")
    value_axis_min: float | None = Field(
        default=None,
        description="Optional explicit minimum for the chart's numeric value axis.",
    )
    value_axis_max: float | None = Field(
        default=None,
        description="Optional explicit maximum for the chart's numeric value axis.",
    )
    scale_note: str | None = Field(
        default=None,
        description="User-facing note explaining any non-zero or narrowed axis scale.",
    )
    question: str | None = Field(
        default=None,
        description="Analytical question this chart helps answer.",
    )
    rationale: str = Field(description="Why this chart type and fields were selected.")

    @field_validator("sort_order", mode="before")
    @classmethod
    def default_sort_order_when_null(cls, value: object) -> object:
        return "descending" if value is None else value

    @field_validator("orientation", mode="before")
    @classmethod
    def default_orientation_when_null(cls, value: object) -> object:
        return "vertical" if value is None else value

    @field_validator("metrics", mode="before")
    @classmethod
    def default_metrics_when_null(cls, value: object) -> object:
        return [] if value is None else value


class DashboardQuestionView(BaseModel):
    question: str = Field(description="Analytical question being answered.")
    answer_strategy: str = Field(
        description="How the dashboard view will answer the question."
    )
    chart: DashboardChartSpec = Field(description="Chart spec for this question.")


class DashboardPlan(BaseModel):
    model_config = schema_extra("dashboard_plan")

    dashboard_title: str = Field(description="User-facing dashboard title.")
    dashboard_summary: str = Field(
        description="Brief explanation of what the dashboard focuses on."
    )
    data_integrity_notes: list[str] = Field(
        description="Dataset quality checks or concerns the dashboard should show."
    )
    kpis: list[DashboardKpiSpec] = Field(
        description="Major KPI cards to render near the top of the dashboard."
    )
    overview_charts: list[DashboardChartSpec] = Field(
        description="General-purpose charts useful for understanding the dataset."
    )
    question_views: list[DashboardQuestionView] = Field(
        description="Views that answer semantic-agent analytical questions."
    )
    assumptions: list[str] = Field(description="Assumptions behind the dashboard plan.")
    limitations: list[str] = Field(description="Limitations of the planned dashboard.")
