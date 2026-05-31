from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from contracts import (
    AnalyticalBrainResult,
    DashboardCritique,
    DashboardPlan,
    DashboardValidationReport,
    PandasMetricPlan,
    SemanticUnderstanding,
)
from notebook_export import build_dashboard_notebook, write_dashboard_notebook

from .config import (
    CRITIQUE_DIR,
    DASHBOARD_DIR,
    DATASET_DIR,
    INSIGHTS_DIR,
    LATEST_METADATA_PATH,
    METADATA_DIR,
    METADATA_INDEX_PATH,
    METRIC_PLAN_DIR,
    NOTEBOOK_DIR,
    SEMANTIC_DIR,
    TRACE_DIR,
)


def slugify_filename(filename: str) -> str:
    stem = Path(filename).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "dataset"


def dataset_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return DATASET_DIR / f"{dataset_slug}_{file_hash}.csv"


def save_uploaded_dataset(metadata: dict[str, Any], raw_bytes: bytes) -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    dataset_path = dataset_path_for(metadata)
    dataset_path.write_bytes(raw_bytes)
    return dataset_path


def metadata_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return METADATA_DIR / f"{dataset_slug}_{file_hash}.json"


def update_metadata_index(metadata_path: Path, metadata: dict[str, Any]) -> None:
    if METADATA_INDEX_PATH.exists():
        index = json.loads(METADATA_INDEX_PATH.read_text(encoding="utf-8"))
    else:
        index = []

    entry = {
        "source_file": metadata["source_file"],
        "metadata_file": str(metadata_path),
        "file_sha256": metadata["file_sha256"],
        "created_at": metadata["created_at"],
        "row_count": metadata["row_count"],
        "column_count": metadata["column_count"],
    }

    index = [
        existing
        for existing in index
        if not (
            existing.get("source_file") == entry["source_file"]
            and existing.get("file_sha256") == entry["file_sha256"]
        )
    ]
    index.append(entry)
    METADATA_INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def save_metadata(metadata: dict[str, Any]) -> Path:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = metadata_path_for(metadata)
    metadata_json = json.dumps(metadata, indent=2)

    metadata_path.write_text(metadata_json, encoding="utf-8")
    LATEST_METADATA_PATH.write_text(metadata_json, encoding="utf-8")
    update_metadata_index(metadata_path, metadata)

    return metadata_path


def semantic_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return SEMANTIC_DIR / f"{dataset_slug}_{file_hash}_semantic.json"


def save_semantic_understanding(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
) -> Path:
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)
    semantic_path = semantic_path_for(metadata)
    semantic_path.write_text(
        semantic_understanding.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return semantic_path


def metric_plan_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return METRIC_PLAN_DIR / f"{dataset_slug}_{file_hash}_metric_plan.json"


def save_metric_plan(metadata: dict[str, Any], metric_plan: PandasMetricPlan) -> Path:
    METRIC_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    metric_plan_path = metric_plan_path_for(metadata)
    metric_plan_path.write_text(
        metric_plan.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return metric_plan_path


def failed_metric_plan_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    suffix = uuid.uuid4().hex[:8]
    return METRIC_PLAN_DIR / f"{dataset_slug}_{file_hash}_failed_metric_plan_{timestamp}_{suffix}.json"


def save_failed_metric_plan(
    metadata: dict[str, Any],
    metric_plan: PandasMetricPlan,
    error_message: str,
    sanitized_code: str,
) -> Path:
    METRIC_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    failed_path = failed_metric_plan_path_for(metadata)
    payload = {
        "error_message": error_message,
        "sanitized_code": sanitized_code,
        "metric_plan": metric_plan.model_dump(),
    }
    failed_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return failed_path


def dashboard_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return DASHBOARD_DIR / f"{dataset_slug}_{file_hash}_dashboard.json"


def save_dashboard_plan(metadata: dict[str, Any], dashboard_plan: DashboardPlan) -> Path:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    dashboard_path = dashboard_path_for(metadata)
    dashboard_path.write_text(
        dashboard_plan.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return dashboard_path


def dashboard_validation_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return DASHBOARD_DIR / f"{dataset_slug}_{file_hash}_dashboard_validation.json"


def save_dashboard_validation_report(
    metadata: dict[str, Any],
    report: DashboardValidationReport,
) -> Path:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    report_path = dashboard_validation_path_for(metadata)
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report_path


def dashboard_critique_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return CRITIQUE_DIR / f"{dataset_slug}_{file_hash}_dashboard_critique.json"


def save_dashboard_critique(
    metadata: dict[str, Any],
    critique: DashboardCritique,
) -> Path:
    CRITIQUE_DIR.mkdir(parents=True, exist_ok=True)
    critique_path = dashboard_critique_path_for(metadata)
    critique_path.write_text(critique.model_dump_json(indent=2), encoding="utf-8")
    return critique_path


def insights_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return INSIGHTS_DIR / f"{dataset_slug}_{file_hash}_analytical_insights.json"


def save_analytical_insights(
    metadata: dict[str, Any],
    insights: AnalyticalBrainResult,
) -> Path:
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    insights_path = insights_path_for(metadata)
    insights_path.write_text(insights.model_dump_json(indent=2), encoding="utf-8")
    return insights_path


def notebook_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return NOTEBOOK_DIR / f"{dataset_slug}_{file_hash}_analysis_notebook.ipynb"


def trace_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return TRACE_DIR / f"{dataset_slug}_{file_hash}_trace.json"


def save_dashboard_notebook_artifact(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
    dashboard_plan: DashboardPlan,
    validation_report: DashboardValidationReport,
    critique: DashboardCritique | None,
    analytical_insights: AnalyticalBrainResult | None,
    df_preview: pd.DataFrame,
    artifact_paths: dict[str, Any],
) -> Path:
    notebook = build_dashboard_notebook(
        metadata=metadata,
        semantic_understanding=semantic_understanding,
        metric_plan=metric_plan,
        analysis_outputs=analysis_outputs,
        dashboard_plan=dashboard_plan,
        validation_report=validation_report,
        critique=critique,
        analytical_insights=analytical_insights,
        df_preview=df_preview,
        artifact_paths=artifact_paths,
    )
    return write_dashboard_notebook(notebook_path_for(metadata), notebook)
