from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


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


def infer_role_from_dtype(dtype: str | None) -> str | None:
    """Best-effort role inference for legacy metadata that only stored dtype."""
    if not dtype:
        return None
    normalized = dtype.lower()
    if "datetime" in normalized or normalized in {"date", "time", "timestamp"}:
        return "temporal"
    if normalized in {"bool", "boolean"}:
        return "boolean"
    if any(token in normalized for token in ["int", "float", "double", "number", "decimal"]):
        return "numeric"
    if normalized in {"category", "categorical"}:
        return "categorical"
    if normalized in {"str", "string", "object"}:
        return "text"
    return None


def normalize_column_metadata(column: dict[str, Any], row_count: int | None = None) -> dict[str, Any]:
    """Return a column profile with the canonical metadata keys filled in."""
    normalized = dict(column)
    pandas_dtype = normalized.get("pandas_dtype") or normalized.get("dtype")
    if pandas_dtype is not None:
        normalized["pandas_dtype"] = str(pandas_dtype)
        normalized.setdefault("dtype", str(pandas_dtype))

    normalized.setdefault("inferred_role", infer_role_from_dtype(normalized.get("pandas_dtype")))

    if "null_count" not in normalized and "missing_count" in normalized:
        normalized["null_count"] = normalized["missing_count"]
    if "missing_count" not in normalized and "null_count" in normalized:
        normalized["missing_count"] = normalized["null_count"]

    if "unique_count" not in normalized and "non_null_count" in normalized:
        normalized["unique_count"] = normalized["non_null_count"]

    if "null_percentage" not in normalized:
        null_count = normalized.get("null_count")
        total_rows = row_count or normalized.get("row_count")
        if isinstance(null_count, (int, float)) and isinstance(total_rows, (int, float)) and total_rows:
            normalized["null_percentage"] = round(float(null_count) / float(total_rows) * 100, 2)

    if row_count is not None:
        normalized.setdefault("row_count", row_count)

    return normalized


def normalize_dataset_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Normalize saved metadata so legacy and current runs expose one shape."""
    normalized = dict(metadata)
    row_count = normalized.get("row_count")
    row_count_int = int(row_count) if isinstance(row_count, (int, float)) else None
    columns = [
        normalize_column_metadata(column, row_count=row_count_int)
        for column in normalized.get("columns", [])
        if isinstance(column, dict)
    ]
    normalized["columns"] = columns

    schema = dict(normalized.get("schema") or {})
    schema_columns = schema.get("columns")
    if not schema_columns or all(isinstance(column, str) for column in schema_columns):
        schema["columns"] = columns
    else:
        schema["columns"] = [
            normalize_column_metadata(column, row_count=row_count_int)
            if isinstance(column, dict)
            else column
            for column in schema_columns
        ]
    normalized["schema"] = schema
    return normalized


def build_dataset_metadata(
    df: pd.DataFrame,
    filename: str,
    raw_bytes: bytes,
    dataset_description: str,
) -> dict[str, Any]:
    columns = analyze_columns(df)

    return normalize_dataset_metadata({
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
    })


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def _compact_column_for_context(column: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {
        "name": column.get("name"),
        "pandas_dtype": column.get("pandas_dtype") or column.get("dtype"),
        "inferred_role": column.get("inferred_role"),
        "null_count": column.get("null_count", column.get("missing_count")),
        "unique_count": column.get("unique_count"),
    }
    if "statistics" in column:
        compacted["statistics"] = column["statistics"]
    if "sample_values" in column:
        compacted["sample_values"] = column["sample_values"][:3]
    if "top_values" in column:
        compacted["top_values"] = column["top_values"][:8]
    if "unique_values" in column:
        compacted["unique_values"] = column["unique_values"][:20]
    if "representative_values" in column:
        compacted["representative_values"] = column["representative_values"][:20]
    return {key: value for key, value in compacted.items() if value is not None}


def compact_metadata_for_agent_context(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": metadata["source_file"],
        "row_count": metadata["row_count"],
        "column_count": metadata["column_count"],
        "dataset_description": _truncate_text(metadata.get("dataset_description", ""), 1600),
        "columns": [_compact_column_for_context(column) for column in metadata["columns"]],
    }


def build_dataframe_context(metadata: dict[str, Any], df: pd.DataFrame, rows: int = 5) -> str:
    context = compact_metadata_for_agent_context(metadata)
    return (
        "Dataset context JSON:\n"
        f"{json.dumps(context, indent=2)}\n\n"
        f"First {rows} dataframe rows:\n{df.head(rows).to_markdown(index=False)}"
    )


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
