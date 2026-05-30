import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api import ArtifactStore, create_app, run_id_for


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "artifacts"
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

    def test_run_notebook_endpoint_returns_ipynb_json(self):
        response = self.client.get(f"/api/runs/{self.run_id}/notebook")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nbformat"], 4)

    def test_missing_run_returns_404(self):
        response = self.client.get("/api/runs/not-real")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
