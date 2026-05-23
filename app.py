from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


METADATA_DIR = Path("artifacts") / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
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


def build_dataset_metadata(df: pd.DataFrame, filename: str, raw_bytes: bytes) -> dict[str, Any]:
    return {
        "source_file": filename,
        "file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": analyze_columns(df),
    }


def save_metadata(metadata: dict[str, Any]) -> Path:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return LATEST_METADATA_PATH


st.set_page_config(page_title="Smart AI Dashboarding", layout="wide")

st.title("Smart AI Dashboarding")
st.caption("Upload a CSV to preview the data and generate basic column metadata.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file to begin.")
else:
    raw_bytes = uploaded_file.getvalue()
    logger.info("CSV upload received: filename=%s size_bytes=%s", uploaded_file.name, len(raw_bytes))

    try:
        df, parser_used = read_csv_with_fallbacks(uploaded_file)
    except Exception as exc:
        logger.exception("CSV upload failed: filename=%s", uploaded_file.name)
        st.error(f"Could not read CSV: {exc}")
        st.caption(f"Details were logged to `{APP_LOG_PATH}`.")
        st.stop()

    metadata = build_dataset_metadata(df, uploaded_file.name, raw_bytes)
    st.session_state["dataset_metadata"] = metadata
    metadata_path = save_metadata(metadata)
    logger.info(
        "CSV upload processed: filename=%s rows=%s columns=%s metadata_path=%s",
        uploaded_file.name,
        metadata["row_count"],
        metadata["column_count"],
        metadata_path,
    )

    st.success(f"Loaded {metadata['row_count']} rows and {metadata['column_count']} columns.")
    st.caption(f"CSV parser used: {parser_used}")

    tab_data, tab_columns, tab_metadata = st.tabs(["Data", "Columns", "Metadata"])

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

    with tab_metadata:
        st.subheader("Stored Metadata")
        st.caption(f"Saved to `{metadata_path}`")
        st.json(metadata)
        st.download_button(
            "Download metadata JSON",
            data=json.dumps(metadata, indent=2),
            file_name="dataset_metadata.json",
            mime="application/json",
        )
