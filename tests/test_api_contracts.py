import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import ArtifactStore, create_app, run_id_for, serialize_analysis_outputs
from contracts import SemanticUnderstanding


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "artifacts"
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

        self.metadata = {
            "source_file": "sample dataset.csv",
            "file_sha256": "abcdef1234567890",
            "created_at": "2026-05-31T00:00:00+00:00",
            "row_count": 10,
            "column_count": 3,
            "columns": [],
        }
        self.run_id = run_id_for(self.metadata)
        self.metadata_path = self.root / "metadata" / f"{self.run_id}.json"
        self.metadata_path.write_text(json.dumps(self.metadata), encoding="utf-8")
        (self.root / "metadata" / "latest_metadata.json").write_text(
            json.dumps(self.metadata),
            encoding="utf-8",
        )
        (self.root / "metadata" / "metadata_index.json").write_text(
            json.dumps(
                [
                    {
                        "source_file": self.metadata["source_file"],
                        "file_sha256": self.metadata["file_sha256"],
                        "created_at": self.metadata["created_at"],
                        "row_count": self.metadata["row_count"],
                        "column_count": self.metadata["column_count"],
                        "metadata_file": str(self.metadata_path),
                    }
                ]
            ),
            encoding="utf-8",
        )

        (self.root / "semantic" / f"{self.run_id}_semantic.json").write_text(
            json.dumps({"dataset_domain": "Testing"}),
            encoding="utf-8",
        )
        (self.root / "dashboard" / f"{self.run_id}_dashboard.json").write_text(
            json.dumps({"dashboard_title": "Sample Dashboard"}),
            encoding="utf-8",
        )
        (self.root / "dashboard" / f"{self.run_id}_dashboard_validation.json").write_text(
            json.dumps({"status": "passed", "issues": []}),
            encoding="utf-8",
        )
        (self.root / "notebooks" / f"{self.run_id}_analysis_notebook.ipynb").write_text(
            json.dumps({"nbformat": 4, "cells": []}),
            encoding="utf-8",
        )

        self.client = TestClient(create_app(ArtifactStore(self.root)))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_list_runs_returns_artifact_status(self):
        response = self.client.get("/api/runs")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload[0]["run_id"], self.run_id)
        self.assertTrue(payload[0]["artifacts"]["metadata"])
        self.assertTrue(payload[0]["artifacts"]["semantic"])
        self.assertTrue(payload[0]["artifacts"]["dashboard"])
        self.assertTrue(payload[0]["artifacts"]["validation"])
        self.assertTrue(payload[0]["artifacts"]["notebook"])
        self.assertFalse(payload[0]["artifacts"]["metric_plan"])
        self.assertFalse(payload[0]["artifacts"]["analysis_outputs"])
        self.assertFalse(payload[0]["artifacts"]["trace"])

    def test_latest_run_bundle_returns_frontend_contract(self):
        response = self.client.get("/api/runs/latest")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["run_id"], self.run_id)
        self.assertEqual(payload["metadata"]["source_file"], "sample dataset.csv")
        self.assertEqual(payload["semantic_understanding"]["dataset_domain"], "Testing")
        self.assertEqual(payload["dashboard_plan"]["dashboard_title"], "Sample Dashboard")
        self.assertEqual(payload["validation_report"]["status"], "passed")
        self.assertTrue(payload["notebook_available"])
        self.assertIsNone(payload["trace"])

    def test_run_trace_endpoint_returns_trace_or_404(self):
        missing = self.client.get(f"/api/runs/{self.run_id}/trace")
        self.assertEqual(missing.status_code, 404)

        trace_payload = {
            "run_id": self.run_id,
            "job_id": "job-1",
            "status": "completed",
            "started_at": "2026-05-31T00:00:00+00:00",
            "finished_at": "2026-05-31T00:00:01+00:00",
            "duration_ms": 1000,
            "message": "ok",
            "events": [
                {
                    "stage": "semantic",
                    "event_type": "stage",
                    "status": "completed",
                    "started_at": "2026-05-31T00:00:00+00:00",
                    "finished_at": "2026-05-31T00:00:01+00:00",
                    "duration_ms": 1000,
                    "message": "done",
                    "artifact_paths": {"semantic": "semantic.json"},
                }
            ],
        }
        self.client.app.dependency_overrides = {}
        (self.root / "traces" / f"{self.run_id}_trace.json").write_text(
            json.dumps(trace_payload),
            encoding="utf-8",
        )

        response = self.client.get(f"/api/runs/{self.run_id}/trace")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"][0]["stage"], "semantic")

        bundle = self.client.get(f"/api/runs/{self.run_id}").json()
        self.assertTrue(bundle["summary"]["artifacts"]["trace"])
        self.assertEqual(bundle["trace"]["status"], "completed")

    def test_run_notebook_endpoint_returns_ipynb_json(self):
        response = self.client.get(f"/api/runs/{self.run_id}/notebook")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nbformat"], 4)

    def test_missing_run_returns_404(self):
        response = self.client.get("/api/runs/not-real")

        self.assertEqual(response.status_code, 404)

    def test_upload_dataset_creates_new_run(self):
        response = self.client.post(
            "/api/datasets/upload",
            files={"file": ("fresh.csv", b"name,value\nA,1\nB,2\n", "text/csv")},
            data={"description": "Small upload test"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["source_file"], "fresh.csv")
        self.assertEqual(payload["summary"]["row_count"], 2)
        self.assertEqual(payload["summary"]["column_count"], 2)
        self.assertTrue(payload["summary"]["artifacts"]["metadata"])
        self.assertTrue(payload["summary"]["artifacts"]["dataset"])
        self.assertEqual(payload["metadata"]["source"]["type"], "upload")

        latest = self.client.get("/api/runs/latest")
        self.assertEqual(latest.json()["summary"]["source_file"], "fresh.csv")

    def test_upload_dataset_uses_core_csv_fallbacks_and_rich_metadata(self):
        response = self.client.post(
            "/api/datasets/upload",
            files={"file": ("semicolon.csv", b"name;value\nA;1\nB;2\n", "text/csv")},
            data={"description": "Semicolon upload test"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["row_count"], 2)
        self.assertEqual(payload["summary"]["column_count"], 2)
        self.assertEqual(payload["metadata"]["columns"][0]["name"], "name")
        self.assertIn("inferred_role", payload["metadata"]["columns"][0])

    def test_kaggle_import_creates_new_run_with_fetcher(self):
        def fake_kaggle_fetcher(dataset_ref: str, requested_file: str):
            return {
                "dataset_ref": dataset_ref,
                "selected_file": requested_file or "data.csv",
                "filename": "kaggle_owner_dataset_data.csv",
                "raw_bytes": b"city,sales\nParis,10\nBerlin,12\n",
                "description": "Kaggle metadata description",
                "download_path": "artifacts/kaggle_downloads/data.csv",
            }

        client = TestClient(create_app(ArtifactStore(self.root), kaggle_fetcher=fake_kaggle_fetcher))
        response = client.post(
            "/api/datasets/kaggle",
            json={
                "dataset_ref": "owner/dataset",
                "requested_file": "data.csv",
                "description": "User context",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["row_count"], 2)
        self.assertEqual(payload["metadata"]["source"]["type"], "kaggle")
        self.assertEqual(payload["metadata"]["source"]["dataset_ref"], "owner/dataset")
        self.assertIn("Kaggle metadata description", payload["metadata"]["dataset_description"])
        self.assertIn("User context", payload["metadata"]["dataset_description"])

    def test_generate_run_starts_job_and_writes_artifacts(self):
        (self.root / "datasets" / f"{self.run_id}.csv").write_text(
            "name,value\nA,1\nB,2\n",
            encoding="utf-8",
        )

        def fake_generation_runner(store, metadata, include_notebook, stage_callback, **kwargs):
            stage_callback("semantic")
            store.path_for(metadata, "semantic").write_text(
                json.dumps({"dataset_domain": "Generated"}),
                encoding="utf-8",
            )
            stage_callback("dashboard")
            store.path_for(metadata, "analysis_outputs").write_text(
                json.dumps(
                    {
                        "sample_output": {
                            "kind": "table",
                            "type": "DataFrame",
                            "columns": ["name", "value"],
                            "rows": [{"name": "A", "value": 1}],
                            "row_count": 1,
                            "truncated": False,
                        }
                    }
                ),
                encoding="utf-8",
            )
            store.path_for(metadata, "dashboard").write_text(
                json.dumps({"dashboard_title": "Generated Dashboard"}),
                encoding="utf-8",
            )
            store.path_for(metadata, "validation").write_text(
                json.dumps({"status": "passed", "issues": []}),
                encoding="utf-8",
            )
            if include_notebook:
                store.path_for(metadata, "notebook").write_text(
                    json.dumps({"nbformat": 4, "cells": []}),
                    encoding="utf-8",
                )
            return store.bundle_for(metadata)

        client = TestClient(
            create_app(
                ArtifactStore(self.root),
                generation_runner=fake_generation_runner,
            )
        )

        response = client.post(
            f"/api/runs/{self.run_id}/generate",
            json={"include_notebook": True},
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()
        status = client.get(f"/api/jobs/{job['job_id']}").json()
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["stage"], "complete")
        self.assertTrue(status["finished_at"])

        bundle = client.get(f"/api/runs/{self.run_id}").json()
        self.assertEqual(bundle["semantic_understanding"]["dataset_domain"], "Generated")
        self.assertEqual(bundle["analysis_outputs"]["sample_output"]["rows"][0]["value"], 1)
        self.assertTrue(bundle["summary"]["artifacts"]["analysis_outputs"])
        self.assertEqual(bundle["dashboard_plan"]["dashboard_title"], "Generated Dashboard")
        self.assertTrue(bundle["notebook_available"])

    def test_serialize_analysis_outputs_preserves_renderable_shapes(self):
        import pandas as pd

        payload = serialize_analysis_outputs(
            {
                "table_output": pd.DataFrame(
                    {"category": ["A", "B"], "value": [10, 20]}
                ),
                "series_output": pd.Series([3, 4], index=["x", "y"]),
                "dict_output": {"count": 2, "label": "ok"},
                "scalar_output": 42,
            }
        )

        self.assertEqual(payload["table_output"]["kind"], "table")
        self.assertEqual(payload["table_output"]["columns"], ["category", "value"])
        self.assertEqual(payload["table_output"]["rows"][1]["value"], 20)
        self.assertEqual(payload["series_output"]["kind"], "table")
        self.assertEqual(payload["dict_output"]["kind"], "mapping")
        self.assertEqual(payload["scalar_output"]["kind"], "scalar")

    def test_generation_passes_metadata_to_metric_execution_for_failed_attempt_artifacts(self):
        (self.root / "datasets" / f"{self.run_id}.csv").write_text(
            "name,value\nA,1\nB,2\n",
            encoding="utf-8",
        )
        semantic = SemanticUnderstanding(
            dataset_domain="Testing",
            primary_entities=["row"],
            important_dimensions=["name"],
            important_metrics=["value"],
            analytical_goals=["test"],
            suggested_questions=["test?"],
        )

        captured = {}

        def fake_metric_plan(*, df, semantic_understanding, df_head, metadata, **kwargs):
            captured["metadata"] = metadata
            raise ValueError("metric failure")

        with (
            patch("core.run_orchestration.generate_semantic_understanding", return_value=semantic),
            patch("core.run_orchestration.generate_executable_metric_plan", side_effect=fake_metric_plan),
        ):
            client = TestClient(create_app(ArtifactStore(self.root)))
            response = client.post(
                f"/api/runs/{self.run_id}/generate",
                json={"include_notebook": False},
            )

        self.assertEqual(response.status_code, 200)
        job = response.json()
        status = client.get(f"/api/jobs/{job['job_id']}").json()
        self.assertEqual(status["status"], "failed")
        self.assertEqual(captured["metadata"]["source_file"], self.metadata["source_file"])


if __name__ == "__main__":
    unittest.main()
