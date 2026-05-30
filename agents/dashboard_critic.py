from __future__ import annotations

import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.dashboard_planner import DashboardPlan, load_dashboard_design_guide
from agents.metric_code_planner import PandasMetricPlan
from agents.semantic_understanding import (
    DEFAULT_MODEL,
    SemanticUnderstanding,
    compact_json,
    resolve_openai_api_key,
)
from dashboard_validation import DashboardValidationReport


class DashboardCritique(BaseModel):
    critique_summary: str = Field(
        description="Brief explanation of why the original dashboard needed repair."
    )
    repaired_dashboard_plan: DashboardPlan = Field(
        description="A complete repaired dashboard plan that should pass validation."
    )
    repair_notes: list[str] = Field(
        description="Specific changes made to improve dashboard quality."
    )
    remaining_risks: list[str] = Field(
        description="Known residual limitations after repair."
    )


def build_dashboard_critic_chain(model: str | None = None):
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        api_key=api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(DashboardCritique)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a dashboard quality critic and repair agent. You receive a "
                "dashboard plan, metric plan, deterministic validation report, "
                "semantic understanding, metadata, and dataframe context. Repair the "
                "dashboard plan so it is more likely to pass validation and be useful "
                "to a real analyst. Do not write executable code. Do not invent new "
                "analysis output keys. Use only source_output_key values declared in "
                "the metric plan analysis_outputs. "
                "Remove or replace charts that failed validation. Prefer fewer, "
                "clearer charts over dense dashboards. For outputs with mixed grain "
                "or extra categorical dimensions, use table views unless the metric "
                "output is already aggregated or filtered. For line charts, keep time "
                "on x, use a meaningful color/entity column, set top_n when needed, "
                "and ensure no more than 12 visible series. For ranked outputs, use "
                "bar charts or tables. For correlation outputs, prefer tables unless "
                "a clean scatter output already exists. For 100% threshold outputs, "
                "prefer tables and KPI counts. "
                "Keep the repaired plan compact: no more than 2 overview charts, "
                "no more than 3 question views, and table top_n values of 25 or "
                "less. If many table views remain, keep only the ones that best "
                "support decisions and move the rest to limitations. "
                "The repaired_dashboard_plan must be complete, compact, and should "
                "not include charts mentioned in rejected_chart_titles unless they "
                "have been changed to a safer table or fixed to address the exact "
                "validation issue.",
            ),
            (
                "human",
                "Dashboard design guide:\n{dashboard_design_guide}\n\n"
                "Dataset metadata:\n{metadata_json}\n\n"
                "Semantic understanding:\n{semantic_json}\n\n"
                "Metric plan:\n{metric_plan_json}\n\n"
                "Original dashboard plan:\n{dashboard_plan_json}\n\n"
                "Validation report:\n{validation_report_json}\n\n"
                "Dataframe context:\n{df_context}\n\n"
                "Return a repaired dashboard critique.",
            ),
        ]
    )
    return prompt | structured_llm


def repair_dashboard_plan(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    dashboard_plan: DashboardPlan,
    validation_report: DashboardValidationReport,
    df_context: str,
    model: str | None = None,
) -> DashboardCritique:
    chain = build_dashboard_critic_chain(model=model)
    return chain.invoke(
        {
            "metadata_json": compact_json(metadata),
            "semantic_json": semantic_understanding.model_dump_json(indent=2),
            "metric_plan_json": metric_plan.model_dump_json(indent=2),
            "dashboard_plan_json": dashboard_plan.model_dump_json(indent=2),
            "validation_report_json": validation_report.model_dump_json(indent=2),
            "df_context": df_context,
            "dashboard_design_guide": load_dashboard_design_guide(),
        }
    )
