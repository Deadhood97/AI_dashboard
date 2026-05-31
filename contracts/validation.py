from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from contracts.base import schema_extra


IssueSeverity = Literal["info", "warning", "error"]
IssueComponent = Literal["metric_output", "kpi", "chart"]


class ValidationIssue(BaseModel):
    severity: IssueSeverity
    component: IssueComponent
    item_title: str
    source_output_key: str | None = None
    message: str
    suggested_fix: str


class DashboardValidationReport(BaseModel):
    model_config = schema_extra("dashboard_validation_report")

    status: Literal["passed", "passed_with_warnings", "failed"]
    issues: list[ValidationIssue] = Field(default_factory=list)
    rejected_chart_titles: list[str] = Field(default_factory=list)
    rejected_kpi_titles: list[str] = Field(default_factory=list)
