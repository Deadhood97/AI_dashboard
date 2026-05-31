from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path("artifacts")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def optional_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json(path)


def artifact_paths(run_id: str, root: Path) -> dict[str, Path]:
    return {
        "semantic": root / "semantic" / f"{run_id}_semantic.json",
        "metric_plan": root / "metric_plans" / f"{run_id}_metric_plan.json",
        "analysis_outputs": root / "analysis_outputs" / f"{run_id}_analysis_outputs.json",
        "dashboard": root / "dashboard" / f"{run_id}_dashboard.json",
        "validation": root / "dashboard" / f"{run_id}_dashboard_validation.json",
        "critique": root / "critiques" / f"{run_id}_dashboard_critique.json",
        "insights": root / "insights" / f"{run_id}_analytical_insights.json",
        "notebook": root / "notebooks" / f"{run_id}_analysis_notebook.ipynb",
        "trace": root / "traces" / f"{run_id}_trace.json",
    }


def trace_summary(trace: dict[str, Any] | None) -> dict[str, Any]:
    if not trace:
        return {"present": False}
    events = trace.get("events", [])
    return {
        "present": True,
        "status": trace.get("status"),
        "duration_ms": trace.get("duration_ms"),
        "warnings": [
            {"stage": event.get("stage"), "message": event.get("message")}
            for event in events
            if event.get("status") == "warning"
        ],
        "failures": [
            {
                "stage": event.get("stage"),
                "message": event.get("message"),
                "error": event.get("error_message"),
            }
            for event in events
            if event.get("status") == "failed"
        ],
        "stage_durations_ms": {
            str(event.get("stage")): event.get("duration_ms")
            for event in events
            if event.get("duration_ms") is not None
        },
    }


def dashboard_summary(dashboard: dict[str, Any] | None) -> dict[str, Any]:
    if not dashboard:
        return {"present": False}
    return {
        "present": True,
        "title": dashboard.get("dashboard_title"),
        "kpi_count": len(dashboard.get("kpis", [])),
        "overview_chart_count": len(dashboard.get("overview_charts", [])),
        "question_view_count": len(dashboard.get("question_views", [])),
        "overview_chart_types": [
            chart.get("chart_type") for chart in dashboard.get("overview_charts", [])
        ],
        "question_chart_types": [
            view.get("chart", {}).get("chart_type")
            for view in dashboard.get("question_views", [])
        ],
    }


def validation_summary(validation: dict[str, Any] | None) -> dict[str, Any]:
    if not validation:
        return {"present": False}
    issues = validation.get("issues", [])
    return {
        "present": True,
        "status": validation.get("status"),
        "issue_count": len(issues),
        "error_count": sum(1 for issue in issues if issue.get("severity") == "error"),
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "rejected_charts": validation.get("rejected_chart_titles", []),
        "rejected_kpis": validation.get("rejected_kpi_titles", []),
    }


def metric_summary(run_id: str, root: Path, metric_plan: dict[str, Any] | None, outputs: dict[str, Any] | None) -> dict[str, Any]:
    failed_attempts = list((root / "metric_plans").glob(f"{run_id}_failed_metric_plan_*.json"))
    output_specs = metric_plan.get("analysis_outputs", []) if metric_plan else []
    return {
        "metric_plan_present": metric_plan is not None,
        "analysis_outputs_present": outputs is not None,
        "declared_output_count": len(output_specs),
        "produced_output_count": len(outputs or {}),
        "failed_attempt_count": len(failed_attempts),
    }


def run_summary(run_id: str, root: Path) -> dict[str, Any]:
    paths = artifact_paths(run_id, root)
    metric_plan = optional_json(paths["metric_plan"])
    outputs = optional_json(paths["analysis_outputs"])
    dashboard = optional_json(paths["dashboard"])
    validation = optional_json(paths["validation"])
    trace = optional_json(paths["trace"])
    return {
        "run_id": run_id,
        "artifacts": {name: path.exists() for name, path in paths.items()},
        "metrics": metric_summary(run_id, root, metric_plan, outputs),
        "dashboard": dashboard_summary(dashboard),
        "validation": validation_summary(validation),
        "trace": trace_summary(trace),
    }


def compare_runs(before_run_id: str, after_run_id: str, root: Path) -> dict[str, Any]:
    before = run_summary(before_run_id, root)
    after = run_summary(after_run_id, root)
    return {
        "before": before,
        "after": after,
        "delta": {
            "failed_metric_attempts": (
                after["metrics"]["failed_attempt_count"]
                - before["metrics"]["failed_attempt_count"]
            ),
            "validation_errors": (
                after["validation"].get("error_count", 0)
                - before["validation"].get("error_count", 0)
            ),
            "validation_warnings": (
                after["validation"].get("warning_count", 0)
                - before["validation"].get("warning_count", 0)
            ),
            "duration_ms": (
                (after["trace"].get("duration_ms") or 0)
                - (before["trace"].get("duration_ms") or 0)
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare dashboard run artifacts before and after model changes.")
    parser.add_argument("before_run_id")
    parser.add_argument("after_run_id")
    parser.add_argument("--artifact-root", type=Path, default=ARTIFACT_ROOT)
    args = parser.parse_args()

    print(json.dumps(compare_runs(args.before_run_id, args.after_run_id, args.artifact_root), indent=2))


if __name__ == "__main__":
    main()
