from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.dataset_metadata import normalize_dataset_metadata
from core.run_orchestration import run_dashboard_generation, serialize_analysis_outputs
from core.run_tracing import RunTrace


ARTIFACT_ROOT = Path("artifacts")
logger = logging.getLogger(__name__)


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
    analysis_outputs: bool = False
    dashboard: bool = False
    validation: bool = False
    critique: bool = False
    insights: bool = False
    notebook: bool = False
    trace: bool = False


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
    analysis_outputs: dict[str, Any] | None = None
    dashboard_plan: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    dashboard_critique: dict[str, Any] | None = None
    analytical_insights: dict[str, Any] | None = None
    notebook_available: bool = False
    trace: RunTrace | None = None


class KaggleImportRequest(BaseModel):
    dataset_ref: str
    requested_file: str = ""
    description: str = ""


class GenerateRunRequest(BaseModel):
    include_notebook: bool = True


class JobStatus(BaseModel):
    job_id: str
    run_id: str
    status: str
    stage: str
    message: str = ""
    started_at: str
    finished_at: str | None = None


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
            "analysis_outputs": self.root / "analysis_outputs" / f"{stem}_analysis_outputs.json",
            "dashboard": self.root / "dashboard" / f"{stem}_dashboard.json",
            "validation": self.root / "dashboard" / f"{stem}_dashboard_validation.json",
            "critique": self.root / "critiques" / f"{stem}_dashboard_critique.json",
            "insights": self.root / "insights" / f"{stem}_analytical_insights.json",
            "notebook": self.root / "notebooks" / f"{stem}_analysis_notebook.ipynb",
            "trace": self.root / "traces" / f"{stem}_trace.json",
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
                    return normalize_dataset_metadata(read_json(metadata_path))
                fallback = self.path_for(entry, "metadata")
                if fallback.exists():
                    return normalize_dataset_metadata(read_json(fallback))
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    def latest_metadata(self) -> dict[str, Any]:
        if not self.latest_metadata_path.exists():
            raise HTTPException(status_code=404, detail="No latest run artifact exists.")
        return normalize_dataset_metadata(read_json(self.latest_metadata_path))

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
            analysis_outputs=self.optional_json_artifact(metadata, "analysis_outputs"),
            dashboard_plan=self.optional_json_artifact(metadata, "dashboard"),
            validation_report=self.optional_json_artifact(metadata, "validation"),
            dashboard_critique=self.optional_json_artifact(metadata, "critique"),
            analytical_insights=self.optional_json_artifact(metadata, "insights"),
            notebook_available=self.path_for(metadata, "notebook").exists(),
            trace=self.optional_json_artifact(metadata, "trace"),
        )

    def notebook_for(self, metadata: dict[str, Any]) -> dict[str, Any]:
        path = self.path_for(metadata, "notebook")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Notebook artifact not found.")
        return read_json(path)

    def trace_for(self, metadata: dict[str, Any]) -> RunTrace:
        path = self.path_for(metadata, "trace")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Trace artifact not found.")
        return RunTrace.model_validate(read_json(path))

    def save_dataset_run(
        self,
        *,
        filename: str,
        raw_bytes: bytes,
        dataset_description: str,
        source: dict[str, Any],
    ) -> RunBundle:
        try:
            from core.csv_io import make_named_bytes_file, read_csv_with_fallbacks
            from core.dataset_metadata import build_dataset_metadata

            df, _parser_used = read_csv_with_fallbacks(make_named_bytes_file(raw_bytes, filename))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}") from exc

        metadata = build_dataset_metadata(df, filename, raw_bytes, dataset_description)
        metadata["source"] = source
        metadata = normalize_dataset_metadata(metadata)

        run_id = run_id_for(metadata)
        for folder in [
            "metadata",
            "datasets",
            "semantic",
            "metric_plans",
            "analysis_outputs",
            "dashboard",
            "critiques",
            "insights",
            "notebooks",
            "traces",
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


class JobManager:
    def __init__(self):
        self._jobs: dict[str, JobStatus] = {}
        self._lock = threading.Lock()

    def create(self, run_id: str) -> JobStatus:
        job = JobStatus(
            job_id=uuid.uuid4().hex,
            run_id=run_id,
            status="queued",
            stage="queued",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._set(job)
        return job

    def get(self, job_id: str) -> JobStatus:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        return job

    def update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        stage: str | None = None,
        message: str | None = None,
        finished: bool = False,
    ) -> None:
        with self._lock:
            job = self._jobs[job_id]
            self._jobs[job_id] = job.model_copy(
                update={
                    "status": status or job.status,
                    "stage": stage or job.stage,
                    "message": job.message if message is None else message,
                    "finished_at": datetime.now(timezone.utc).isoformat() if finished else job.finished_at,
                }
            )

    def _set(self, job: JobStatus) -> None:
        with self._lock:
            self._jobs[job.job_id] = job


def fetch_kaggle_dataset_default(dataset_ref: str, requested_file: str = "") -> dict[str, Any]:
    from core.kaggle_import import fetch_kaggle_dataset

    return fetch_kaggle_dataset(dataset_ref, requested_file)


def create_app(
    store: ArtifactStore | None = None,
    kaggle_fetcher: Callable[[str, str], dict[str, Any]] | None = None,
    generation_runner: Callable[..., RunBundle] | None = None,
    job_manager: JobManager | None = None,
) -> FastAPI:
    store = store or ArtifactStore()
    kaggle_fetcher = kaggle_fetcher or fetch_kaggle_dataset_default
    generation_runner = generation_runner or run_dashboard_generation
    job_manager = job_manager or JobManager()
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

    @app.get("/api/runs/{run_id}/trace", response_model=RunTrace)
    def get_trace(run_id: str) -> RunTrace:
        return store.trace_for(store.load_metadata_for_run(run_id))

    @app.get("/api/jobs/{job_id}", response_model=JobStatus)
    def get_job(job_id: str) -> JobStatus:
        return job_manager.get(job_id)

    @app.post("/api/runs/{run_id}/generate", response_model=JobStatus)
    def generate_run(
        run_id: str,
        payload: GenerateRunRequest,
        background_tasks: BackgroundTasks,
    ) -> JobStatus:
        metadata = store.load_metadata_for_run(run_id)
        job = job_manager.create(run_id)

        def task() -> None:
            try:
                job_manager.update(job.job_id, status="running", stage="starting")
                generation_runner(
                    store,
                    metadata,
                    payload.include_notebook,
                    lambda stage: job_manager.update(job.job_id, status="running", stage=stage),
                    run_id=run_id,
                    job_id=job.job_id,
                )
            except Exception as exc:
                logger.exception("Dashboard generation job failed: job_id=%s run_id=%s", job.job_id, run_id)
                job_manager.update(
                    job.job_id,
                    status="failed",
                    stage="failed",
                    message=f"{type(exc).__name__}: {exc}",
                    finished=True,
                )
            else:
                job_manager.update(
                    job.job_id,
                    status="completed",
                    stage="complete",
                    message="Dashboard artifacts generated.",
                    finished=True,
                )

        background_tasks.add_task(task)
        return job

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
