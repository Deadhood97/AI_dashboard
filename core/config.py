from __future__ import annotations

import os
from pathlib import Path


METADATA_DIR = Path("artifacts") / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
METADATA_INDEX_PATH = METADATA_DIR / "metadata_index.json"
DATASET_DIR = Path("artifacts") / "datasets"
SEMANTIC_DIR = Path("artifacts") / "semantic"
METRIC_PLAN_DIR = Path("artifacts") / "metric_plans"
DASHBOARD_DIR = Path("artifacts") / "dashboard"
CRITIQUE_DIR = Path("artifacts") / "critiques"
INSIGHTS_DIR = Path("artifacts") / "insights"
NOTEBOOK_DIR = Path("artifacts") / "notebooks"
TRACE_DIR = Path("artifacts") / "traces"
LOG_DIR = Path("artifacts") / "logs"
APP_LOG_PATH = LOG_DIR / "app.log"
KAGGLE_DOWNLOAD_DIR = Path("artifacts") / "kaggle_downloads"


def notebook_view_enabled() -> bool:
    value = os.getenv("ENABLE_NOTEBOOK_VIEW", "").strip().lower()
    return value in {"1", "true", "yes", "on"}
