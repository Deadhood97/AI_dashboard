from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
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
    logger.info(
        "CSV upload received: filename=%s size_bytes=%s",
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

    cleaned_description = dataset_description.strip()
    metadata = build_dataset_metadata(
        df,
        uploaded_file.name,
        raw_bytes,
        cleaned_description,
    )
    st.session_state["dataset_metadata"] = metadata
    metadata_path = save_metadata(metadata)
    logger.info(
        "CSV upload processed: filename=%s rows=%s columns=%s description_chars=%s metadata_path=%s",
        uploaded_file.name,
        metadata["row_count"],
        metadata["column_count"],
        len(cleaned_description),
        metadata_path,
    )

    st.success(f"Loaded {metadata['row_count']} rows and {metadata['column_count']} columns.")
    st.caption(f"CSV parser used: {parser_used}")

    tab_data, tab_columns, tab_semantic, tab_metadata = st.tabs(
        ["Data", "Columns", "Semantic Understanding", "Metadata"]
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
