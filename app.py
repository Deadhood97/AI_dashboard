from __future__ import annotations

import hashlib
import ast
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st
from agents.dashboard_planner import (
    DashboardChartSpec,
    DashboardKpiSpec,
    DashboardPlan,
    generate_dashboard_plan,
)
from agents.metric_code_planner import (
    PandasMetricPlan,
    generate_metric_code_plan,
)
from agents.semantic_understanding import (
    SemanticUnderstanding,
    generate_semantic_understanding,
)
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


METADATA_DIR = Path("artifacts") / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
METADATA_INDEX_PATH = METADATA_DIR / "metadata_index.json"
SEMANTIC_DIR = Path("artifacts") / "semantic"
METRIC_PLAN_DIR = Path("artifacts") / "metric_plans"
DASHBOARD_DIR = Path("artifacts") / "dashboard"
LOG_DIR = Path("artifacts") / "logs"
APP_LOG_PATH = LOG_DIR / "app.log"


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
    lines = []
    for line in code.splitlines():
        if line.strip() in allowed_imports:
            continue
        lines.append(line)
    return "\n".join(lines)


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
    st.subheader("Data Integrity")
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


def render_kpis(analysis_outputs: dict[str, Any], plan: DashboardPlan) -> None:
    st.subheader("Major KPIs")
    if not plan.kpis:
        st.info("No KPI cards were selected by the dashboard planner.")
        return

    cols = st.columns(min(len(plan.kpis), 4))
    for index, spec in enumerate(plan.kpis):
        with cols[index % len(cols)]:
            st.metric(spec.title, calculate_kpi(analysis_outputs, spec))
            st.caption(spec.rationale)


def sorted_chart_data(chart_data: pd.DataFrame, spec: DashboardChartSpec) -> pd.DataFrame:
    if chart_data.empty:
        return chart_data
    sort_by = spec.sort_by or spec.x or spec.dimension
    if sort_by and sort_by in chart_data.columns:
        ascending = spec.sort_order == "ascending"
        chart_data = chart_data.sort_values(sort_by, ascending=ascending)
    if spec.top_n:
        chart_data = chart_data.head(spec.top_n)
    return chart_data


def render_chart(analysis_outputs: dict[str, Any], spec: DashboardChartSpec) -> None:
    st.markdown(f"**{spec.title}**")
    st.caption(spec.rationale)
    if spec.source_output_key not in analysis_outputs:
        st.warning(f"Missing analysis output: {spec.source_output_key}")
        return

    chart_data = sorted_chart_data(output_to_dataframe(analysis_outputs[spec.source_output_key]), spec)

    try:
        x = spec.x or spec.dimension
        y = spec.y or spec.metric
        if spec.chart_type == "bar" and x in chart_data.columns and y in chart_data.columns:
            if spec.orientation == "horizontal":
                fig = px.bar(chart_data, x=y, y=x, orientation="h", title=spec.title)
            else:
                fig = px.bar(chart_data, x=x, y=y, color=spec.color if spec.color in chart_data.columns else None, title=spec.title)
            st.plotly_chart(fig, use_container_width=True)
        elif spec.chart_type in {"line", "multi_line"} and x in chart_data.columns:
            y_value: str | list[str] | None = y if y in chart_data.columns else None
            if not y_value and spec.metrics:
                y_value = [metric for metric in spec.metrics if metric in chart_data.columns]
            if not y_value:
                st.dataframe(chart_data, use_container_width=True)
                return
            fig = px.line(
                chart_data,
                x=x,
                y=y_value,
                color=spec.color if spec.color in chart_data.columns else None,
                markers=True,
                title=spec.title,
            )
            st.plotly_chart(fig, use_container_width=True)
        elif spec.chart_type == "histogram" and y in chart_data.columns:
            fig = px.histogram(chart_data, x=y, title=spec.title)
            st.plotly_chart(fig, use_container_width=True)
        elif spec.chart_type == "scatter" and x in chart_data.columns and y in chart_data.columns:
            fig = px.scatter(
                chart_data,
                x=x,
                y=y,
                color=spec.color if spec.color in chart_data.columns else None,
                title=spec.title,
            )
            st.plotly_chart(fig, use_container_width=True)
        elif spec.chart_type in {"table", "text", "kpi"}:
            st.dataframe(chart_data, use_container_width=True, hide_index=True)
        else:
            st.warning("Chart spec did not match available output columns. Showing table instead.")
            st.dataframe(chart_data, use_container_width=True, hide_index=True)
    except Exception as exc:
        logger.exception("Dashboard chart render failed: title=%s", spec.title)
        st.warning(f"Could not render this chart: {exc}")
        st.dataframe(chart_data, use_container_width=True, hide_index=True)


