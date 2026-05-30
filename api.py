from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


ARTIFACT_ROOT = Path("artifacts")


def slugify_filename(filename: str) -> str:
    stem = Path(filename).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "dataset"


def run_id_for(metadata: dict[str, Any]) -> str:
    file_hash = str(metadata["file_sha256"])[:12]
    return f"{slugify_filename(str(metadata['source_file']))}_{file_hash}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class ArtifactStatus(BaseModel):
    metadata: bool = False
    dataset: bool = False
    semantic: bool = False
    metric_plan: bool = False
    dashboard: bool = False
    validation: bool = False
    critique: bool = False
    insights: bool = False
    notebook: bool = False


class RunSummary(BaseModel):
    run_id: str
    source_file: str
    file_sha256: str
    created_at: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    artifacts: ArtifactStatus = Field(default_factory=ArtifactStatus)


class RunBundle(BaseModel):
    summary: RunSummary
    metadata: dict[str, Any]
    semantic_understanding: dict[str, Any] | None = None
    metric_plan: dict[str, Any] | None = None
    dashboard_plan: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    dashboard_critique: dict[str, Any] | None = None
    analytical_insights: dict[str, Any] | None = None
    notebook_available: bool = False


class KaggleImportRequest(BaseModel):
    dataset_ref: str
    requested_file: str = ""
    description: str = ""


class ArtifactStore:
    def __init__(self, root: Path = ARTIFACT_ROOT):
        self.root = root

    @property
    def metadata_dir(self) -> Path:
        return self.root / "metadata"

    @property
    def metadata_index_path(self) -> Path:
        return self.metadata_dir / "metadata_index.json"

    @property
    def latest_metadata_path(self) -> Path:
        return self.metadata_dir / "latest_metadata.json"

    def path_for(self, metadata: dict[str, Any], artifact_type: str) -> Path:
        stem = run_id_for(metadata)
        paths = {
            "metadata": self.root / "metadata" / f"{stem}.json",
            "dataset": self.root / "datasets" / f"{stem}.csv",
            "semantic": self.root / "semantic" / f"{stem}_semantic.json",
            "metric_plan": self.root / "metric_plans" / f"{stem}_metric_plan.json",
            "dashboard": self.root / "dashboard" / f"{stem}_dashboard.json",
            "validation": self.root / "dashboard" / f"{stem}_dashboard_validation.json",
            "critique": self.root / "critiques" / f"{stem}_dashboard_critique.json",
            "insights": self.root / "insights" / f"{stem}_analytical_insights.json",
            "notebook": self.root / "notebooks" / f"{stem}_analysis_notebook.ipynb",
        }
        return paths[artifact_type]

    def artifact_status(self, metadata: dict[str, Any]) -> ArtifactStatus:
        return ArtifactStatus(
            **{
                artifact_type: self.path_for(metadata, artifact_type).exists()
                for artifact_type in ArtifactStatus.model_fields
            }
        )

    def list_metadata_entries(self) -> list[dict[str, Any]]:
        if not self.metadata_index_path.exists():
            return []
        entries = read_json(self.metadata_index_path)
        return entries if isinstance(entries, list) else []

    def load_metadata_for_run(self, run_id: str) -> dict[str, Any]:
        for entry in self.list_metadata_entries():
            if run_id_for(entry) == run_id:
                metadata_path = Path(entry.get("metadata_file", ""))
                if not metadata_path.is_absolute():
                    metadata_path = metadata_path
                if metadata_path.exists():
                    return read_json(metadata_path)
                fallback = self.path_for(entry, "metadata")
                if fallback.exists():
                    return read_json(fallback)
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    def latest_metadata(self) -> dict[str, Any]:
        if not self.latest_metadata_path.exists():
            raise HTTPException(status_code=404, detail="No latest run artifact exists.")
        return read_json(self.latest_metadata_path)

    def summary_for(self, metadata: dict[str, Any]) -> RunSummary:
        return RunSummary(
            run_id=run_id_for(metadata),
            source_file=str(metadata.get("source_file", "")),
            file_sha256=str(metadata.get("file_sha256", "")),
            created_at=metadata.get("created_at"),
            row_count=metadata.get("row_count"),
            column_count=metadata.get("column_count"),
            artifacts=self.artifact_status(metadata),
        )

    def list_runs(self) -> list[RunSummary]:
        summaries = [self.summary_for(entry) for entry in self.list_metadata_entries()]
        return sorted(summaries, key=lambda run: run.created_at or "", reverse=True)

    def optional_json_artifact(self, metadata: dict[str, Any], artifact_type: str) -> dict[str, Any] | None:
        path = self.path_for(metadata, artifact_type)
        if not path.exists():
            return None
        return read_json(path)

    def bundle_for(self, metadata: dict[str, Any]) -> RunBundle:
        return RunBundle(
            summary=self.summary_for(metadata),
            metadata=metadata,
            semantic_understanding=self.optional_json_artifact(metadata, "semantic"),
            metric_plan=self.optional_json_artifact(metadata, "metric_plan"),
            dashboard_plan=self.optional_json_artifact(metadata, "dashboard"),
            validation_report=self.optional_json_artifact(metadata, "validation"),
            dashboard_critique=self.optional_json_artifact(metadata, "critique"),
            analytical_insights=self.optional_json_artifact(metadata, "insights"),
            notebook_available=self.path_for(metadata, "notebook").exists(),
        )

    def notebook_for(self, metadata: dict[str, Any]) -> dict[str, Any]:
        path = self.path_for(metadata, "notebook")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Notebook artifact not found.")
        return read_json(path)

    def save_dataset_run(
        self,
        *,
        filename: str,
        raw_bytes: bytes,
        dataset_description: str,
        source: dict[str, Any],
    ) -> RunBundle:
        try:
            df = pd.read_csv(BytesIO(raw_bytes))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}") from exc

        metadata = {
            "source_file": filename,
            "file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_description": dataset_description,
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": [
                {
                    "name": str(column),
                    "dtype": str(df[column].dtype),
                    "missing_count": int(df[column].isna().sum()),
                    "non_null_count": int(df[column].notna().sum()),
                }
                for column in df.columns
            ],
            "schema": {
                "description": dataset_description,
                "columns": [str(column) for column in df.columns],
            },
            "source": source,
        }

        run_id = run_id_for(metadata)
        for folder in [
            "metadata",
            "datasets",
            "semantic",
            "metric_plans",
            "dashboard",
            "critiques",
            "insights",
            "notebooks",
        ]:
            (self.root / folder).mkdir(parents=True, exist_ok=True)

        metadata_path = self.path_for(metadata, "metadata")
        metadata_json = json.dumps(metadata, indent=2)
        metadata_path.write_text(metadata_json, encoding="utf-8")
        self.latest_metadata_path.write_text(metadata_json, encoding="utf-8")
        self.path_for(metadata, "dataset").write_bytes(raw_bytes)

        index = self.list_metadata_entries()
        index = [
            entry
            for entry in index
            if not (
                entry.get("source_file") == metadata["source_file"]
                and entry.get("file_sha256") == metadata["file_sha256"]
            )
        ]
        index.append(
            {
                "source_file": metadata["source_file"],
                "metadata_file": str(metadata_path),
                "file_sha256": metadata["file_sha256"],
                "created_at": metadata["created_at"],
                "row_count": metadata["row_count"],
                "column_count": metadata["column_count"],
            }
        )
        self.metadata_index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return self.bundle_for(metadata)


