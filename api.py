from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
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


def create_app(store: ArtifactStore | None = None) -> FastAPI:
    store = store or ArtifactStore()
    app = FastAPI(title="Dashboard Studio API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET"],
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

    return app


app = create_app()

