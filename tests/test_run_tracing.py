import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from api import ArtifactStore, run_id_for
from contracts import AnalyticalBrainResult
from core.run_orchestration import run_dashboard_generation
from core.run_tracing import RunTracer, load_trace
from tests.test_agents_contracts import (
    sample_dashboard_plan,
    sample_insights,
    sample_metric_plan,
    sample_semantic,
    sample_validation_report,
)


class RunTracingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "artifacts"
        self.store = ArtifactStore(self.root)
        self.metadata = {
            "source_file": "sample.csv",
            "file_sha256": "abcdef1234567890",
            "created_at": "2026-05-31T00:00:00+00:00",
            "row_count": 2,
            "column_count": 2,
            "columns": [
                {"name": "Training_Intensity", "pandas_dtype": "str", "inferred_role": "categorical"},
                {"name": "Fatigue_Score", "pandas_dtype": "float64", "inferred_role": "numeric"},
            ],
            "dataset_description": "test",
        }
        self.run_id = run_id_for(self.metadata)
        for artifact_type in ["metadata", "dataset"]:
            self.store.path_for(self.metadata, artifact_type).parent.mkdir(parents=True, exist_ok=True)
        self.store.path_for(self.metadata, "metadata").write_text(json.dumps(self.metadata), encoding="utf-8")
        self.store.path_for(self.metadata, "dataset").write_text(
            "Training_Intensity,Fatigue_Score\nHigh,10\nLow,5\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_trace_helper_writes_incremental_events(self):
        trace_path = self.root / "traces" / "sample_trace.json"
        tracer = RunTracer(trace_path, run_id="run-1", job_id="job-1")
        event = tracer.start_event("semantic", "Starting semantic.")
        tracer.complete_event(event, "Semantic complete.", {"semantic": "semantic.json"})
        tracer.finish("completed", "done")

        trace = load_trace(trace_path)

        self.assertEqual(trace.status, "completed")
        self.assertEqual(trace.events[0].stage, "semantic")
        self.assertEqual(trace.events[0].artifact_paths["semantic"], "semantic.json")
        self.assertIsNotNone(trace.events[0].duration_ms)

    def test_successful_run_records_ordered_trace_events_and_artifacts(self):
        with (
            patch("core.run_orchestration.generate_semantic_understanding", return_value=sample_semantic()),
            patch(
                "core.run_orchestration.generate_executable_metric_plan",
                return_value=(sample_metric_plan(), {"fatigue_by_intensity": pd.DataFrame({"value": [1]})}),
            ),
            patch(
                "core.run_orchestration.generate_validated_dashboard_plan",
                return_value=(sample_dashboard_plan(), sample_validation_report().model_copy(update={"status": "passed", "issues": []}), None),
            ),
            patch("core.run_orchestration.generate_analytical_insights", return_value=sample_insights()),
        ):
            run_dashboard_generation(
                self.store,
                self.metadata,
                include_notebook=False,
                run_id=self.run_id,
                job_id="job-success",
            )

        trace = load_trace(self.store.path_for(self.metadata, "trace"))
        stages = [event.stage for event in trace.events]

        self.assertEqual(trace.status, "completed")
        self.assertIn("dataset_context", stages)
        self.assertIn("semantic", stages)
        self.assertIn("metrics", stages)
        self.assertIn("dashboard", stages)
        self.assertIn("notebook", stages)
        metric_event = next(event for event in trace.events if event.stage == "metrics")
        self.assertEqual(metric_event.status, "completed")
        self.assertIn("metric_plan", metric_event.artifact_paths)
        self.assertIn("analysis_outputs", metric_event.artifact_paths)

    def test_required_metric_failure_records_failed_trace(self):
        with (
            patch("core.run_orchestration.generate_semantic_understanding", return_value=sample_semantic()),
            patch("core.run_orchestration.generate_executable_metric_plan", side_effect=ValueError("metric failed")),
        ):
            with self.assertRaisesRegex(ValueError, "metric failed"):
                run_dashboard_generation(
                    self.store,
                    self.metadata,
                    include_notebook=False,
                    run_id=self.run_id,
                    job_id="job-failed",
                )

        trace = load_trace(self.store.path_for(self.metadata, "trace"))
        metric_event = next(event for event in trace.events if event.stage == "metrics")

        self.assertEqual(trace.status, "failed")
        self.assertEqual(metric_event.status, "failed")
        self.assertEqual(metric_event.error_type, "ValueError")
        self.assertIn("metric failed", metric_event.error_message)

    def test_optional_insights_failure_records_warning_not_failed_trace(self):
        with (
            patch("core.run_orchestration.generate_semantic_understanding", return_value=sample_semantic()),
            patch(
                "core.run_orchestration.generate_executable_metric_plan",
                return_value=(sample_metric_plan(), {"fatigue_by_intensity": pd.DataFrame({"value": [1]})}),
            ),
            patch(
                "core.run_orchestration.generate_validated_dashboard_plan",
                return_value=(sample_dashboard_plan(), sample_validation_report().model_copy(update={"status": "passed", "issues": []}), None),
            ),
            patch("core.run_orchestration.generate_analytical_insights", side_effect=RuntimeError("insights down")),
        ):
            run_dashboard_generation(
                self.store,
                self.metadata,
                include_notebook=False,
                run_id=self.run_id,
                job_id="job-warning",
            )

        trace = load_trace(self.store.path_for(self.metadata, "trace"))
        insights_event = next(event for event in trace.events if event.stage == "insights")

        self.assertEqual(trace.status, "completed")
        self.assertEqual(insights_event.status, "warning")
        self.assertEqual(insights_event.error_type, "RuntimeError")


if __name__ == "__main__":
    unittest.main()
