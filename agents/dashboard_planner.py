from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.semantic_understanding import (
    DEFAULT_MODEL,
    SemanticUnderstanding,
    compact_json,
    resolve_openai_api_key,
)
from agents.metric_code_planner import PandasMetricPlan


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
    question: str | None = Field(
        default=None,
        description="Analytical question this chart helps answer.",
    )
    rationale: str = Field(description="Why this chart type and fields were selected.")


class DashboardQuestionView(BaseModel):
    question: str = Field(description="Analytical question being answered.")
    answer_strategy: str = Field(
        description="How the dashboard view will answer the question."
    )
    chart: DashboardChartSpec = Field(description="Chart spec for this question.")


class DashboardPlan(BaseModel):
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


def build_dashboard_planner_chain(model: str | None = None):
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        api_key=api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(DashboardPlan)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a dashboard design agent for a data analytics app. "
                "Create a compact, useful dashboard plan from metadata, semantic "
                "understanding, metric planning output, and df.head(). Do not write executable code. "
                "Choose only chart types from: bar, line, histogram, scatter, table. "
                "Use only columns that appear in the metadata or dataframe head. "
                "Use the metric plan's dashboard metrics, question analyses, and "
                "analysis output specs as the primary source for what the dashboard "
                "should calculate and display. "
                "Every KPI, overview chart, and question chart must reference a "
                "source_output_key that exists in the metric plan analysis_outputs. "
                "Use x, y, color, metrics, sort_by, sort_order, and orientation to "
                "describe how to render the referenced output. For timelines, put "
                "time on the x-axis and set sort_order to ascending. For country or "
                "entity trend comparisons, use chart_type multi_line or line with a "
                "color column. For scalar outputs, use KPI or text views. "
                "Ground data integrity notes only in evidence from metadata or "
                "df.head(); do not claim missing values, duplicates, outliers, or "
                "type problems unless the provided context supports that claim. "
                "Prefer simple charts that can be rendered deterministically with "
                "pandas and Plotly. Include a data integrity section, major KPIs, "
                "overview charts, and views that answer the suggested analytical "
                "questions. Avoid duplicate charts. Keep titles concise.",
            ),
            (
                "human",
                "Dataset metadata:\n{metadata_json}\n\n"
                "Semantic understanding:\n{semantic_json}\n\n"
                "Metric plan:\n{metric_plan_json}\n\n"
                "Dataframe head:\n{df_head}\n\n"
                "Return a structured dashboard plan.",
            ),
        ]
    )
    return prompt | structured_llm


def generate_dashboard_plan(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    df_head: str,
    model: str | None = None,
) -> DashboardPlan:
    chain = build_dashboard_planner_chain(model=model)
    return chain.invoke(
        {
            "metadata_json": compact_json(metadata),
            "semantic_json": semantic_understanding.model_dump_json(indent=2),
            "metric_plan_json": metric_plan.model_dump_json(indent=2),
            "df_head": df_head,
        }
    )


def load_metadata(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_semantic_understanding(path: Path) -> SemanticUnderstanding:
    return SemanticUnderstanding.model_validate_json(path.read_text(encoding="utf-8"))


def load_metric_plan(path: Path) -> PandasMetricPlan:
    return PandasMetricPlan.model_validate_json(path.read_text(encoding="utf-8"))


def dataframe_head_markdown(csv_path: Path, rows: int = 5) -> str:
    df = pd.read_csv(csv_path)
    return df.head(rows).to_markdown(index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a dashboard plan from metadata, semantic understanding, and CSV head."
    )
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--semantic", type=Path, required=True)
    parser.add_argument("--metric-plan", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    metadata = load_metadata(args.metadata)
    semantic_understanding = load_semantic_understanding(args.semantic)
    metric_plan = load_metric_plan(args.metric_plan)
    df_head = dataframe_head_markdown(args.csv, rows=args.rows)
    result = generate_dashboard_plan(
        metadata=metadata,
        semantic_understanding=semantic_understanding,
        metric_plan=metric_plan,
        df_head=df_head,
        model=args.model,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
