from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

TraceStatus = Literal["running", "completed", "warning", "failed", "skipped"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def duration_ms(started_at: str, finished_at: str) -> int:
    started = datetime.fromisoformat(started_at)
    finished = datetime.fromisoformat(finished_at)
    return max(int((finished - started).total_seconds() * 1000), 0)


class RunTraceEvent(BaseModel):
    stage: str
    event_type: str = "stage"
    status: TraceStatus = "running"
    started_at: str
    finished_at: str | None = None
    duration_ms: int | None = None
    message: str = ""
    error_type: str | None = None
    error_message: str | None = None
    artifact_paths: dict[str, str] = Field(default_factory=dict)


class RunTrace(BaseModel):
    run_id: str
    job_id: str | None = None
    status: TraceStatus = "running"
    started_at: str
    finished_at: str | None = None
    duration_ms: int | None = None
    message: str = ""
    events: list[RunTraceEvent] = Field(default_factory=list)


class RunTracer:
    def __init__(self, path: Path, run_id: str, job_id: str | None = None):
        self.path = path
        self.trace = RunTrace(run_id=run_id, job_id=job_id, started_at=iso_now())
        self._write()

    def start_event(self, stage: str, message: str = "", event_type: str = "stage") -> RunTraceEvent:
        event = RunTraceEvent(
            stage=stage,
            event_type=event_type,
            status="running",
            started_at=iso_now(),
            message=message,
        )
        self.trace.events.append(event)
        self._write()
        return event

    def complete_event(
        self,
        event: RunTraceEvent,
        message: str = "",
        artifact_paths: dict[str, Any] | None = None,
    ) -> None:
        self._finish_event(event, "completed", message, artifact_paths)

    def warn_event(
        self,
        event: RunTraceEvent,
        message: str = "",
        error: BaseException | None = None,
        artifact_paths: dict[str, Any] | None = None,
    ) -> None:
        self._finish_event(event, "warning", message, artifact_paths, error)

    def fail_event(
        self,
        event: RunTraceEvent,
        message: str = "",
        error: BaseException | None = None,
        artifact_paths: dict[str, Any] | None = None,
    ) -> None:
        self._finish_event(event, "failed", message, artifact_paths, error)

    def skip_event(self, stage: str, message: str = "") -> None:
        event = self.start_event(stage, message=message)
        self._finish_event(event, "skipped", message)

    def finish(self, status: TraceStatus, message: str = "") -> None:
        finished_at = iso_now()
        self.trace.status = status
        self.trace.finished_at = finished_at
        self.trace.duration_ms = duration_ms(self.trace.started_at, finished_at)
        self.trace.message = message
        self._write()

    def _finish_event(
        self,
        event: RunTraceEvent,
        status: TraceStatus,
        message: str = "",
        artifact_paths: dict[str, Any] | None = None,
        error: BaseException | None = None,
    ) -> None:
        finished_at = iso_now()
        event.status = status
        event.finished_at = finished_at
        event.duration_ms = duration_ms(event.started_at, finished_at)
        if message:
            event.message = message
        if error is not None:
            event.error_type = type(error).__name__
            event.error_message = str(error)
        if artifact_paths:
            event.artifact_paths.update(
                {key: str(value) for key, value in artifact_paths.items() if value is not None}
            )
        self._write()

    def _write(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.trace.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            logger.exception("Failed to write run trace: %s", self.path)


def start_trace(path: Path, run_id: str, job_id: str | None = None) -> RunTracer:
    return RunTracer(path=path, run_id=run_id, job_id=job_id)


def load_trace(path: Path) -> RunTrace:
    return RunTrace.model_validate_json(path.read_text(encoding="utf-8"))
