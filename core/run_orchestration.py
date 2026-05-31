from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from agents.analytical_brain import build_analytical_brain_input, generate_analytical_insights
from agents.semantic_understanding import generate_semantic_understanding
from core.dataset_metadata import build_dataframe_context
from core.metric_execution import generate_executable_metric_plan
from core.pipeline import generate_validated_dashboard_plan
from core.run_tracing import RunTraceEvent, RunTracer
from notebook_export import build_dashboard_notebook, write_dashboard_notebook


logger = logging.getLogger(__name__)


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
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return str(value)


def serialize_analysis_output(value: Any, max_rows: int = 200) -> dict[str, Any]:
    if isinstance(value, pd.DataFrame):
        frame = value.head(max_rows)
        return {
            "kind": "table",
            "type": "DataFrame",
            "columns": [str(column) for column in frame.columns],
            "rows": [
                {str(key): json_safe(cell) for key, cell in row.items()}
                for row in frame.to_dict(orient="records")
            ],
            "row_count": int(len(value)),
            "truncated": len(value) > max_rows,
        }
    if isinstance(value, pd.Series):
        frame = value.reset_index()
        frame.columns = [str(column) for column in frame.columns]
        return serialize_analysis_output(frame, max_rows=max_rows) | {"type": "Series"}
    if isinstance(value, dict):
        return {
            "kind": "mapping",
            "type": "dict",
            "value": {str(key): json_safe(cell) for key, cell in value.items()},
        }
    if isinstance(value, (list, tuple)):
        frame = pd.DataFrame(value)
        return serialize_analysis_output(frame, max_rows=max_rows)
    return {
        "kind": "scalar",
        "type": type(value).__name__,
        "value": json_safe(value),
    }


def serialize_analysis_outputs(analysis_outputs: dict[str, Any]) -> dict[str, Any]:
    return {
        key: serialize_analysis_output(value)
        for key, value in analysis_outputs.items()
    }


