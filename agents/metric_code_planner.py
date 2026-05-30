from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Literal

from pydantic import BaseModel, Field

from agents.semantic_understanding import (
    DEFAULT_MODEL,
    SemanticUnderstanding,
    compact_json,
    resolve_openai_api_key,
)

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


def build_metric_code_planner_chain(model: str | None = None):
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        api_key=api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(PandasMetricPlan)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a senior analytics engineer writing safe, deterministic "
                "pandas analysis code. Generate code that helps answer the semantic "
                "agent's suggested questions and computes generally useful dashboard "
                "metrics. Use only pandas/numpy-style dataframe operations. Do not "
                "read files, write files, call APIs, plot charts, mutate global state, "
                "or use eval/exec. Do not import modules. Do not use scipy, sklearn, "
                "statsmodels, or custom statistical-test helpers that require import "
                "machinery. For correlation-style outputs, use pandas/numpy operations "
                "such as numeric encoding plus Series.corr/DataFrame.corr. "
                "Assume a pandas dataframe named df already exists. "
                "The code must create a dictionary named analysis_outputs and store "
                "every table, series, or scalar result in that dictionary. Use only "
                "columns that appear in the provided dataframe context, metadata, or "
                "semantic understanding. If category filters are needed, use exact "
                "values from metadata unique_values/top_values or derive categories "
                "dynamically from the dataframe; do not invent abbreviations or aliases "
                "such as 'US' when the data may store 'United States'. If an analytical "
                "question names entities but exact dataframe values are uncertain, build "
                "a defensible top-entity or latest-year ranking from available data "
                "instead of filtering to possibly nonexistent labels. If "
                "needed, include defensive column checks and date/numeric conversion. "
                "When converting columns, create a working copy such as df_work and "
                "use the converted columns in all downstream calculations. "
                "When using dropna(subset=...), the subset list must contain only "
                "real dataframe column-name strings, never data values such as years "
                "or category labels. Filter year values with boolean masks such as "
                "df_work['year'].isin([2024, 2025]), then use dropna only on required "
                "columns like ['year', 'renewables_share_elec']. "
                "When selecting multiple columns after groupby, use double brackets, "
                "for example groupby_cols[['metric_a', 'metric_b']], not a tuple key. "
                "Handle missing values intelligently instead of failing only because "
                "NaN values exist. Choose and document a missing-data strategy for "
                "each metric and question analysis. Prefer dropping rows only when "
                "the required dimension or metric is missing for that specific "
                "aggregation; use numeric imputation such as 0, median, or mean only "
                "when it is analytically defensible; use mode or 'Unknown' labels "
                "for missing categorical dimensions when that preserves useful "
                "segmentation. Store missingness counts or data-quality notes in "
                "analysis_outputs when missing values may affect interpretation. "
                "Raise errors only for missing required columns or completely "
                "unusable data after cleaning. "
                "For every analysis_outputs entry, provide semantic_role, columns, "
                "and recommended_views so dashboard agents can render it without "
                "guessing. For time series by entity, output a dataframe with a time "
                "column, value column, and entity column. For multi-metric trends, "
                "prefer tidy long-form outputs with columns like year, metric_name, "
                "metric_value, and optional entity. "
                "For rankings based on averages, ratings, scores, or prices, always "
                "include a count/sample-size column and apply a defensible minimum "
                "sample-size filter before presenting a top-ranked chart. If the "
                "dataset is large, use at least 5 records per ranked group unless "
                "the metadata proves a different threshold is better. Do not present "
                "one-record categories as 'top' performers without a visible warning "
                "or table fallback. For high-cardinality text columns such as "
                "descriptions, do not output the full raw text table as a dashboard "
                "view; create summary statistics, representative samples, or modeling "
                "readiness counts instead. "
                "Return a structured plan that other agents can read and an app can "
                "render: dashboard metric specs, per-question analysis specs, output "
                "specs, assumptions, limitations, and pandas code.",
            ),
            (
                "human",
                "Semantic understanding JSON:\n{semantic_json}\n\n"
                "Dataframe context:\n{df_head}\n\n"
                "Generate the pandas metric plan and code.",
            ),
        ]
    )

    return prompt | structured_llm


def generate_metric_code_plan(
    semantic_understanding: SemanticUnderstanding,
    df_head: str,
    model: str | None = None,
) -> PandasMetricPlan:
    chain = build_metric_code_planner_chain(model=model)
    return chain.invoke(
        {
            "semantic_json": semantic_understanding.model_dump_json(indent=2),
            "df_head": df_head,
        }
    )


def repair_metric_code_plan(
    failed_plan: PandasMetricPlan,
    semantic_understanding: SemanticUnderstanding,
    df_head: str,
    error_message: str,
    failing_code: str = "",
    model: str | None = None,
) -> PandasMetricPlan:
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        api_key=api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(PandasMetricPlan)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You repair pandas metric plans. The previous plan failed during "
                "safe execution. Return a corrected complete PandasMetricPlan. "
                "Preserve the original analytical intent, but fix the code and "
                "structured output specs so they are internally consistent. Do not "
                "read files, write files, call APIs, plot charts, use eval/exec, or "
                "import modules. Do not use scipy, sklearn, statsmodels, or helper "
                "functions that depend on Python import machinery. For correlation "
                "analyses, use pandas/numpy-native operations. Assume df already exists. "
                "The code must create analysis_outputs as a dictionary. Return plain "
                "top-level Python statements only: no markdown fences, no prose, no "
                "dangling else/elif blocks, and no code nested under a nonexistent "
                "if/try/function block. Every if/else block must be syntactically "
                "complete.",
            ),
            (
                "human",
                "Semantic understanding:\n{semantic_json}\n\n"
                "Dataframe context:\n{df_head}\n\n"
                "Failed metric plan:\n{failed_plan_json}\n\n"
                "Execution error:\n{error_message}\n\n"
                "Sanitized failing code:\n{failing_code}\n\n"
                "Return the repaired metric plan.",
            ),
        ]
    )
    chain = prompt | structured_llm
    return chain.invoke(
        {
            "semantic_json": semantic_understanding.model_dump_json(indent=2),
            "df_head": df_head,
            "failed_plan_json": failed_plan.model_dump_json(indent=2),
            "error_message": error_message,
            "failing_code": failing_code,
        }
    )


def load_semantic_understanding(path: Path) -> SemanticUnderstanding:
    data = json.loads(path.read_text(encoding="utf-8"))
    return SemanticUnderstanding.model_validate(data)


def dataframe_head_markdown(csv_path: Path, rows: int = 5) -> str:
    df = pd.read_csv(csv_path)
    return df.head(rows).to_markdown(index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pandas metric code from semantic understanding and CSV head."
    )
    parser.add_argument("--semantic", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    semantic_understanding = load_semantic_understanding(args.semantic)
    df_head = dataframe_head_markdown(args.csv, rows=args.rows)
    result = generate_metric_code_plan(
        semantic_understanding=semantic_understanding,
        df_head=df_head,
        model=args.model,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
