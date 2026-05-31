from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contracts import DashboardCritique, DashboardPlan, DashboardValidationReport, PandasMetricPlan, SemanticUnderstanding
from core.dataset_metadata import build_dataframe_context, normalize_dataset_metadata
from core.pipeline import generate_validated_dashboard_plan


BENCHMARK_DIR = Path("artifacts") / "benchmarks" / "dashboard_models"
DashboardRunner = Callable[..., tuple[DashboardPlan, DashboardValidationReport, DashboardCritique | None]]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_semantic_understanding(path: Path) -> SemanticUnderstanding:
    return SemanticUnderstanding.model_validate_json(path.read_text(encoding="utf-8"))


def load_metric_plan(path: Path) -> PandasMetricPlan:
    return PandasMetricPlan.model_validate_json(path.read_text(encoding="utf-8"))


def deserialize_analysis_output(payload: dict[str, Any]) -> Any:
    kind = payload.get("kind")
    if kind == "table":
        return pd.DataFrame(payload.get("rows", []), columns=payload.get("columns") or None)
    if kind == "mapping":
        return payload.get("value", {})
    if kind == "scalar":
        return payload.get("value")
    return payload


def deserialize_analysis_outputs(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: deserialize_analysis_output(value) if isinstance(value, dict) else value
        for key, value in payload.items()
    }


@contextmanager
def dashboard_model_environment(model: str, timeout_seconds: float | None) -> Iterator[None]:
    keys = [
        "OPENAI_DASHBOARD_MODEL",
        "OPENAI_DASHBOARD_CRITIC_MODEL",
        "OPENAI_TIMEOUT_SECONDS",
    ]
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["OPENAI_DASHBOARD_MODEL"] = model
    os.environ["OPENAI_DASHBOARD_CRITIC_MODEL"] = model
    if timeout_seconds is not None:
        os.environ["OPENAI_TIMEOUT_SECONDS"] = str(timeout_seconds)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def chart_type_counts(plan: DashboardPlan) -> dict[str, int]:
    counts: dict[str, int] = {}
    charts = plan.overview_charts + [view.chart for view in plan.question_views]
    for chart in charts:
        counts[chart.chart_type] = counts.get(chart.chart_type, 0) + 1
    return counts


def validation_summary(report: DashboardValidationReport) -> dict[str, Any]:
    return {
        "status": report.status,
        "issue_count": len(report.issues),
        "error_count": sum(1 for issue in report.issues if issue.severity == "error"),
        "warning_count": sum(1 for issue in report.issues if issue.severity == "warning"),
        "rejected_charts": report.rejected_chart_titles,
        "rejected_kpis": report.rejected_kpi_titles,
        "issues": [issue.model_dump() for issue in report.issues],
    }


def dashboard_summary(plan: DashboardPlan, report: DashboardValidationReport, critique: DashboardCritique | None) -> dict[str, Any]:
    return {
        "title": plan.dashboard_title,
        "kpi_count": len(plan.kpis),
        "overview_chart_count": len(plan.overview_charts),
        "question_view_count": len(plan.question_views),
        "chart_type_counts": chart_type_counts(plan),
        "overview_charts": [
            {
                "title": chart.title,
                "type": chart.chart_type,
                "source_output_key": chart.source_output_key,
                "x": chart.x,
                "y": chart.y,
                "color": chart.color,
                "top_n": chart.top_n,
            }
            for chart in plan.overview_charts
        ],
        "question_views": [
            {
                "question": view.question,
                "chart_title": view.chart.title,
                "type": view.chart.chart_type,
                "source_output_key": view.chart.source_output_key,
            }
            for view in plan.question_views
        ],
        "validation": validation_summary(report),
        "critic_used": critique is not None,
    }


def run_single_model_benchmark(
    *,
    model: str,
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
    df_context: str,
    max_repairs: int,
    timeout_seconds: float | None,
    runner: DashboardRunner = generate_validated_dashboard_plan,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()
    result: dict[str, Any] = {
        "model": model,
        "status": "running",
        "started_at": started_at,
        "max_repairs": max_repairs,
        "timeout_seconds": timeout_seconds,
    }

    with dashboard_model_environment(model, timeout_seconds):
        try:
            dashboard_plan, validation_report, critique = runner(
                metadata=metadata,
                semantic_understanding=semantic_understanding,
                metric_plan=metric_plan,
                analysis_outputs=analysis_outputs,
                df_context=df_context,
                max_repairs=max_repairs,
            )
        except Exception as exc:
            result.update(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(limit=8),
                }
            )
        else:
            result.update(
                {
                    "status": "succeeded",
                    "dashboard": dashboard_summary(dashboard_plan, validation_report, critique),
                }
            )

    result.update(
        {
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.perf_counter() - start_time, 3),
        }
    )
    return result


def write_report(report: dict[str, Any], output_dir: Path = BENCHMARK_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    path = output_dir / f"{timestamp}_dashboard_model_benchmark.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def print_console_table(results: list[dict[str, Any]]) -> None:
    print("model,status,seconds,validation,errors,warnings,critic,kpis,overview,questions,error")
    for result in results:
        dashboard = result.get("dashboard", {})
        validation = dashboard.get("validation", {})
        print(
            ",".join(
                [
                    str(result.get("model", "")),
                    str(result.get("status", "")),
                    str(result.get("duration_seconds", "")),
                    str(validation.get("status", "")),
                    str(validation.get("error_count", 0)),
                    str(validation.get("warning_count", 0)),
                    str(dashboard.get("critic_used", "")),
                    str(dashboard.get("kpi_count", 0)),
                    str(dashboard.get("overview_chart_count", 0)),
                    str(dashboard.get("question_view_count", 0)),
                    str(result.get("error_type", "")),
                ]
            )
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark dashboard planning/validation across OpenAI models.")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--semantic", type=Path, required=True)
    parser.add_argument("--metric-plan", type=Path, required=True)
    parser.add_argument("--analysis-outputs", type=Path, required=True)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--max-repairs", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--output-dir", type=Path, default=BENCHMARK_DIR)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    metadata = normalize_dataset_metadata(read_json(args.metadata))
    df = pd.read_csv(args.csv)
    semantic_understanding = load_semantic_understanding(args.semantic)
    metric_plan = load_metric_plan(args.metric_plan)
    analysis_outputs = deserialize_analysis_outputs(read_json(args.analysis_outputs))
    df_context = build_dataframe_context(metadata, df)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "csv": str(args.csv),
        "metadata": str(args.metadata),
        "semantic": str(args.semantic),
        "metric_plan": str(args.metric_plan),
        "analysis_outputs": str(args.analysis_outputs),
        "models": args.models,
        "max_repairs": args.max_repairs,
        "timeout_seconds": args.timeout_seconds,
        "results": [],
    }

    for model in args.models:
        print(f"Running dashboard benchmark for {model}...", flush=True)
        report["results"].append(
            run_single_model_benchmark(
                model=model,
                metadata=metadata,
                semantic_understanding=semantic_understanding,
                metric_plan=metric_plan,
                analysis_outputs=analysis_outputs,
                df_context=df_context,
                max_repairs=args.max_repairs,
                timeout_seconds=args.timeout_seconds,
            )
        )
        print_console_table(report["results"])

    report_path = write_report(report, args.output_dir)
    print(f"Saved benchmark report: {report_path}")


if __name__ == "__main__":
    main()
