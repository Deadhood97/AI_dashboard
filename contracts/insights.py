from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from contracts.base import schema_extra
from contracts.dashboard import DashboardPlan
from contracts.metrics import PandasMetricPlan
from contracts.semantic import SemanticUnderstanding
from contracts.validation import DashboardValidationReport


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
    model_config = schema_extra("analytical_brain_result")

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
    model_config = schema_extra("analytical_brain_input")

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
