from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from contracts.dashboard import (
    Aggregation,
    ChartType,
    DashboardChartSpec,
    DashboardKpiSpec,
    DashboardPlan,
    DashboardQuestionView,
    Orientation,
    SortOrder,
)
from contracts.base import validate_contract
from contracts.metrics import PandasMetricPlan
from contracts.semantic import SemanticUnderstanding
from agents.semantic_understanding import (
    compact_json,
    resolve_openai_api_key,
)
from core.model_config import model_for_role, resolve_llm_max_retries, resolve_llm_timeout


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DESIGN_GUIDE_PATH = PROJECT_ROOT / "docs" / "dashboard-design-guide.md"


def load_dashboard_design_guide() -> str:
    if DASHBOARD_DESIGN_GUIDE_PATH.exists():
        return DASHBOARD_DESIGN_GUIDE_PATH.read_text(encoding="utf-8")
    return (
        "Create compact dashboards for a clear audience and decision. Prefer a few "
        "strong charts over many weak charts. Use bars for category comparison, "
        "lines for real timelines, scatter plots only for varied numeric pairs, "
        "and tables for detail. Reject high-cardinality raw tables, mixed-grain "
        "charts, crowded legends, and average/rating rankings without sample size."
    )


def build_dashboard_planner_chain(model: str | None = None):
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model_for_role("dashboard", model),
        api_key=api_key,
        temperature=0,
        timeout=resolve_llm_timeout(),
        max_retries=resolve_llm_max_retries(),
    )
    structured_llm = llm.with_structured_output(DashboardPlan)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a dashboard design agent for a data analytics app. "
                "Create a compact, useful dashboard plan from metadata, semantic "
                "understanding, metric planning output, and dataframe context. Do not write executable code. "
                "Choose only chart types from: bar, line, histogram, scatter, table. "
                "Use only columns that appear in the metadata or dataframe context. "
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
                "Use top_n to limit categories or entities, not time-series rows. "
                "Avoid top_n on scatter plots unless the referenced metric output is "
                "already a meaningful ranked or sampled dataframe. "
                "Never plot a dataframe that still has extra categorical dimensions "
                "not represented by x, color, metrics, or a filter. For example, do "
                "not plot country-year-source data as a source-only line chart unless "
                "the country dimension has already been filtered or aggregated. "
                "Line and multi-line charts should have no more than 12 visible series. "
                "If an output has too many entities or multiple grains, prefer a "
                "ranked bar chart or table, or ask for an aggregated metric output. "
                "Do not create timeline charts from outputs with fewer than two time "
                "values. Do not create scatter plots unless both axes are numeric and "
                "have meaningful variance. "
                "Ground data integrity notes only in evidence from metadata or "
                "the dataframe context; do not claim missing values, duplicates, outliers, or "
                "type problems unless the provided context supports that claim. "
                "Prefer simple charts that can be rendered deterministically with "
                "pandas and Plotly. Include a data integrity section, major KPIs, "
                "overview charts, and views that answer the suggested analytical "
                "questions. Keep the plan compact: use no more than 2 overview "
                "charts and no more than 3 question views. Tables should be "
                "exception views or compact rankings with top_n of 25 or less. "
                "Avoid duplicate charts. Keep titles concise. "
                "If numeric values are tightly clustered and a zero baseline would "
                "hide meaningful differences, set value_axis_min/value_axis_max and "
                "include a clear scale_note. Do this only when the narrowed scale is "
                "necessary for interpretation and explicitly disclosed."
            ),
            (
                "human",
                "Dashboard design guide:\n{dashboard_design_guide}\n\n"
                "Dataset metadata:\n{metadata_json}\n\n"
                "Semantic understanding:\n{semantic_json}\n\n"
                "Metric plan:\n{metric_plan_json}\n\n"
                "Dataframe context:\n{df_head}\n\n"
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
    semantic_understanding = validate_contract(SemanticUnderstanding, semantic_understanding)
    metric_plan = validate_contract(PandasMetricPlan, metric_plan)
    chain = build_dashboard_planner_chain(model=model)
    result = chain.invoke(
        {
            "metadata_json": compact_json(metadata),
            "semantic_json": semantic_understanding.model_dump_json(indent=2),
            "metric_plan_json": metric_plan.model_dump_json(indent=2),
            "df_head": df_head,
            "dashboard_design_guide": load_dashboard_design_guide(),
        }
    )
    return validate_contract(DashboardPlan, result)


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
