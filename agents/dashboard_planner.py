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
ChartType = Literal["bar", "line", "histogram", "scatter", "table"]


class DashboardKpiSpec(BaseModel):
    title: str = Field(description="Short user-facing KPI title.")
    column: str = Field(description="Column used to compute the KPI.")
    aggregation: Aggregation = Field(description="Aggregation used for the KPI.")
    rationale: str = Field(description="Why this KPI belongs on the dashboard.")


class DashboardChartSpec(BaseModel):
    title: str = Field(description="Short chart title.")
    chart_type: ChartType = Field(description="Allowed Plotly chart type.")
    dimension: str | None = Field(
        default=None,
        description="Dimension column for grouping, x-axis, or categories.",
    )
    metric: str | None = Field(
        default=None,
        description="Metric column for aggregation, y-axis, or numeric distribution.",
    )
    aggregation: Aggregation | None = Field(
        default=None,
        description="Aggregation to apply when a chart needs grouped values.",
    )
    top_n: int | None = Field(
        default=10,
        description="Optional row/category limit for readability.",
    )
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