def write_model_json(path: Path, model: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    return path


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _artifact_paths(store: Any, metadata: dict[str, Any], *artifact_types: str) -> dict[str, str]:
    return {
        artifact_type: str(store.path_for(metadata, artifact_type))
        for artifact_type in artifact_types
    }


def run_dashboard_generation(
    store: Any,
    metadata: dict[str, Any],
    include_notebook: bool = True,
    stage_callback: Callable[[str], None] | None = None,
    *,
    run_id: str,
    job_id: str | None = None,
) -> Any:
    def set_stage(stage: str) -> None:
        if stage_callback:
            stage_callback(stage)

    tracer = RunTracer(store.path_for(metadata, "trace"), run_id=run_id, job_id=job_id)

    def required_event(stage: str, message: str = "") -> RunTraceEvent:
        set_stage(stage)
        return tracer.start_event(stage, message=message)

    try:
        event = required_event("dataset_context", "Loading dataset and building dataframe context.")
        dataset_path = store.path_for(metadata, "dataset")
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset artifact not found for run: {run_id}")
        df = pd.read_csv(dataset_path)
        df_context = build_dataframe_context(metadata, df)
        tracer.complete_event(
            event,
            "Dataset context prepared.",
            _artifact_paths(store, metadata, "dataset", "metadata"),
        )

        event = required_event("semantic", "Generating semantic understanding.")
        semantic = generate_semantic_understanding(metadata=metadata, df_head=df_context)
        write_model_json(store.path_for(metadata, "semantic"), semantic)
        tracer.complete_event(
            event,
            "Semantic understanding generated.",
            _artifact_paths(store, metadata, "semantic"),
        )

        event = required_event("metrics", "Generating and executing metric plan.")
        metric_plan, analysis_outputs = generate_executable_metric_plan(
            df=df,
            semantic_understanding=semantic,
            df_head=df_context,
            metadata=metadata,
        )
        metric_plan_path = write_model_json(store.path_for(metadata, "metric_plan"), metric_plan)
        analysis_outputs_path = write_json(
            store.path_for(metadata, "analysis_outputs"),
            serialize_analysis_outputs(analysis_outputs),
        )
        tracer.complete_event(
            event,
            "Metric plan executed.",
            {
                **_artifact_paths(store, metadata, "metric_plan", "analysis_outputs"),
                "metric_plan_path": str(metric_plan_path),
                "analysis_outputs_path": str(analysis_outputs_path),
            },
        )

        critic_event: RunTraceEvent | None = None

        def critic_event_callback(action: str, payload: dict[str, Any]) -> None:
            nonlocal critic_event
            if action == "start":
                critic_event = tracer.start_event("critic_repair", str(payload.get("message") or ""))
            elif action == "complete" and critic_event is not None:
                tracer.complete_event(critic_event, str(payload.get("message") or ""))
            elif action == "warning":
                if critic_event is None:
                    critic_event = tracer.start_event("critic_repair", str(payload.get("message") or ""))
                error = payload.get("error")
                tracer.warn_event(
                    critic_event,
                    str(payload.get("message") or ""),
                    error if isinstance(error, BaseException) else None,
                )

        event = required_event("dashboard", "Generating dashboard plan and validation report.")
        dashboard_plan, validation_report, critique = generate_validated_dashboard_plan(
            metadata=metadata,
            semantic_understanding=semantic,
            metric_plan=metric_plan,
            analysis_outputs=analysis_outputs,
            df_context=df_context,
            critic_event_callback=critic_event_callback,
        )
        dashboard_path = write_model_json(store.path_for(metadata, "dashboard"), dashboard_plan)
        validation_path = write_model_json(store.path_for(metadata, "validation"), validation_report)
        critique_path = write_model_json(store.path_for(metadata, "critique"), critique) if critique else None
        tracer.complete_event(
            event,
            "Dashboard plan and validation report generated.",
            {
                **_artifact_paths(store, metadata, "dashboard", "validation"),
                "dashboard_path": str(dashboard_path),
                "validation_path": str(validation_path),
                "critique_path": str(critique_path) if critique_path else "",
            },
        )
        if critic_event is None:
            tracer.skip_event("critic_repair", "Dashboard validation did not require critic repair.")

        set_stage("insights")
        event = tracer.start_event("insights", "Generating analytical insights.")
        insights = None
        insights_path = None
        try:
            analytical_input = build_analytical_brain_input(
                metadata=metadata,
                semantic_understanding=semantic,
                metric_plan=metric_plan,
                analysis_outputs=analysis_outputs,
                dashboard_plan=dashboard_plan,
                validation_report=validation_report,
                df_context=df_context,
            )
            insights = generate_analytical_insights(analytical_input)
            insights_path = write_model_json(store.path_for(metadata, "insights"), insights)
            tracer.complete_event(
                event,
                "Analytical insights generated.",
                _artifact_paths(store, metadata, "insights"),
            )
        except Exception as exc:
            logger.exception("Analytical insights generation failed for run: %s", run_id)
            tracer.warn_event(event, "Analytical insights generation failed.", exc)

        if include_notebook:
            set_stage("notebook")
            event = tracer.start_event("notebook", "Building notebook artifact.")
            try:
                notebook = build_dashboard_notebook(
                    metadata=metadata,
                    semantic_understanding=semantic,
                    metric_plan=metric_plan,
                    analysis_outputs=analysis_outputs,
                    dashboard_plan=dashboard_plan,
                    validation_report=validation_report,
                    critique=critique,
                    analytical_insights=insights,
                    df_preview=df.head(20),
                    artifact_paths={
                        "metadata": store.path_for(metadata, "metadata"),
                        "metric_plan": metric_plan_path,
                        "analysis_outputs": analysis_outputs_path,
                        "dashboard_plan": dashboard_path,
                        "validation_report": validation_path,
                        "critique": critique_path,
                        "analytical_insights": insights_path,
                    },
                )
                write_dashboard_notebook(store.path_for(metadata, "notebook"), notebook)
                tracer.complete_event(
                    event,
                    "Notebook artifact generated.",
                    _artifact_paths(store, metadata, "notebook"),
                )
            except Exception as exc:
                logger.exception("Notebook generation failed for run: %s", run_id)
                tracer.warn_event(event, "Notebook generation failed.", exc)
        else:
            tracer.skip_event("notebook", "Notebook generation was disabled for this job.")

        set_stage("complete")
        event = tracer.start_event("complete", "Run generation complete.")
        tracer.complete_event(event, "Dashboard artifacts generated.")
        tracer.finish("completed", "Dashboard artifacts generated.")
        return store.bundle_for(metadata)
    except Exception as exc:
        if "event" in locals() and isinstance(event, RunTraceEvent) and event.status == "running":
            tracer.fail_event(event, "Required stage failed.", exc)
        tracer.finish("failed", f"{type(exc).__name__}: {exc}")
        raise