def render_dashboard(df: pd.DataFrame, plan: DashboardPlan, analysis_outputs: dict[str, Any]) -> None:
    st.subheader(plan.dashboard_title)
    st.write(plan.dashboard_summary)
    render_data_integrity(df, plan)
    render_kpis(analysis_outputs, plan)

    st.subheader("Overview Charts")
    for chart in plan.overview_charts:
        render_chart(analysis_outputs, chart)

    st.subheader("Answers To Analytical Questions")
    for view in plan.question_views:
        st.markdown(f"**{view.question}**")
        st.write(view.answer_strategy)
        render_chart(analysis_outputs, view.chart)

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
    st.markdown("**Dataset domain**")
    st.write(result.dataset_domain)

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

    st.title("Smart AI Dashboarding")
    st.caption("Upload a CSV to preview the data and generate basic column metadata.")

    if "submitted_dataset_key" not in st.session_state:
        st.session_state["submitted_dataset_key"] = None

    dataset_description = st.text_area(
        "Dataset description",
        placeholder=(
            "Optional: describe what this dataset represents, where it came from, "
            "and what business process or domain it belongs to."
        ),
        help="This context is stored in the dataset schema for future semantic understanding agents.",
    )

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is None:
        st.info("Upload a CSV file to begin.")
        return

    raw_bytes = uploaded_file.getvalue()
    cleaned_description = dataset_description.strip()
    dataset_key = (
        f"{uploaded_file.name}:"
        f"{hashlib.sha256(raw_bytes).hexdigest()}:"
        f"{hashlib.sha256(cleaned_description.encode('utf-8')).hexdigest()}"
    )

    if st.session_state.get("submitted_dataset_key") != dataset_key:
        st.session_state.pop("dataset_df", None)
        st.session_state.pop("dataset_metadata", None)
        st.session_state.pop("metadata_path", None)
        st.session_state.pop("parser_used", None)
        st.session_state.pop("semantic_understanding", None)
        st.session_state.pop("semantic_understanding_key", None)
        st.session_state.pop("semantic_understanding_path", None)
        st.session_state.pop("metric_plan", None)
        st.session_state.pop("metric_plan_key", None)
        st.session_state.pop("metric_plan_path", None)
        st.session_state.pop("analysis_outputs", None)
        st.session_state.pop("dashboard_plan", None)
        st.session_state.pop("dashboard_plan_key", None)
        st.session_state.pop("dashboard_plan_path", None)
        st.session_state["submitted_dataset_key"] = None

    dataset_already_submitted = st.session_state.get("submitted_dataset_key") == dataset_key
    submit_clicked = st.button("Submit dataset", type="primary")

    if not dataset_already_submitted and not submit_clicked:
        st.info("Add a description if helpful, then submit the dataset to generate metadata.")
        return

    if dataset_already_submitted and not submit_clicked:
        df = st.session_state["dataset_df"]
        metadata = st.session_state["dataset_metadata"]
        metadata_path = st.session_state["metadata_path"]
        parser_used = st.session_state["parser_used"]
    else:
        logger.info(
            "CSV upload submitted: filename=%s size_bytes=%s",
            uploaded_file.name,
            len(raw_bytes),
        )

        try:
            df, parser_used = read_csv_with_fallbacks(uploaded_file)
        except Exception as exc:
            logger.exception("CSV upload failed: filename=%s", uploaded_file.name)
            st.error(f"Could not read CSV: {exc}")
            st.caption(f"Details were logged to `{APP_LOG_PATH}`.")
            st.stop()

        metadata = build_dataset_metadata(
            df,
            uploaded_file.name,
            raw_bytes,
            cleaned_description,
        )
        metadata_path = save_metadata(metadata)
        st.session_state["submitted_dataset_key"] = dataset_key
        st.session_state["dataset_df"] = df
        st.session_state["dataset_metadata"] = metadata
        st.session_state["metadata_path"] = metadata_path
        st.session_state["parser_used"] = parser_used
        logger.info(
            "CSV upload processed: filename=%s rows=%s columns=%s description_chars=%s metadata_path=%s",
            uploaded_file.name,
            metadata["row_count"],
            metadata["column_count"],
            len(cleaned_description),
            metadata_path,
        )

    if st.session_state.get("submitted_dataset_key") != dataset_key:
        st.info("Submit the dataset to generate metadata.")
        return

    st.success(f"Loaded {metadata['row_count']} rows and {metadata['column_count']} columns.")
    st.caption(f"CSV parser used: {parser_used}")

    tab_data, tab_columns, tab_semantic, tab_dashboard, tab_metadata = st.tabs(
        ["Data", "Columns", "Semantic Understanding", "Dashboard", "Metadata"]
    )

    with tab_data:
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True)

    with tab_columns:
        st.subheader("Column Analysis")
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
        st.subheader("What The App Understands")
        st.caption(
            "Generate a semantic summary from the saved metadata and the first rows "
            "of the dataframe."
        )

        semantic_key = (
            f"{metadata['source_file']}:{metadata['file_sha256']}:"
            f"{hashlib.sha256(cleaned_description.encode('utf-8')).hexdigest()}"
        )
        if st.button("Generate semantic understanding", type="primary"):
            df_head = df.head(5).to_markdown(index=False)
            try:
                with st.spinner("Asking the semantic understanding agent..."):
                    semantic_result = generate_semantic_understanding(
                        metadata=metadata,
                        df_head=df_head,
                    )
                    semantic_path = save_semantic_understanding(metadata, semantic_result)
            except Exception as exc:
                logger.exception(
                    "Semantic understanding failed: filename=%s",
                    uploaded_file.name,
                )
                st.error(f"Could not generate semantic understanding: {exc}")
                st.caption(f"Details were logged to `{APP_LOG_PATH}`.")
            else:
                st.session_state["semantic_understanding"] = semantic_result
                st.session_state["semantic_understanding_key"] = semantic_key
                st.session_state["semantic_understanding_path"] = semantic_path
                logger.info(
                    "Semantic understanding generated: filename=%s semantic_path=%s",
                    uploaded_file.name,
                    semantic_path,
                )
                st.success("Semantic understanding generated.")

        existing_semantic = st.session_state.get("semantic_understanding")
        existing_semantic_key = st.session_state.get("semantic_understanding_key")

        if existing_semantic and existing_semantic_key == semantic_key:
            semantic_path = st.session_state.get("semantic_understanding_path")
            if semantic_path:
                st.caption(f"Saved to `{semantic_path}`")
            render_semantic_understanding(existing_semantic)
            st.download_button(
                "Download semantic understanding JSON",
                data=existing_semantic.model_dump_json(indent=2),
                file_name="semantic_understanding.json",
                mime="application/json",
            )
        else:
            st.info("Click the button to run the semantic understanding agent.")

    with tab_dashboard:
        st.subheader("Dataset Dashboard")
        st.caption(
            "Generate a basic dashboard from metadata, semantic understanding, "
            "and safe pandas/Plotly renderers."
        )

        existing_semantic = st.session_state.get("semantic_understanding")
        existing_semantic_key = st.session_state.get("semantic_understanding_key")
        semantic_is_current = existing_semantic and existing_semantic_key == semantic_key
        dashboard_key = (
            f"{metadata['source_file']}:{metadata['file_sha256']}:"
            f"{existing_semantic_key or 'no-semantic'}"
        )

        if not semantic_is_current:
            st.info("Generate semantic understanding before creating the dashboard.")
        elif st.button("Generate dashboard", type="primary"):
            df_head = df.head(5).to_markdown(index=False)
            try:
                with st.spinner("Planning metrics and dashboard views..."):
                    metric_plan = generate_metric_code_plan(
                        semantic_understanding=existing_semantic,
                        df_head=df_head,
                    )
                    analysis_outputs = execute_metric_plan(df, metric_plan)
                    metric_plan_path = save_metric_plan(metadata, metric_plan)
                    dashboard_plan = generate_dashboard_plan(
                        metadata=metadata,
                        semantic_understanding=existing_semantic,
                        metric_plan=metric_plan,
                        df_head=df_head,
                    )
                    dashboard_path = save_dashboard_plan(metadata, dashboard_plan)
            except Exception as exc:
                logger.exception(
                    "Dashboard generation failed: filename=%s",
                    uploaded_file.name,
                )
                st.error(f"Could not generate dashboard: {exc}")
                st.caption(f"Details were logged to `{APP_LOG_PATH}`.")
            else:
                st.session_state["dashboard_plan"] = dashboard_plan
                st.session_state["dashboard_plan_key"] = dashboard_key
                st.session_state["dashboard_plan_path"] = dashboard_path
                st.session_state["metric_plan"] = metric_plan
                st.session_state["metric_plan_key"] = dashboard_key
                st.session_state["metric_plan_path"] = metric_plan_path
                st.session_state["analysis_outputs"] = analysis_outputs
                logger.info(
                    "Dashboard generated: filename=%s metric_plan_path=%s dashboard_path=%s",
                    uploaded_file.name,
                    metric_plan_path,
                    dashboard_path,
                )
                st.success("Dashboard generated.")

        existing_dashboard = st.session_state.get("dashboard_plan")
        existing_dashboard_key = st.session_state.get("dashboard_plan_key")
        if semantic_is_current and existing_dashboard and existing_dashboard_key == dashboard_key:
            dashboard_path = st.session_state.get("dashboard_plan_path")
            metric_plan_path = st.session_state.get("metric_plan_path")
            if metric_plan_path:
                st.caption(f"Metric plan saved to `{metric_plan_path}`")
            if dashboard_path:
                st.caption(f"Dashboard plan saved to `{dashboard_path}`")
            analysis_outputs = st.session_state.get("analysis_outputs")
            if not isinstance(analysis_outputs, dict):
                st.warning("Analysis outputs are missing. Regenerate the dashboard.")
            else:
                render_dashboard(df, existing_dashboard, analysis_outputs)
            st.download_button(
                "Download dashboard plan JSON",
                data=existing_dashboard.model_dump_json(indent=2),
                file_name="dashboard_plan.json",
                mime="application/json",
            )
        elif semantic_is_current:
            st.info("Click the button to generate the dashboard.")

    with tab_metadata:
        st.subheader("Stored Metadata")
        st.caption(f"Saved to `{metadata_path}`")
        st.caption(f"Metadata index: `{METADATA_INDEX_PATH}`")
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
