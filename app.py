from __future__ import annotations

import ast
import hashlib
import json
import logging
import shutil
import re
import tempfile
import textwrap
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from agents.dashboard_planner import (
    DashboardChartSpec,
    DashboardKpiSpec,
    DashboardPlan,
    generate_dashboard_plan,
)
from agents.dashboard_critic import DashboardCritique, repair_dashboard_plan
from agents.metric_code_planner import (
    PandasMetricPlan,
    generate_metric_code_plan,
    repair_metric_code_plan,
)
from agents.semantic_understanding import (
    SemanticUnderstanding,
    generate_semantic_understanding,
)
from dashboard_validation import (
    DashboardValidationReport,
    chart_is_rejected,
    kpi_is_rejected,
    validate_dashboard_plan,
)
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


METADATA_DIR = Path("artifacts") / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
METADATA_INDEX_PATH = METADATA_DIR / "metadata_index.json"
DATASET_DIR = Path("artifacts") / "datasets"
SEMANTIC_DIR = Path("artifacts") / "semantic"
METRIC_PLAN_DIR = Path("artifacts") / "metric_plans"
DASHBOARD_DIR = Path("artifacts") / "dashboard"
CRITIQUE_DIR = Path("artifacts") / "critiques"
LOG_DIR = Path("artifacts") / "logs"
APP_LOG_PATH = LOG_DIR / "app.log"
KAGGLE_DOWNLOAD_DIR = Path("artifacts") / "kaggle_downloads"
MAX_OVERVIEW_CHARTS = 2
MAX_QUESTION_VIEWS = 3
MAX_TABLE_ROWS = 25


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background: #f4f1ea;
            color: #1f1c18;
        }

        .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }

        [data-testid="stSidebar"] {
            background: #fbfaf7;
            border-right: 1px solid #ded8cb;
        }

        [data-testid="stSidebar"] * {
            color: #1f1c18;
        }

        [data-testid="stSidebar"] h3 {
            color: #1f1c18;
            font-size: 0.95rem;
            font-weight: 760;
            margin-top: 0.8rem;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #4d473f;
        }

        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] input {
            background: #ffffff;
            border: 1px solid #cfc8bb;
            color: #1f1c18;
        }

        [data-testid="stFileUploader"] section {
            background: #ffffff;
            border: 1px dashed #bdb5a7;
            border-radius: 8px;
            color: #1f1c18;
        }

        [data-testid="stFileUploader"] section button {
            color: #1f1c18;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        div.stButton > button {
            border-radius: 6px;
            border: 1px solid #b8b5aa;
            font-weight: 650;
            min-height: 2.4rem;
        }

        div.stButton > button[kind="primary"] {
            background: #0f766e;
            border-color: #0f766e;
            color: #ffffff;
        }

        div.stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            border-bottom: 1px solid #dedbd2;
            margin-top: 1.5rem;
        }

        div.stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 0.6rem 1rem;
            font-weight: 650;
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e3e0d7;
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }

        .app-kicker {
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
        }

        .app-title {
            color: #181612;
            font-size: 2.05rem;
            font-weight: 760;
            line-height: 1.08;
            margin: 0;
        }

        .app-subtitle {
            color: #5f5a50;
            font-size: 0.98rem;
            margin-top: 0.45rem;
            max-width: 760px;
        }

        .section-label {
            color: #6a6258;
            font-size: 0.8rem;
            font-weight: 750;
            letter-spacing: 0.06em;
            margin: 1rem 0 0.2rem;
            text-transform: uppercase;
        }

        .section-title {
            color: #1f1c18;
            font-size: 1.25rem;
            font-weight: 720;
            margin: 0 0 0.35rem;
        }

        .chart-title {
            color: #1f1c18;
            font-size: 1.02rem;
            font-weight: 720;
            margin: 0 0 0.25rem;
        }

        .muted-note {
            color: #6a6258;
            font-size: 0.9rem;
        }

        .empty-state {
            border: 1px solid #ded8cb;
            border-radius: 8px;
            padding: 1.5rem;
            background: #ffffff;
            margin-top: 1.25rem;
            max-width: 760px;
            box-shadow: 0 1px 2px rgba(30, 26, 18, 0.05);
        }

        .empty-eyebrow {
            color: #0f766e;
            font-size: 0.75rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .empty-title {
            color: #1f1c18;
            font-size: 1.4rem;
            font-weight: 760;
            margin: 0.35rem 0 0.35rem;
        }

        .empty-body {
            color: #5f5a50;
            font-size: 0.98rem;
            line-height: 1.5;
            max-width: 600px;
        }

        .workflow-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1.15rem;
        }

        .workflow-step {
            background: #f8f6f1;
            border: 1px solid #e2dccf;
            border-radius: 8px;
            padding: 0.85rem;
        }

        .workflow-step strong {
            color: #1f1c18;
            display: block;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }

        .workflow-step span {
            color: #6a6258;
            font-size: 0.82rem;
            line-height: 1.35;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-top: 3.4rem;
            }

            .app-title {
                font-size: 1.7rem;
            }

            .workflow-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header() -> None:
    st.markdown(
        """
        <h1 class="app-title">Dashboard Studio</h1>
        <div class="app-subtitle">
            Load a dataset, run the analysis agents, and review a validated dashboard with saved artifacts.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(label: str, title: str, body: str | None = None) -> None:
    st.markdown(
        f'<div class="section-label">{label}</div><h2 class="section-title">{title}</h2>',
        unsafe_allow_html=True,
    )
    if body:
        st.markdown(f'<div class="muted-note">{body}</div>', unsafe_allow_html=True)


def render_empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-eyebrow">Start here</div>
            <div class="empty-title">{title}</div>
            <div class="empty-body">{body}</div>
            <div class="workflow-grid">
                <div class="workflow-step">
                    <strong>1. Load data</strong>
                    <span>Upload a CSV or fetch one from Kaggle in the source panel.</span>
                </div>
                <div class="workflow-step">
                    <strong>2. Generate context</strong>
                    <span>Profile columns and run semantic understanding before dashboard planning.</span>
                </div>
                <div class="workflow-step">
                    <strong>3. Review output</strong>
                    <span>Inspect validated KPIs, charts, assumptions, and saved artifacts.</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_summary(metadata: dict[str, Any], parser_used: str) -> None:
    source = metadata.get("source", {})
    source_label = source.get("type", "upload")
    if source_label == "kaggle":
        source_label = f"Kaggle: {source.get('dataset_ref', 'dataset')}"
    else:
        source_label = "Uploaded CSV"

    cols = st.columns([1.2, 0.8, 0.8, 1.4])
    cols[0].metric("Rows", f"{metadata['row_count']:,}")
    cols[1].metric("Columns", f"{metadata['column_count']:,}")
    cols[2].metric("Source", source_label)
    cols[3].metric("Parser", parser_used.replace(" pandas ", " "))


def render_artifact_path(label: str, path: Any) -> None:
    if path:
        st.caption(f"{label}: `{path}`")


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("smart_dashboarding")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(APP_LOG_PATH, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)

    return logger


logger = configure_logging()


def read_csv_with_fallbacks(uploaded_file: Any) -> tuple[pd.DataFrame, str]:
    """Read an uploaded CSV with a strict first pass and safer fallbacks."""
    attempts = [
        {
            "label": "default pandas C parser",
            "options": {},
        },
        {
            "label": "python parser with inferred delimiter",
            "options": {"engine": "python", "sep": None},
        },
        {
            "label": "python parser skipping malformed rows",
            "options": {
                "engine": "python",
                "sep": None,
                "on_bad_lines": "skip",
            },
        },
    ]

    last_error: Exception | None = None

    for attempt in attempts:
        uploaded_file.seek(0)
        try:
            df = pd.read_csv(uploaded_file, **attempt["options"])
            return df, attempt["label"]
        except Exception as exc:
            last_error = exc
            logger.exception(
                "CSV read attempt failed: filename=%s parser=%s",
                uploaded_file.name,
                attempt["label"],
            )

    raise ValueError(
        "Could not parse the CSV after trying the default parser and safer "
        "fallback parsers. The file may have malformed rows, inconsistent "
        "columns, broken quoting, an unusual delimiter, or unsupported encoding."
    ) from last_error


def make_named_bytes_file(raw_bytes: bytes, filename: str) -> BytesIO:
    buffer = BytesIO(raw_bytes)
    buffer.name = filename
    return buffer


def normalize_kaggle_dataset_ref(value: str) -> str:
    dataset_ref = value.strip()
    if dataset_ref.startswith("https://www.kaggle.com/datasets/"):
        dataset_ref = dataset_ref.removeprefix("https://www.kaggle.com/datasets/")
    elif dataset_ref.startswith("http://www.kaggle.com/datasets/"):
        dataset_ref = dataset_ref.removeprefix("http://www.kaggle.com/datasets/")
    dataset_ref = dataset_ref.strip("/")
    parts = dataset_ref.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("Use a Kaggle dataset reference like `owner/dataset-slug`.")
    return "/".join(parts[:3])


def kaggle_download_folder(dataset_ref: str) -> Path:
    return KAGGLE_DOWNLOAD_DIR / slugify_filename(dataset_ref.replace("/", "_"))


def kaggle_api() -> Any:
    load_dotenv()
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise RuntimeError(
            "The `kaggle` package is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    api = KaggleApi()
    try:
        api.authenticate()
    except SystemExit as exc:
        raise RuntimeError(
            "Kaggle authentication is not configured. Run `kaggle auth login`, "
            "set `KAGGLE_API_TOKEN`, or set legacy `KAGGLE_USERNAME` and `KAGGLE_KEY`."
        ) from exc
    return api


def list_kaggle_files(api: Any, dataset_ref: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        response = api.dataset_list_files(
            dataset_ref,
            page_token=page_token,
            page_size=100,
        )
        if getattr(response, "error_message", None):
            raise RuntimeError(response.error_message)

        for dataset_file in getattr(response, "files", []) or []:
            files.append(
                {
                    "name": getattr(dataset_file, "name", ""),
                    "size": getattr(dataset_file, "total_bytes", None),
                    "creation_date": getattr(dataset_file, "creation_date", None),
                }
            )

        page_token = getattr(response, "next_page_token", None)
        if not page_token:
            return files


def choose_kaggle_csv_file(files: list[dict[str, Any]], requested_file: str) -> str:
    csv_files = [
        str(file_info["name"])
        for file_info in files
        if str(file_info.get("name", "")).lower().endswith(".csv")
    ]
    if requested_file:
        matching_file = next(
            (
                filename
                for filename in csv_files
                if filename == requested_file or Path(filename).name == requested_file
            ),
            None,
        )
        if not matching_file:
            raise ValueError(f"`{requested_file}` was not found as a CSV in this Kaggle dataset.")
        return matching_file

    if not csv_files:
        raise ValueError("This Kaggle dataset does not expose any CSV files.")
    return csv_files[0]


def kaggle_description_from_metadata(metadata: dict[str, Any], dataset_ref: str) -> str:
    title = str(metadata.get("title") or "").strip()
    subtitle = str(metadata.get("subtitle") or "").strip()
    description = str(metadata.get("description") or "").strip()
    licenses = metadata.get("licenses") or []
    license_names = [
        str(license_info.get("name", "")).strip()
        for license_info in licenses
        if isinstance(license_info, dict) and license_info.get("name")
    ]

    parts = [f"Kaggle dataset: {dataset_ref}"]
    if title:
        parts.append(f"Title: {title}")
    if subtitle:
        parts.append(f"Subtitle: {subtitle}")
    if description:
        parts.append(description)
    if license_names:
        parts.append(f"License: {', '.join(license_names)}")
    return "\n\n".join(parts)


def fetch_kaggle_dataset(dataset_ref_input: str, requested_file: str = "") -> dict[str, Any]:
    dataset_ref = normalize_kaggle_dataset_ref(dataset_ref_input)
    api = kaggle_api()
    files = list_kaggle_files(api, dataset_ref)
    selected_file = choose_kaggle_csv_file(files, requested_file.strip())

    download_dir = kaggle_download_folder(dataset_ref)
    if download_dir.exists():
        shutil.rmtree(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as metadata_temp_dir:
        metadata_path = Path(api.dataset_metadata(dataset_ref, metadata_temp_dir))
        kaggle_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    api.dataset_download_file(
        dataset_ref,
        selected_file,
        path=str(download_dir),
        force=True,
        quiet=True,
    )

    downloaded_files = [path for path in download_dir.rglob("*") if path.is_file()]
    selected_path = next(
        (
            path
            for path in downloaded_files
            if path.name == Path(selected_file).name or str(path.relative_to(download_dir)) == selected_file
        ),
        None,
    )
    if selected_path is None:
        csv_files = [path for path in downloaded_files if path.suffix.lower() == ".csv"]
        selected_path = csv_files[0] if csv_files else None
    if selected_path is None:
        raise FileNotFoundError(f"Kaggle download completed, but `{selected_file}` was not found.")

    raw_bytes = selected_path.read_bytes()
    source_filename = f"kaggle_{dataset_ref.replace('/', '_')}_{Path(selected_file).name}"
    return {
        "dataset_ref": dataset_ref,
        "selected_file": selected_file,
        "filename": source_filename,
        "raw_bytes": raw_bytes,
        "description": kaggle_description_from_metadata(kaggle_metadata, dataset_ref),
        "files": files,
        "download_path": selected_path,
    }


def clear_dataset_session_state() -> None:
    for key in [
        "dataset_df",
        "dataset_metadata",
        "metadata_path",
        "dataset_path",
        "parser_used",
        "semantic_understanding",
        "semantic_understanding_key",
        "semantic_understanding_path",
        "metric_plan",
        "metric_plan_key",
        "metric_plan_path",
        "analysis_outputs",
        "dashboard_plan",
        "dashboard_plan_key",
        "dashboard_plan_path",
        "dashboard_validation_report",
        "dashboard_validation_path",
        "dashboard_critique",
        "dashboard_critique_path",
    ]:
        st.session_state.pop(key, None)
    st.session_state["submitted_dataset_key"] = None


def infer_column_role(series: pd.Series) -> str:
    """Return a simple analytical role for a dataframe column."""
    if is_datetime64_any_dtype(series):
        return "temporal"
    if is_bool_dtype(series):
        return "boolean"
    if is_numeric_dtype(series):
        return "numeric"

    unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
    if unique_ratio <= 0.2:
        return "categorical"
    return "text"


def json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def analyze_columns(df: pd.DataFrame) -> list[dict[str, Any]]:
    metadata: list[dict[str, Any]] = []

    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        unique_values = non_null.drop_duplicates()
        column_info: dict[str, Any] = {
            "name": str(column),
            "pandas_dtype": str(series.dtype),
            "inferred_role": infer_column_role(series),
            "row_count": int(len(series)),
            "null_count": int(series.isna().sum()),
            "null_percentage": round(float(series.isna().mean() * 100), 2),
            "unique_count": int(series.nunique(dropna=True)),
            "sample_values": [json_safe(value) for value in non_null.head(5).tolist()],
        }

        if is_numeric_dtype(series) and not is_bool_dtype(series):
            column_info["statistics"] = {
                "min": json_safe(series.min()),
                "max": json_safe(series.max()),
                "mean": json_safe(series.mean()),
                "median": json_safe(series.median()),
            }
        elif is_datetime64_any_dtype(series):
            column_info["statistics"] = {
                "min": json_safe(series.min()),
                "max": json_safe(series.max()),
            }
        else:
            value_counts = non_null.astype(str).value_counts().head(12)
            column_info["top_values"] = [
                {"value": json_safe(index), "count": int(count)}
                for index, count in value_counts.items()
            ]

            if len(unique_values) <= 500:
                sorted_values = sorted(str(value) for value in unique_values.tolist())
                column_info["unique_values"] = sorted_values
            else:
                sorted_values = sorted(str(value) for value in unique_values.tolist())
                step = max(len(sorted_values) // 40, 1)
                column_info["representative_values"] = sorted_values[::step][:40]

        metadata.append(column_info)

    return metadata


def build_dataset_metadata(
    df: pd.DataFrame,
    filename: str,
    raw_bytes: bytes,
    dataset_description: str,
) -> dict[str, Any]:
    columns = analyze_columns(df)

    return {
        "source_file": filename,
        "file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_description": dataset_description,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": columns,
        "schema": {
            "description": dataset_description,
            "columns": columns,
        },
    }


def dataset_path_for(metadata: dict[str, Any]) -> Path:
    file_hash = str(metadata["file_sha256"])[:12]
    dataset_slug = slugify_filename(str(metadata["source_file"]))
    return DATASET_DIR / f"{dataset_slug}_{file_hash}.csv"


def save_uploaded_dataset(metadata: dict[str, Any], raw_bytes: bytes) -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    dataset_path = dataset_path_for(metadata)
    dataset_path.write_bytes(raw_bytes)
    return dataset_path


def build_dataframe_context(metadata: dict[str, Any], df: pd.DataFrame, rows: int = 8) -> str:
    context = {
        "source_file": metadata["source_file"],
        "row_count": metadata["row_count"],
        "column_count": metadata["column_count"],
        "dataset_description": metadata.get("dataset_description", ""),
        "columns": metadata["columns"],
    }
    return (
        "Dataset context JSON:\n"
        f"{json.dumps(context, indent=2)}\n\n"
        f"First {rows} dataframe rows:\n{df.head(rows).to_markdown(index=False)}"
    )


def slugify_filename(filename: str) -> str:
    stem = Path(filename).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "dataset"


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


def data_integrity_summary(df: pd.DataFrame) -> dict[str, Any]:
    total_cells = int(df.shape[0] * df.shape[1])
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    missing_percentage = round((missing_cells / total_cells) * 100, 2) if total_cells else 0
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_cells": missing_cells,
        "missing_percentage": missing_percentage,
        "duplicate_rows": duplicate_rows,
    }


def sanitize_generated_code(code: str) -> str:
    allowed_imports = {"import pandas as pd", "import numpy as np"}
    cleaned_code = textwrap.dedent(code).strip()
    if cleaned_code.startswith("```"):
        cleaned_lines = cleaned_code.splitlines()
        if cleaned_lines and cleaned_lines[0].strip().startswith("```"):
            cleaned_lines = cleaned_lines[1:]
        if cleaned_lines and cleaned_lines[-1].strip() == "```":
            cleaned_lines = cleaned_lines[:-1]
        cleaned_code = "\n".join(cleaned_lines)
    cleaned_code = textwrap.dedent(cleaned_code).strip()

    lines = []
    for line in cleaned_code.splitlines():
        if line.strip() in allowed_imports:
            continue
        lines.append(line)
    cleaned_code = "\n".join(lines)

    try:
        ast.parse(cleaned_code)
    except IndentationError:
        normalized_lines: list[str] = []
        previous_significant = ""
        for line in cleaned_code.splitlines():
            if line.startswith((" ", "\t")) and not previous_significant.endswith(":"):
                normalized_lines.append(line.lstrip())
            else:
                normalized_lines.append(line)
            if line.strip():
                previous_significant = line.rstrip()
        cleaned_code = "\n".join(normalized_lines)

    return cleaned_code


def validate_generated_code(code: str) -> None:
    tree = ast.parse(code)
    blocked_names = {"open", "exec", "eval", "compile", "__import__", "input"}
    blocked_roots = {"os", "sys", "subprocess", "socket", "requests", "pathlib", "shutil"}

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Generated code may not import modules.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in blocked_names:
                raise ValueError(f"Generated code may not call {node.func.id}.")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise ValueError("Generated code may not access dunder attributes.")
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and root.id in blocked_roots:
                raise ValueError(f"Generated code may not access {root.id}.")


def execute_metric_plan(df: pd.DataFrame, metric_plan: PandasMetricPlan) -> dict[str, Any]:
    code = sanitize_generated_code(metric_plan.pandas_code)
    validate_generated_code(code)
    safe_builtins = {
        "ValueError": ValueError,
        "TypeError": TypeError,
        "Exception": Exception,
        "len": len,
        "range": range,
        "sorted": sorted,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "enumerate": enumerate,
    }
    globals_dict = {"__builtins__": safe_builtins, "pd": pd, "np": np}
    locals_dict: dict[str, Any] = {"df": df.copy()}
    exec(compile(code, "<metric_plan>", "exec"), globals_dict, locals_dict)
    analysis_outputs = locals_dict.get("analysis_outputs")
    if not isinstance(analysis_outputs, dict):
        raise ValueError("Metric plan code must create analysis_outputs as a dictionary.")
    return analysis_outputs


def generate_executable_metric_plan(
    df: pd.DataFrame,
    semantic_understanding: SemanticUnderstanding,
    df_head: str,
    max_repairs: int = 1,
) -> tuple[PandasMetricPlan, dict[str, Any]]:
    metric_plan = generate_metric_code_plan(
        semantic_understanding=semantic_understanding,
        df_head=df_head,
    )
    for attempt in range(max_repairs + 1):
        try:
            return metric_plan, execute_metric_plan(df, metric_plan)
        except Exception as exc:
            if attempt >= max_repairs:
                raise
            logger.info("Repairing metric plan after execution failure: %s", exc)
            metric_plan = repair_metric_code_plan(
                failed_plan=metric_plan,
                semantic_understanding=semantic_understanding,
                df_head=df_head,
                error_message=f"{type(exc).__name__}: {exc}",
            )

    raise RuntimeError("Metric plan repair loop exited unexpectedly.")


def generate_validated_dashboard_plan(
    metadata: dict[str, Any],
    semantic_understanding: SemanticUnderstanding,
    metric_plan: PandasMetricPlan,
    analysis_outputs: dict[str, Any],
    df_context: str,
    max_repairs: int = 1,
) -> tuple[DashboardPlan, DashboardValidationReport, DashboardCritique | None]:
    dashboard_plan = generate_dashboard_plan(
        metadata=metadata,
        semantic_understanding=semantic_understanding,
        metric_plan=metric_plan,
        df_head=df_context,
    )
    validation_report = validate_dashboard_plan(
        dashboard_plan=dashboard_plan,
        metric_plan=metric_plan,
        analysis_outputs=analysis_outputs,
    )
    critique: DashboardCritique | None = None

    for attempt in range(max_repairs):
        if validation_report.status != "failed":
            break
        logger.info(
            "Repairing dashboard plan after validation failure: rejected_charts=%s rejected_kpis=%s",
            validation_report.rejected_chart_titles,
            validation_report.rejected_kpi_titles,
        )
        critique = repair_dashboard_plan(
            metadata=metadata,
            semantic_understanding=semantic_understanding,
            metric_plan=metric_plan,
            dashboard_plan=dashboard_plan,
            validation_report=validation_report,
            df_context=df_context,
        )
        dashboard_plan = critique.repaired_dashboard_plan
        validation_report = validate_dashboard_plan(
            dashboard_plan=dashboard_plan,
            metric_plan=metric_plan,
            analysis_outputs=analysis_outputs,
        )

    return dashboard_plan, validation_report, critique


def output_to_dataframe(output: Any) -> pd.DataFrame:
    if isinstance(output, pd.DataFrame):
        return output.copy()
    if isinstance(output, pd.Series):
        return output.reset_index()
    if isinstance(output, dict):
        return pd.DataFrame([output])
    if isinstance(output, (list, tuple)):
        return pd.DataFrame(output)
    return pd.DataFrame({"value": [output]})


def format_value(value: Any) -> str:
    if pd.isna(value):
        return "N/A"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.2f}"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    return str(value)


def render_data_integrity(df: pd.DataFrame, plan: DashboardPlan) -> None:
    render_section_heading("Quality", "Dataset Health")
    summary = data_integrity_summary(df)
    cols = st.columns(5)
    cols[0].metric("Rows", f"{summary['row_count']:,}")
    cols[1].metric("Columns", f"{summary['column_count']:,}")
    cols[2].metric("Missing Cells", f"{summary['missing_cells']:,}")
    cols[3].metric("Missing %", f"{summary['missing_percentage']}%")
    cols[4].metric("Duplicate Rows", f"{summary['duplicate_rows']:,}")

    null_summary = (
        df.isna()
        .sum()
        .reset_index()
        .rename(columns={"index": "column", 0: "missing_values"})
    )
    null_summary = null_summary[null_summary["missing_values"] > 0]
    if not null_summary.empty:
        st.dataframe(null_summary, use_container_width=True, hide_index=True)
    for note in plan.data_integrity_notes:
        st.caption(note)


def calculate_kpi(analysis_outputs: dict[str, Any], spec: DashboardKpiSpec) -> str:
    if spec.source_output_key not in analysis_outputs:
        return "Missing output"
    output = analysis_outputs[spec.source_output_key]
    if isinstance(output, (int, float, str, np.integer, np.floating)):
        return format_value(output)
    if isinstance(output, dict):
        if spec.value_column and spec.value_column in output:
            return format_value(output[spec.value_column])
        numeric_values = [value for value in output.values() if isinstance(value, (int, float, np.integer, np.floating))]
        return format_value(numeric_values[0]) if numeric_values else str(output)

    table = output_to_dataframe(output)
    if table.empty:
        return "N/A"
    if spec.value_column and spec.value_column in table.columns:
        series = table[spec.value_column]
    else:
        numeric_columns = table.select_dtypes(include="number").columns
        series = table[numeric_columns[0]] if len(numeric_columns) else table.iloc[:, -1]

    wants_latest = "latest" in f"{spec.title} {spec.rationale}".lower()
    temporal_columns = [
        column
        for column in table.columns
        if str(column).lower() in {"year", "date", "time", "month", "quarter"}
    ]
    if wants_latest and spec.value_column and temporal_columns:
        sorted_table = table.copy()
        sorted_table[temporal_columns[0]] = pd.to_numeric(
            sorted_table[temporal_columns[0]],
            errors="ignore",
        )
        sorted_table = sorted_table.sort_values(temporal_columns[0])
        latest_value = sorted_table[spec.value_column].dropna()
        if not latest_value.empty:
            return format_value(latest_value.iloc[-1])

    if spec.aggregation in {"sum", "mean", "median", "min", "max"}:
        series = pd.to_numeric(series, errors="coerce")
    aggregation = spec.aggregation or "count"
    aggregations = {
        "sum": series.sum,
        "mean": series.mean,
        "median": series.median,
        "count": series.count,
        "nunique": series.nunique,
        "min": series.min,
        "max": series.max,
    }
    return format_value(aggregations[aggregation]())


def render_kpis(
    analysis_outputs: dict[str, Any],
    plan: DashboardPlan,
    validation_report: DashboardValidationReport | None = None,
) -> None:
    render_section_heading("Summary", "Key Measures")
    if not plan.kpis:
        st.info("No KPI cards were selected by the dashboard planner.")
        return

    valid_kpis = [
        spec for spec in plan.kpis if not kpi_is_rejected(validation_report, spec.title)
    ]
    rejected_count = len(plan.kpis) - len(valid_kpis)
    if rejected_count:
        st.warning(f"{rejected_count} KPI card(s) were hidden by validation.")
    if not valid_kpis:
        st.info("No KPI cards passed validation.")
        return

    cols = st.columns(min(len(valid_kpis), 4))
    for index, spec in enumerate(valid_kpis):
        with cols[index % len(cols)]:
            st.metric(spec.title, calculate_kpi(analysis_outputs, spec))
            st.caption(spec.rationale)


def metric_columns_for_spec(chart_data: pd.DataFrame, spec: DashboardChartSpec) -> list[str]:
    columns: list[str] = []
    if spec.y and spec.y in chart_data.columns:
        columns.append(spec.y)
    columns.extend(metric for metric in spec.metrics if metric in chart_data.columns)
    return list(dict.fromkeys(columns))


def limit_chart_data(chart_data: pd.DataFrame, spec: DashboardChartSpec) -> pd.DataFrame:
    if chart_data.empty:
        return chart_data

    if spec.chart_type == "table":
        table_limit = min(spec.top_n or MAX_TABLE_ROWS, MAX_TABLE_ROWS)
        sort_by = spec.sort_by
        if sort_by and sort_by in chart_data.columns:
            ascending = spec.sort_order == "ascending"
            return chart_data.sort_values(sort_by, ascending=ascending).head(table_limit)
        return chart_data.head(table_limit)

    if not spec.top_n:
        return chart_data

    x = spec.x or spec.dimension
    y_columns = metric_columns_for_spec(chart_data, spec)
    entity_column = spec.color if spec.color in chart_data.columns else None

    if spec.chart_type == "scatter":
        if len(chart_data) <= spec.top_n:
            return chart_data
        sort_columns = [
            column
            for column in [x, y_columns[0] if y_columns else None, entity_column]
            if column and column in chart_data.columns
        ]
        sampled_data = chart_data.sort_values(sort_columns) if sort_columns else chart_data
        positions = np.linspace(0, len(sampled_data) - 1, spec.top_n, dtype=int)
        return sampled_data.iloc[sorted(set(positions))]

    if entity_column and y_columns:
        ranking_data = chart_data.copy()
        if x and x in ranking_data.columns:
            latest_x = ranking_data.groupby(entity_column, dropna=True)[x].transform("max")
            ranking_data = ranking_data[ranking_data[x] == latest_x]
        ranking_series = (
            ranking_data.groupby(entity_column, dropna=True)[y_columns[0]]
            .mean(numeric_only=True)
            .sort_values(ascending=False)
        )
        keep_entities = ranking_series.head(spec.top_n).index
        return chart_data[chart_data[entity_column].isin(keep_entities)]

    if x and x in chart_data.columns and y_columns:
        ascending = spec.sort_order == "ascending"
        return chart_data.sort_values(y_columns[0], ascending=ascending).head(spec.top_n)

    return chart_data.head(spec.top_n)


def sorted_chart_data(chart_data: pd.DataFrame, spec: DashboardChartSpec) -> pd.DataFrame:
    if chart_data.empty:
        return chart_data
    chart_data = limit_chart_data(chart_data, spec)
    sort_by = spec.sort_by or spec.x or spec.dimension
    if sort_by and sort_by in chart_data.columns:
        ascending = spec.sort_order == "ascending"
        chart_data = chart_data.sort_values(sort_by, ascending=ascending)
    return chart_data


def chart_key(spec: DashboardChartSpec) -> str:
    raw_key = f"{spec.title}-{spec.source_output_key}-{spec.chart_type}"
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", raw_key).strip("-").lower()


def render_text_output(output: Any) -> None:
    if isinstance(output, dict):
        cols = st.columns(min(len(output), 4) or 1)
        for index, (key, value) in enumerate(output.items()):
            with cols[index % len(cols)]:
                label = str(key).replace("_", " ").title()
                st.metric(label, format_value(value))
        return
    if isinstance(output, (int, float, str, np.integer, np.floating)):
        st.write(format_value(output))
        return
    table = output_to_dataframe(output)
    if table.empty:
        st.info("No text summary was produced.")
    else:
        st.dataframe(table.head(10), use_container_width=True, hide_index=True)


def render_chart(
    analysis_outputs: dict[str, Any],
    spec: DashboardChartSpec,
    validation_report: DashboardValidationReport | None = None,
) -> None:
    chart_container = st.container(border=True)
    with chart_container:
        st.markdown(f'<div class="chart-title">{spec.title}</div>', unsafe_allow_html=True)
        st.caption(spec.rationale)
    if chart_is_rejected(validation_report, spec.title):
        with chart_container:
            st.warning("Hidden by validation.")
            if validation_report:
                for issue in validation_report.issues:
                    if issue.component == "chart" and issue.item_title == spec.title:
                        st.caption(f"{issue.severity.upper()}: {issue.message}")
                        st.caption(f"Suggested fix: {issue.suggested_fix}")
        return

    if spec.source_output_key not in analysis_outputs:
        with chart_container:
            st.warning(f"Missing analysis output: {spec.source_output_key}")
        return

    output = analysis_outputs[spec.source_output_key]
    if spec.chart_type in {"text", "kpi"}:
        with chart_container:
            render_text_output(output)
        return

    chart_data = sorted_chart_data(output_to_dataframe(output), spec)

    try:
        x = spec.x or spec.dimension
        y = spec.y or spec.metric
        if spec.chart_type == "bar" and x in chart_data.columns and y in chart_data.columns:
            if spec.orientation == "horizontal":
                fig = px.bar(chart_data, x=y, y=x, orientation="h")
            else:
                fig = px.bar(chart_data, x=x, y=y, color=spec.color if spec.color in chart_data.columns else None)
            fig.update_layout(margin=dict(l=8, r=8, t=12, b=8), legend_title_text="")
            with chart_container:
                st.plotly_chart(fig, use_container_width=True, key=chart_key(spec))
        elif spec.chart_type in {"line", "multi_line"} and x in chart_data.columns:
            y_value: str | list[str] | None = y if y in chart_data.columns else None
            if not y_value and spec.metrics:
                y_value = [metric for metric in spec.metrics if metric in chart_data.columns]
            if not y_value:
                with chart_container:
                    st.dataframe(chart_data, use_container_width=True)
                return
            fig = px.line(
                chart_data,
                x=x,
                y=y_value,
                color=spec.color if spec.color in chart_data.columns else None,
                markers=True,
            )
            fig.update_layout(margin=dict(l=8, r=8, t=12, b=8), legend_title_text="")
            with chart_container:
                st.plotly_chart(fig, use_container_width=True, key=chart_key(spec))
        elif spec.chart_type == "histogram" and y in chart_data.columns:
            fig = px.histogram(chart_data, x=y)
            fig.update_layout(margin=dict(l=8, r=8, t=12, b=8))
            with chart_container:
                st.plotly_chart(fig, use_container_width=True, key=chart_key(spec))
        elif spec.chart_type == "scatter" and x in chart_data.columns and y in chart_data.columns:
            fig = px.scatter(
                chart_data,
                x=x,
                y=y,
                color=spec.color if spec.color in chart_data.columns else None,
            )
            fig.update_layout(margin=dict(l=8, r=8, t=12, b=8), legend_title_text="")
            with chart_container:
                st.plotly_chart(fig, use_container_width=True, key=chart_key(spec))
        elif spec.chart_type == "table":
            with chart_container:
                st.dataframe(chart_data, use_container_width=True, hide_index=True)
        else:
            with chart_container:
                st.warning("Showing table fallback.")
                st.dataframe(chart_data, use_container_width=True, hide_index=True)
    except Exception as exc:
        logger.exception("Dashboard chart render failed: title=%s", spec.title)
        with chart_container:
            st.warning(f"Could not render this chart: {exc}")
            st.dataframe(chart_data, use_container_width=True, hide_index=True)


def render_validation_report(report: DashboardValidationReport | None) -> None:
    if report is None:
        return

    if report.status == "passed":
        st.success("Validation passed.")
    elif report.status == "passed_with_warnings":
        st.warning("Validation passed with warnings.")
    else:
        st.error("Validation failed. Invalid components are hidden.")

    if report.issues:
        with st.expander("Dashboard validation report"):
            issue_rows = [issue.model_dump() for issue in report.issues]
            st.dataframe(pd.DataFrame(issue_rows), use_container_width=True, hide_index=True)


def render_dashboard_critique(critique: DashboardCritique | None) -> None:
    if critique is None:
        return

    with st.expander("Dashboard critic repair notes"):
        st.write(critique.critique_summary)
        render_list("Repair notes", critique.repair_notes)
        render_list("Remaining risks", critique.remaining_risks)


def render_dashboard(
    df: pd.DataFrame,
    plan: DashboardPlan,
    analysis_outputs: dict[str, Any],
    validation_report: DashboardValidationReport | None = None,
    critique: DashboardCritique | None = None,
) -> None:
    render_section_heading("Dashboard", plan.dashboard_title, plan.dashboard_summary)
    render_validation_report(validation_report)
    render_dashboard_critique(critique)
    render_data_integrity(df, plan)
    render_kpis(analysis_outputs, plan, validation_report)

    render_section_heading("Charts", "Overview")
    overview_charts = plan.overview_charts[:MAX_OVERVIEW_CHARTS]
    hidden_overview_count = max(len(plan.overview_charts) - len(overview_charts), 0)
    if hidden_overview_count:
        st.caption(f"{hidden_overview_count} lower-priority overview chart(s) were omitted for readability.")
    for chart in overview_charts:
        render_chart(analysis_outputs, chart, validation_report)

    render_section_heading("Analysis", "Question Views")
    chart_priority = {"bar": 0, "line": 0, "multi_line": 0, "scatter": 1, "histogram": 1, "text": 2, "kpi": 2, "table": 3}
    visible_question_views = sorted(
        plan.question_views,
        key=lambda view: chart_priority.get(view.chart.chart_type, 4),
    )[:MAX_QUESTION_VIEWS]
    hidden_question_count = max(len(plan.question_views) - len(visible_question_views), 0)
    if hidden_question_count:
        st.caption(f"{hidden_question_count} lower-priority question view(s) were omitted for readability.")
    for view in visible_question_views:
        st.markdown(f"**{view.question}**")
        st.caption(view.answer_strategy)
        render_chart(analysis_outputs, view.chart, validation_report)

    with st.expander("Dashboard assumptions and limitations"):
        render_list("Assumptions", plan.assumptions)
        render_list("Limitations", plan.limitations)


def render_list(label: str, values: list[str]) -> None:
    st.markdown(f"**{label}**")
    if values:
        for value in values:
            st.write(f"- {value}")
    else:
        st.caption("No values identified.")


def render_semantic_understanding(result: SemanticUnderstanding) -> None:
    render_section_heading("Understanding", result.dataset_domain)

    left, right = st.columns(2)
    with left:
        render_list("Primary entities", result.primary_entities)
        render_list("Important dimensions", result.important_dimensions)
        render_list("Important metrics", result.important_metrics)
    with right:
        render_list("Analytical goals", result.analytical_goals)
        render_list("Suggested questions", result.suggested_questions)


def main() -> None:
    st.set_page_config(page_title="Smart AI Dashboarding", layout="wide")
    inject_global_styles()

    render_page_header()

    if "submitted_dataset_key" not in st.session_state:
        st.session_state["submitted_dataset_key"] = None

    source_filename = ""
    raw_bytes = b""
    cleaned_description = ""
    empty_state: tuple[str, str] | None = None

    with st.sidebar:
        st.markdown("### Source")
        data_source = st.radio(
            "Data source",
            ["Upload CSV", "Kaggle dataset"],
            horizontal=False,
        )

        if data_source == "Upload CSV":
            dataset_description = st.text_area(
                "Dataset description",
                placeholder="Optional business context or domain notes.",
                help="Stored in the dataset schema for the semantic agent.",
            )
            uploaded_file = st.file_uploader("CSV file", type=["csv"])

            if uploaded_file is None:
                empty_state = (
                    "No dataset loaded",
                    "Select a CSV file in the source panel. On small screens, open the panel from the top-left control.",
                )
            else:
                raw_bytes = uploaded_file.getvalue()
                source_filename = uploaded_file.name
                cleaned_description = dataset_description.strip()
                csv_file = uploaded_file

        else:
            kaggle_ref = st.text_input(
                "Kaggle dataset",
                placeholder="owner/dataset-slug",
                help="A Kaggle dataset slug or dataset URL.",
            )
            kaggle_file = st.text_input(
                "CSV file name",
                placeholder="Optional",
            )

            if st.button("Fetch from Kaggle", type="primary", use_container_width=True):
                try:
                    with st.spinner("Fetching dataset..."):
                        st.session_state["kaggle_import"] = fetch_kaggle_dataset(
                            kaggle_ref,
                            kaggle_file,
                        )
                except Exception as exc:
                    logger.exception(
                        "Kaggle import failed: dataset_ref=%s requested_file=%s",
                        kaggle_ref,
                        kaggle_file,
                    )
                    st.error(f"Could not import from Kaggle: {exc}")
                    st.caption(f"Log: `{APP_LOG_PATH}`")

            kaggle_import = st.session_state.get("kaggle_import")
            if not kaggle_import:
                empty_state = (
                    "No dataset loaded",
                    "Enter a Kaggle dataset reference in the source panel. On small screens, open the panel from the top-left control.",
                )
            else:
                source_filename = kaggle_import["filename"]
                raw_bytes = kaggle_import["raw_bytes"]
                csv_file = make_named_bytes_file(raw_bytes, source_filename)
                kaggle_description = kaggle_import["description"]
                kaggle_notes = st.text_area(
                    "Additional notes",
                    placeholder="Optional context not captured by Kaggle metadata.",
                    help="Appended to the Kaggle metadata before analysis.",
                )
                cleaned_description = kaggle_description
                if kaggle_notes.strip():
                    cleaned_description = f"{kaggle_description}\n\nUser notes:\n{kaggle_notes.strip()}"

                st.caption(f"`{kaggle_import['selected_file']}`")

    if empty_state:
        render_empty_state(*empty_state)
        return

    dataset_key = (
        f"{data_source}:{source_filename}:"
        f"{hashlib.sha256(raw_bytes).hexdigest()}:"
        f"{hashlib.sha256(cleaned_description.encode('utf-8')).hexdigest()}"
    )

    if st.session_state.get("submitted_dataset_key") != dataset_key:
        clear_dataset_session_state()

    dataset_already_submitted = st.session_state.get("submitted_dataset_key") == dataset_key
    with st.sidebar:
        st.markdown("### Run")
        submit_clicked = st.button("Prepare dataset", type="primary", use_container_width=True)

    if not dataset_already_submitted and not submit_clicked:
        render_empty_state(
            "Dataset ready",
            "Prepare the dataset to profile columns and unlock agent analysis.",
        )
        return

    if dataset_already_submitted and not submit_clicked:
        df = st.session_state["dataset_df"]
        metadata = st.session_state["dataset_metadata"]
        metadata_path = st.session_state["metadata_path"]
        parser_used = st.session_state["parser_used"]
    else:
        logger.info(
            "CSV dataset submitted: source=%s filename=%s size_bytes=%s",
            data_source,
            source_filename,
            len(raw_bytes),
        )

        try:
            df, parser_used = read_csv_with_fallbacks(csv_file)
        except Exception as exc:
            logger.exception("CSV read failed: filename=%s", source_filename)
            st.error(f"Could not read CSV: {exc}")
            st.caption(f"Log: `{APP_LOG_PATH}`")
            st.stop()

        metadata = build_dataset_metadata(
            df,
            source_filename,
            raw_bytes,
            cleaned_description,
        )
        if data_source == "Kaggle dataset":
            metadata["source"] = {
                "type": "kaggle",
                "dataset_ref": kaggle_import["dataset_ref"],
                "selected_file": kaggle_import["selected_file"],
                "download_path": str(kaggle_import["download_path"]),
            }
        else:
            metadata["source"] = {"type": "upload"}
        metadata_path = save_metadata(metadata)
        dataset_path = save_uploaded_dataset(metadata, raw_bytes)
        st.session_state["submitted_dataset_key"] = dataset_key
        st.session_state["dataset_df"] = df
        st.session_state["dataset_metadata"] = metadata
        st.session_state["metadata_path"] = metadata_path
        st.session_state["dataset_path"] = dataset_path
        st.session_state["parser_used"] = parser_used
        logger.info(
            "CSV dataset processed: source=%s filename=%s rows=%s columns=%s description_chars=%s metadata_path=%s dataset_path=%s",
            data_source,
            source_filename,
            metadata["row_count"],
            metadata["column_count"],
            len(cleaned_description),
            metadata_path,
            dataset_path,
        )

    if st.session_state.get("submitted_dataset_key") != dataset_key:
        render_empty_state(
            "Dataset ready",
            "Prepare the dataset to profile columns and unlock agent analysis.",
        )
        return

    render_dataset_summary(metadata, parser_used)

    tab_data, tab_columns, tab_semantic, tab_dashboard, tab_metadata = st.tabs(
        ["Preview", "Schema", "Understanding", "Dashboard", "Artifacts"]
    )

    with tab_data:
        render_section_heading("Preview", "Dataset Rows")
        st.dataframe(df, use_container_width=True)
        if data_source == "Kaggle dataset":
            with st.expander("Kaggle metadata"):
                st.write(kaggle_description)
            with st.expander("Kaggle files"):
                st.dataframe(pd.DataFrame(kaggle_import["files"]), use_container_width=True, hide_index=True)

    with tab_columns:
        render_section_heading("Schema", "Column Profile")
        column_summary = pd.DataFrame(metadata["columns"])
        st.dataframe(
            column_summary[
                [
                    "name",
                    "pandas_dtype",
                    "inferred_role",
                    "null_count",
                    "null_percentage",
                    "unique_count",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab_semantic:
        render_section_heading("Agent", "Semantic Understanding")

        semantic_key = (
            f"{metadata['source_file']}:{metadata['file_sha256']}:"
            f"{hashlib.sha256(cleaned_description.encode('utf-8')).hexdigest()}"
        )
        if st.button("Generate understanding", type="primary"):
            df_head = build_dataframe_context(metadata, df)
            try:
                with st.spinner("Running semantic agent..."):
                    semantic_result = generate_semantic_understanding(
                        metadata=metadata,
                        df_head=df_head,
                    )
                    semantic_path = save_semantic_understanding(metadata, semantic_result)
            except Exception as exc:
                logger.exception(
                    "Semantic understanding failed: filename=%s",
                    source_filename,
                )
                st.error(f"Could not generate semantic understanding: {exc}")
                st.caption(f"Log: `{APP_LOG_PATH}`")
            else:
                st.session_state["semantic_understanding"] = semantic_result
                st.session_state["semantic_understanding_key"] = semantic_key
                st.session_state["semantic_understanding_path"] = semantic_path
                logger.info(
                    "Semantic understanding generated: filename=%s semantic_path=%s",
                    source_filename,
                    semantic_path,
                )
                st.success("Understanding generated.")

        existing_semantic = st.session_state.get("semantic_understanding")
        existing_semantic_key = st.session_state.get("semantic_understanding_key")

        if existing_semantic and existing_semantic_key == semantic_key:
            semantic_path = st.session_state.get("semantic_understanding_path")
            if semantic_path:
                render_artifact_path("Semantic artifact", semantic_path)
            render_semantic_understanding(existing_semantic)
            st.download_button(
                "Download semantic understanding JSON",
                data=existing_semantic.model_dump_json(indent=2),
                file_name="semantic_understanding.json",
                mime="application/json",
            )
        else:
            render_empty_state("No semantic output yet", "Run the semantic agent for domain, metric, and question extraction.")

    with tab_dashboard:
        render_section_heading("Output", "Dashboard")

        existing_semantic = st.session_state.get("semantic_understanding")
        existing_semantic_key = st.session_state.get("semantic_understanding_key")
        semantic_is_current = existing_semantic and existing_semantic_key == semantic_key
        dashboard_key = (
            f"{metadata['source_file']}:{metadata['file_sha256']}:"
            f"{existing_semantic_key or 'no-semantic'}"
        )

        if not semantic_is_current:
            render_empty_state("Understanding required", "Generate semantic understanding before creating the dashboard.")
        elif st.button("Generate dashboard", type="primary"):
            df_head = build_dataframe_context(metadata, df)
            try:
                with st.spinner("Planning metrics and dashboard views..."):
                    metric_plan, analysis_outputs = generate_executable_metric_plan(
                        df=df,
                        semantic_understanding=existing_semantic,
                        df_head=df_head,
                    )
                    metric_plan_path = save_metric_plan(metadata, metric_plan)
                    dashboard_plan, validation_report, critique = generate_validated_dashboard_plan(
                        metadata=metadata,
                        semantic_understanding=existing_semantic,
                        metric_plan=metric_plan,
                        analysis_outputs=analysis_outputs,
                        df_context=df_head,
                    )
                    dashboard_path = save_dashboard_plan(metadata, dashboard_plan)
                    validation_path = save_dashboard_validation_report(
                        metadata,
                        validation_report,
                    )
                    critique_path = (
                        save_dashboard_critique(metadata, critique)
                        if critique is not None
                        else None
                    )
            except Exception as exc:
                metric_plan_path = locals().get("metric_plan_path")
                logger.exception(
                    "Dashboard generation failed: filename=%s metric_plan_path=%s",
                    source_filename,
                    metric_plan_path,
                )
                st.error(f"Could not generate dashboard: {exc}")
                if metric_plan_path:
                    render_artifact_path("Metric plan", metric_plan_path)
                st.caption(f"Log: `{APP_LOG_PATH}`")
            else:
                st.session_state["dashboard_plan"] = dashboard_plan
                st.session_state["dashboard_plan_key"] = dashboard_key
                st.session_state["dashboard_plan_path"] = dashboard_path
                st.session_state["dashboard_validation_report"] = validation_report
                st.session_state["dashboard_validation_path"] = validation_path
                st.session_state["dashboard_critique"] = critique
                st.session_state["dashboard_critique_path"] = critique_path
                st.session_state["metric_plan"] = metric_plan
                st.session_state["metric_plan_key"] = dashboard_key
                st.session_state["metric_plan_path"] = metric_plan_path
                st.session_state["analysis_outputs"] = analysis_outputs
                logger.info(
                    "Dashboard generated: filename=%s metric_plan_path=%s dashboard_path=%s validation_path=%s critique_path=%s validation_status=%s",
                    source_filename,
                    metric_plan_path,
                    dashboard_path,
                    validation_path,
                    critique_path,
                    validation_report.status,
                )
                st.success("Dashboard generated.")

        existing_dashboard = st.session_state.get("dashboard_plan")
        existing_dashboard_key = st.session_state.get("dashboard_plan_key")
        if semantic_is_current and existing_dashboard and existing_dashboard_key == dashboard_key:
            dashboard_path = st.session_state.get("dashboard_plan_path")
            metric_plan_path = st.session_state.get("metric_plan_path")
            render_artifact_path("Metric plan", metric_plan_path)
            render_artifact_path("Dashboard plan", dashboard_path)
            validation_path = st.session_state.get("dashboard_validation_path")
            render_artifact_path("Validation report", validation_path)
            critique_path = st.session_state.get("dashboard_critique_path")
            render_artifact_path("Critique", critique_path)
            analysis_outputs = st.session_state.get("analysis_outputs")
            validation_report = st.session_state.get("dashboard_validation_report")
            critique = st.session_state.get("dashboard_critique")
            if not isinstance(analysis_outputs, dict):
                st.warning("Analysis outputs are missing. Regenerate the dashboard.")
            else:
                render_dashboard(
                    df,
                    existing_dashboard,
                    analysis_outputs,
                    validation_report,
                    critique,
                )
            st.download_button(
                "Download dashboard plan JSON",
                data=existing_dashboard.model_dump_json(indent=2),
                file_name="dashboard_plan.json",
                mime="application/json",
            )
        elif semantic_is_current:
            render_empty_state("No dashboard yet", "Generate the dashboard after semantic understanding is current.")

    with tab_metadata:
        render_section_heading("Artifacts", "Stored Metadata")
        render_artifact_path("Metadata", metadata_path)
        render_artifact_path("Index", METADATA_INDEX_PATH)
        if cleaned_description:
            st.markdown("**Dataset description**")
            st.write(cleaned_description)
        st.json(metadata)
        st.download_button(
            "Download metadata JSON",
            data=json.dumps(metadata, indent=2),
            file_name="dataset_metadata.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
