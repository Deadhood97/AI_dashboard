from __future__ import annotations

import logging
from typing import Any, Callable

from agents.dashboard_critic import repair_dashboard_plan
from agents.dashboard_planner import generate_dashboard_plan
from contracts import (
    DashboardCritique,
    DashboardPlan,
    DashboardValidationReport,
    PandasMetricPlan,
    SemanticUnderstanding,
)
from contracts.base import validate_contract
from dashboard_validation import validate_dashboard_plan


logger = logging.getLogger(__name__)


def generate_validated_dashboard_plan(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
    df_context: str,
    max_repairs: int = 1,
    critic_event_callback: Callable[[str, dict[str, Any]], None] | None = None,
) -> tuple[DashboardPlan, DashboardValidationReport, DashboardCritique | None]:
    semantic_understanding = validate_contract(SemanticUnderstanding, semantic_understanding)
    metric_plan = validate_contract(PandasMetricPlan, metric_plan)
    dashboard_plan = generate_dashboard_plan(
        metadata=metadata,
        semantic_understanding=semantic_understanding,
        metric_plan=metric_plan,
        df_head=df_context,
    )
    dashboard_plan = validate_contract(DashboardPlan, dashboard_plan)
    validation_report = validate_dashboard_plan(
        dashboard_plan=dashboard_plan,
        metric_plan=metric_plan,
        analysis_outputs=analysis_outputs,
    )
    validation_report = validate_contract(DashboardValidationReport, validation_report)
    critique: DashboardCritique | None = None

    for _attempt in range(max_repairs):
        if validation_report.status != "failed":
            break
        logger.info(
            "Repairing dashboard plan after validation failure: rejected_charts=%s rejected_kpis=%s",
            validation_report.rejected_chart_titles,
            validation_report.rejected_kpi_titles,
        )
        try:
            if critic_event_callback:
                critic_event_callback(
                    "start",
                    {
                        "message": "Repairing dashboard plan after validation failure.",
                        "rejected_chart_titles": validation_report.rejected_chart_titles,
                        "rejected_kpi_titles": validation_report.rejected_kpi_titles,
                    },
                )
            critique = repair_dashboard_plan(
                metadata=metadata,
                semantic_understanding=semantic_understanding,
                metric_plan=metric_plan,
                analysis_outputs=analysis_outputs,
                dashboard_plan=dashboard_plan,
                validation_report=validation_report,
                df_context=df_context,
            )
            critique = validate_contract(DashboardCritique, critique)
            dashboard_plan = validate_contract(DashboardPlan, critique.repaired_dashboard_plan)
            validation_report = validate_dashboard_plan(
                dashboard_plan=dashboard_plan,
                metric_plan=metric_plan,
                analysis_outputs=analysis_outputs,
            )
            validation_report = validate_contract(DashboardValidationReport, validation_report)
            if critic_event_callback:
                critic_event_callback(
                    "complete",
                    {
                        "message": "Dashboard critic repair completed.",
                        "validation_status": validation_report.status,
                    },
                )
        except Exception as exc:
            logger.exception("Dashboard critic repair failed; keeping original validated dashboard plan.")
            if critic_event_callback:
                critic_event_callback(
                    "warning",
                    {
                        "message": "Dashboard critic repair failed; kept original dashboard plan.",
                        "error": exc,
                    },
                )
            critique = None
            break

    return dashboard_plan, validation_report, critique