def fetch_kaggle_dataset_default(dataset_ref: str, requested_file: str = "") -> dict[str, Any]:
    from app import fetch_kaggle_dataset

    return fetch_kaggle_dataset(dataset_ref, requested_file)


def create_app(
    store: ArtifactStore | None = None,
    kaggle_fetcher: Callable[[str, str], dict[str, Any]] | None = None,
) -> FastAPI:
    store = store or ArtifactStore()
    kaggle_fetcher = kaggle_fetcher or fetch_kaggle_dataset_default
    app = FastAPI(title="Dashboard Studio API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/runs", response_model=list[RunSummary])
    def list_runs() -> list[RunSummary]:
        return store.list_runs()

    @app.get("/api/runs/latest", response_model=RunBundle)
    def latest_run() -> RunBundle:
        return store.bundle_for(store.latest_metadata())

    @app.get("/api/runs/{run_id}", response_model=RunBundle)
    def get_run(run_id: str) -> RunBundle:
        return store.bundle_for(store.load_metadata_for_run(run_id))

    @app.get("/api/runs/{run_id}/notebook")
    def get_notebook(run_id: str) -> dict[str, Any]:
        return store.notebook_for(store.load_metadata_for_run(run_id))

    @app.post("/api/datasets/upload", response_model=RunBundle)
    async def upload_dataset(
        file: UploadFile = File(...),
        description: str = Form(""),
    ) -> RunBundle:
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Upload a CSV file.")
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")
        return store.save_dataset_run(
            filename=file.filename,
            raw_bytes=raw_bytes,
            dataset_description=description,
            source={"type": "upload"},
        )

    @app.post("/api/datasets/kaggle", response_model=RunBundle)
    def import_kaggle_dataset(payload: KaggleImportRequest) -> RunBundle:
        try:
            kaggle_import = kaggle_fetcher(payload.dataset_ref, payload.requested_file)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Kaggle import failed: {exc}") from exc

        kaggle_description = str(kaggle_import.get("description") or "")
        description_parts = [part for part in [kaggle_description, payload.description.strip()] if part]
        return store.save_dataset_run(
            filename=str(kaggle_import["filename"]),
            raw_bytes=kaggle_import["raw_bytes"],
            dataset_description="\n\n".join(description_parts),
            source={
                "type": "kaggle",
                "dataset_ref": kaggle_import.get("dataset_ref"),
                "selected_file": kaggle_import.get("selected_file"),
                "download_path": str(kaggle_import.get("download_path", "")),
            },
        )

    return app


app = create_app()
