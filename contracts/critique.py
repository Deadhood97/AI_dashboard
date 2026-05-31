from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.base import schema_extra
from contracts.dashboard import DashboardPlan


class DashboardCritique(BaseModel):
    model_config = schema_extra("dashboard_critique")

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
