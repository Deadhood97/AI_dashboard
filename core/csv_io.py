from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)


def read_csv_with_fallbacks(uploaded_file: Any) -> tuple[pd.DataFrame, str]:
    attempts = [
        {
            "label": "default pandas C parser",
            "options": {},
        },
        {
            "label": "python parser with inferred delimiter",
            "options": {
                "engine": "python",
                "sep": None,
            },
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
            if (
                attempt["label"] == "default pandas C parser"
                and len(df.columns) == 1
                and any(delimiter in str(df.columns[0]) for delimiter in [";", "\t", "|"])
            ):
                raise ValueError("Default parser produced one delimited column.")
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
