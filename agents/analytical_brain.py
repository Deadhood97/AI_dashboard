from __future__ import annotations

import os
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.dashboard_planner import DashboardPlan
from agents.metric_code_planner import PandasMetricPlan
from agents.semantic_understanding import (
    DEFAULT_MODEL,
    SemanticUnderstanding,
    compact_json,
    resolve_openai_api_key,
)
from dashboard_validation import DashboardValidationReport

InsightConfidence = Literal["high", "medium", "low"]
InsightImpact = Literal["critical", "high", "medium", "low"]


class DashboardInsight(BaseModel):
    headline: str = Field(description="Concise executive insight headline.")
    explanation: str = Field(
        description="Plain-language explanation grounded in dashboard outputs."
    )
    evidence: list[str] = Field(
        description="Specific metrics, chart outputs, or comparisons supporting the insight."
    )
    business_implication: str = Field(
        description="Why this insight matters for decisions or follow-up analysis."
    )
    recommended_action: str = Field(
        description="Practical next step a user could take based on this insight."
    )
    confidence: InsightConfidence = Field(
        description="Confidence based on data quality, validation status, and supporting evidence."
    )
    impact: InsightImpact = Field(description="Likely importance of this insight.")
    related_dashboard_items: list[str] = Field(
        description="Dashboard KPI/chart/question titles that support this insight."
    )


class AnalyticalBrainResult(BaseModel):
    executive_summary: str = Field(
        description="Short synthesis of what the generated dashboard is telling the user."
    )
    key_insights: list[DashboardInsight] = Field(
        description="Prioritized, evidence-backed insights from the dashboard."
    )
    watchouts: list[str] = Field(
        description="Limitations, caveats, or data quality risks that affect interpretation."
    )
    follow_up_questions: list[str] = Field(
        description="High-value analytical questions to investigate next."
    )
    narrative_title: str = Field(
        description="Brief title for the analytical narrative."
    )


class AnalyticalBrainInput(BaseModel):
    metadata: dict[str, Any] = Field(description="Saved dataset metadata.")
    semantic_understanding: SemanticUnderstanding = Field(
        description="Structured output from the semantic understanding agent."
    )
    metric_plan: PandasMetricPlan = Field(
        description="Structured output from the metric code planner."
    )
    analysis_outputs: dict[str, Any] = Field(
        description="Executed deterministic metric outputs, compacted for LLM context."
    )
    dashboard_plan: DashboardPlan = Field(
        description="Final dashboard plan shown to the user."
    )
    validation_report: DashboardValidationReport = Field(
        description="Deterministic dashboard validation report."
    )
    df_context: str = Field(
        description="Compact dataframe context used by upstream agents."
    )


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def compact_analysis_outputs(analysis_outputs: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in analysis_outputs.items():
        if hasattr(value, "columns") and hasattr(value, "head") and hasattr(value, "to_dict"):
            frame = value.head(12)
            compacted[key] = {
                "type": type(value).__name__,
                "shape": list(getattr(value, "shape", [])),
                "columns": [str(column) for column in getattr(value, "columns", [])],
                "sample": [
                    {str(k): json_safe(v) for k, v in row.items()}
                    for row in frame.to_dict(orient="records")
                ],
            }
        elif hasattr(value, "to_dict"):
            sample = value.head(12).to_dict() if hasattr(value, "head") else value.to_dict()
            compacted[key] = {
                "type": type(value).__name__,
                "sample": {str(k): json_safe(v) for k, v in sample.items()}
                if isinstance(sample, dict)
                else json_safe(sample),
            }
        else:
            compacted[key] = json_safe(value)
    return compacted


def build_analytical_brain_chain(model: str | None = None):
    api_key = resolve_openai_api_key()
    llm = ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        api_key=api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(AnalyticalBrainResult)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are the analytical brain of a dashboarding system. Your job is "
                "to synthesize the semantic agent output, executed metric outputs, "
                "final dashboard plan, and validation report into excellent, grounded "
                "business insights. Do not invent facts. Use only evidence present in "
                "the provided analysis outputs, dashboard plan, metadata, and semantic "
                "understanding. If evidence is weak, say so in watchouts and lower "
                "confidence. Prefer insights that compare segments, trends, rankings, "
                "outliers, concentration, changes over time, and operational risks. "
                "Avoid generic statements such as 'monitor this metric' unless tied "
                "to a specific observed pattern. Keep the result concise but valuable: "
                "3 to 6 key insights, each with evidence, implication, action, "
                "confidence, impact, and related dashboard items. Respect validation: "
                "do not base key insights on rejected or hidden dashboard components.",
            ),
            (
                "human",
                "Dataset metadata:\n{metadata_json}\n\n"
                "Semantic understanding:\n{semantic_json}\n\n"
                "Metric plan:\n{metric_plan_json}\n\n"
                "Analysis outputs sample:\n{analysis_outputs_json}\n\n"
                "Final dashboard plan:\n{dashboard_plan_json}\n\n"
                "Validation report:\n{validation_report_json}\n\n"
                "Dataframe context:\n{df_context}\n\n"
                "Return the analytical brain result.",
            ),
        ]
    )
    return prompt | structured_llm


def generate_analytical_insights(
    analytical_input: AnalyticalBrainInput,
    model: str | None = None,
) -> AnalyticalBrainResult:
    chain = build_analytical_brain_chain(model=model)
    return chain.invoke(
        {
            "metadata_json": compact_json(analytical_input.metadata),
            "semantic_json": analytical_input.semantic_understanding.model_dump_json(indent=2),
            "metric_plan_json": analytical_input.metric_plan.model_dump_json(indent=2),
            "analysis_outputs_json": compact_json(analytical_input.analysis_outputs),
            "dashboard_plan_json": analytical_input.dashboard_plan.model_dump_json(indent=2),
            "validation_report_json": analytical_input.validation_report.model_dump_json(indent=2),
            "df_context": analytical_input.df_context,
        }
    )


def build_analytical_brain_input(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
    dashboard_plan: DashboardPlan,
    validation_report: DashboardValidationReport,
    df_context: str,
) -> AnalyticalBrainInput:
    return AnalyticalBrainInput(
        metadata=metadata,
        semantic_understanding=semantic_understanding,
        metric_plan=metric_plan,
        analysis_outputs=compact_analysis_outputs(analysis_outputs),
        dashboard_plan=dashboard_plan,
        validation_report=validation_report,
        df_context=df_context,
    )
