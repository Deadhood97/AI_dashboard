from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from contracts.base import schema_extra


OutputRole = Literal[
    "scalar",
    "ranked_table",
    "time_series",
    "time_series_by_entity",
    "categorical_comparison",
    "correlation_pair",
    "distribution",
    "raw_table",
    "data_quality",
]

RecommendedView = Literal[
    "kpi_card",
    "bar_chart",
    "line_chart",
    "multi_line_chart",
    "scatter_plot",
    "histogram",
    "table",
    "text_insight",
]


class DashboardMetricSpec(BaseModel):
    name: str = Field(description="Short dashboard metric name.")
    business_purpose: str = Field(description="Why this metric matters to a user.")
    calculation: str = Field(description="Plain-language calculation description.")
    output_key: str = Field(
        description="Key in analysis_outputs where this metric result will be stored."
    )
    required_columns: list[str] = Field(
        description="Columns needed to calculate this metric."
    )
    missing_data_strategy: str = Field(
        description=(
            "How missing values should be handled for this metric, such as drop "
            "invalid rows, fill numeric values with 0, median imputation, mode "
            "imputation, or report missingness separately."
        )
    )


class QuestionAnalysisSpec(BaseModel):
    question: str = Field(description="Question from the semantic understanding.")
    analysis_strategy: str = Field(
        description="Plain-language description of how pandas should answer the question."
    )
    output_key: str = Field(
        description="Key in analysis_outputs where this question's result will be stored."
    )
    required_columns: list[str] = Field(
        description="Columns needed to answer the question."
    )
    missing_data_strategy: str = Field(
        description="How missing values should be handled for this question analysis."
    )


class AnalysisOutputSpec(BaseModel):
    key: str = Field(description="Key used in the analysis_outputs dictionary.")
    output_type: str = Field(
        description="Expected output type, such as scalar, dataframe, series, or dictionary."
    )
    semantic_role: OutputRole = Field(
        description="Analytical shape of this output for downstream dashboard planning."
    )
    columns: list[str] = Field(
        description="Expected columns or value fields present in this output."
    )
    recommended_views: list[RecommendedView] = Field(
        description="Supported visual views that would fit this output."
    )
    description: str = Field(description="What the output contains.")
    render_hint: str = Field(
        description="How the app or a future agent could render or use this output."
    )


class PandasMetricPlan(BaseModel):
    model_config = schema_extra("pandas_metric_plan")

    agent_summary: str = Field(
        description="Short explanation of what this metric plan is trying to calculate."
    )
    required_columns: list[str] = Field(
        description="All dataframe columns required by the generated pandas code."
    )
    dashboard_metrics: list[DashboardMetricSpec] = Field(
        description="General dashboard KPI metrics the code should calculate."
    )
    question_analyses: list[QuestionAnalysisSpec] = Field(
        description="Analysis tasks mapped to the semantic agent's suggested questions."
    )
    analysis_outputs: list[AnalysisOutputSpec] = Field(
        description="Structured description of every expected analysis_outputs entry."
    )
    pandas_code: str = Field(
        description=(
            "Executable pandas code. It must assume a dataframe named df already "
            "exists and store all outputs in a dictionary named analysis_outputs."
        )
    )
    assumptions: list[str] = Field(
        description="Assumptions made because only df.head() and semantic understanding were provided."
    )
    limitations: list[str] = Field(
        description="Known limitations or checks needed before executing the code."
    )
