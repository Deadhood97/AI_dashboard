from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from contracts.base import validate_contract
from contracts.insights import (
    AnalyticalBrainInput,
    AnalyticalBrainResult,
    DashboardInsight,
    InsightConfidence,
    InsightImpact,
)
from contracts.dashboard import DashboardPlan
from contracts.metrics import PandasMetricPlan
from contracts.semantic import SemanticUnderstanding
from contracts.validation import DashboardValidationReport
from agents.semantic_understanding import (
    compact_json,
    resolve_openai_api_key,
)
from core.model_config import model_for_role, resolve_llm_max_retries, resolve_llm_timeout


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
        model=model_for_role("insights", model),
        api_key=api_key,
        temperature=0,
        timeout=resolve_llm_timeout(),
        max_retries=resolve_llm_max_retries(),
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
    analytical_input = validate_contract(AnalyticalBrainInput, analytical_input)
    chain = build_analytical_brain_chain(model=model)
    result = chain.invoke(
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
    return validate_contract(AnalyticalBrainResult, result)


def build_analytical_brain_input(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
    dashboard_plan: DashboardPlan,
    validation_report: DashboardValidationReport,
    df_context: str,
) -> AnalyticalBrainInput:
    semantic_understanding = validate_contract(SemanticUnderstanding, semantic_understanding)
    metric_plan = validate_contract(PandasMetricPlan, metric_plan)
    dashboard_plan = validate_contract(DashboardPlan, dashboard_plan)
    validation_report = validate_contract(DashboardValidationReport, validation_report)
    return validate_contract(
        AnalyticalBrainInput,
        {
            "metadata": metadata,
            "semantic_understanding": semantic_understanding,
            "metric_plan": metric_plan,
            "analysis_outputs": compact_analysis_outputs(analysis_outputs),
            "dashboard_plan": dashboard_plan,
            "validation_report": validation_report,
            "df_context": df_context,
        },
    )
