import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import core.artifacts as artifacts
from tests.test_agents_contracts import (
    sample_dashboard_plan,
    sample_insights,
    sample_metric_plan,
    sample_semantic,
    sample_validation_report,
)


class CoreArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.patches = [
            patch.object(artifacts, "METADATA_DIR", self.root / "metadata"),
            patch.object(artifacts, "LATEST_METADATA_PATH", self.root / "metadata" / "latest_metadata.json"),
            patch.object(artifacts, "METADATA_INDEX_PATH", self.root / "metadata" / "metadata_index.json"),
            patch.object(artifacts, "DATASET_DIR", self.root / "datasets"),
            patch.object(artifacts, "SEMANTIC_DIR", self.root / "semantic"),
            patch.object(artifacts, "METRIC_PLAN_DIR", self.root / "metric_plans"),
            patch.object(artifacts, "DASHBOARD_DIR", self.root / "dashboard"),
            patch.object(artifacts, "CRITIQUE_DIR", self.root / "critiques"),
            patch.object(artifacts, "INSIGHTS_DIR", self.root / "insights"),
            patch.object(artifacts, "NOTEBOOK_DIR", self.root / "notebooks"),
            patch.object(artifacts, "TRACE_DIR", self.root / "traces"),
        ]
        for patcher in self.patches:
            patcher.start()

        self.metadata = {
            "source_file": "Sample Dataset.csv",
            "file_sha256": "abcdef1234567890",
            "created_at": "2026-05-31T00:00:00+00:00",
            "row_count": 2,
            "column_count": 2,
        }

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp_dir.cleanup()

    def test_artifact_path_builders_are_stable_and_platform_neutral(self):
        paths = [
            artifacts.dataset_path_for(self.metadata),
            artifacts.metadata_path_for(self.metadata),
            artifacts.semantic_path_for(self.metadata),
            artifacts.metric_plan_path_for(self.metadata),
            artifacts.dashboard_path_for(self.metadata),
            artifacts.dashboard_validation_path_for(self.metadata),
            artifacts.dashboard_critique_path_for(self.metadata),
            artifacts.insights_path_for(self.metadata),
            artifacts.notebook_path_for(self.metadata),
            artifacts.trace_path_for(self.metadata),
        ]

        self.assertTrue(all(isinstance(path, Path) for path in paths))
        self.assertEqual(paths[0].name, "sample-dataset_abcdef123456.csv")
        self.assertEqual(paths[-2].suffix, ".ipynb")
        self.assertEqual(paths[-1].name, "sample-dataset_abcdef123456_trace.json")

    def test_save_metadata_updates_latest_and_deduplicated_index(self):
        artifacts.save_metadata(self.metadata)
        artifacts.save_metadata(self.metadata)

        latest = json.loads(artifacts.LATEST_METADATA_PATH.read_text(encoding="utf-8"))
        index = json.loads(artifacts.METADATA_INDEX_PATH.read_text(encoding="utf-8"))

        self.assertEqual(latest["source_file"], "Sample Dataset.csv")
        self.assertEqual(len(index), 1)

    def test_save_uploaded_dataset_writes_expected_bytes(self):
        path = artifacts.save_uploaded_dataset(self.metadata, b"a,b\n1,2\n")

        self.assertEqual(path.read_bytes(), b"a,b\n1,2\n")
        self.assertEqual(path.parent.name, "datasets")

    def test_model_save_helpers_write_valid_json(self):
        semantic_path = artifacts.save_semantic_understanding(self.metadata, sample_semantic())
        metric_path = artifacts.save_metric_plan(self.metadata, sample_metric_plan())
        dashboard_path = artifacts.save_dashboard_plan(self.metadata, sample_dashboard_plan())
        validation_path = artifacts.save_dashboard_validation_report(self.metadata, sample_validation_report())
        insights_path = artifacts.save_analytical_insights(self.metadata, sample_insights())

        for path in [semantic_path, metric_path, dashboard_path, validation_path, insights_path]:
            self.assertTrue(path.exists())
            self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)

    def test_failed_metric_plan_and_notebook_helpers_write_artifacts(self):
        failed_path = artifacts.save_failed_metric_plan(
            self.metadata,
            sample_metric_plan(),
            "ValueError: broken",
            "analysis_outputs = {}",
        )
        notebook_path = artifacts.save_dashboard_notebook_artifact(
            metadata=self.metadata,
            semantic_understanding=sample_semantic(),
            metric_plan=sample_metric_plan(),
            analysis_outputs={"sample": pd.DataFrame({"value": [1]})},
            dashboard_plan=sample_dashboard_plan(),
            validation_report=sample_validation_report(),
            critique=None,
            analytical_insights=sample_insights(),
            df_preview=pd.DataFrame({"value": [1]}),
            artifact_paths={"metadata": artifacts.metadata_path_for(self.metadata)},
        )

        self.assertIn("failed_metric_plan", failed_path.name)
        self.assertTrue(notebook_path.exists())
        self.assertEqual(json.loads(notebook_path.read_text(encoding="utf-8"))["nbformat"], 4)


if __name__ == "__main__":
    unittest.main()
