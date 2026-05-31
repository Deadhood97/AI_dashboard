import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from contracts import DashboardPlan, DashboardValidationReport
from scripts import benchmark_dashboard_models as benchmark
from tests.test_agents_contracts import sample_dashboard_plan, sample_metric_plan, sample_semantic


class BenchmarkDashboardModelsTests(unittest.TestCase):
    def test_dashboard_model_environment_restores_previous_values(self):
        os.environ["OPENAI_DASHBOARD_MODEL"] = "old-dashboard"
        os.environ.pop("OPENAI_DASHBOARD_CRITIC_MODEL", None)

        with benchmark.dashboard_model_environment("new-dashboard", 33):
            self.assertEqual(os.environ["OPENAI_DASHBOARD_MODEL"], "new-dashboard")
            self.assertEqual(os.environ["OPENAI_DASHBOARD_CRITIC_MODEL"], "new-dashboard")
            self.assertEqual(os.environ["OPENAI_TIMEOUT_SECONDS"], "33")

        self.assertEqual(os.environ["OPENAI_DASHBOARD_MODEL"], "old-dashboard")
        self.assertNotIn("OPENAI_DASHBOARD_CRITIC_MODEL", os.environ)

    def test_deserialize_analysis_outputs_restores_tables(self):
        outputs = benchmark.deserialize_analysis_outputs(
            {
                "table": {
                    "kind": "table",
                    "columns": ["name", "value"],
                    "rows": [{"name": "A", "value": 1}],
                },
                "scalar": {"kind": "scalar", "value": 3},
                "mapping": {"kind": "mapping", "value": {"ok": True}},
            }
        )

        self.assertIsInstance(outputs["table"], pd.DataFrame)
        self.assertEqual(outputs["table"].iloc[0]["value"], 1)
        self.assertEqual(outputs["scalar"], 3)
        self.assertEqual(outputs["mapping"], {"ok": True})

    def test_run_single_model_benchmark_records_success(self):
        def fake_runner(**kwargs):
            return (
                sample_dashboard_plan(),
                DashboardValidationReport(status="passed", issues=[], rejected_chart_titles=[], rejected_kpi_titles=[]),
                None,
            )

        result = benchmark.run_single_model_benchmark(
            model="test-model",
            metadata={"source_file": "sample.csv", "file_sha256": "abcdef1234567890", "columns": []},
            semantic_understanding=sample_semantic(),
            metric_plan=sample_metric_plan(),
            analysis_outputs={"fatigue_by_intensity": pd.DataFrame({"Training_Intensity": ["High"], "Fatigue_Score": [80]})},
            df_context="context",
            max_repairs=1,
            timeout_seconds=20,
            runner=fake_runner,
        )

        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["dashboard"]["validation"]["status"], "passed")
        self.assertEqual(result["dashboard"]["overview_chart_count"], 1)

    def test_run_single_model_benchmark_records_failure(self):
        def fake_runner(**kwargs):
            raise RuntimeError("dashboard broke")

        result = benchmark.run_single_model_benchmark(
            model="test-model",
            metadata={"source_file": "sample.csv", "file_sha256": "abcdef1234567890", "columns": []},
            semantic_understanding=sample_semantic(),
            metric_plan=sample_metric_plan(),
            analysis_outputs={},
            df_context="context",
            max_repairs=1,
            timeout_seconds=None,
            runner=fake_runner,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_type"], "RuntimeError")

    def test_write_report_creates_json_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = benchmark.write_report({"results": []}, Path(temp_dir))

            self.assertTrue(path.exists())
            self.assertTrue(path.name.endswith("_dashboard_model_benchmark.json"))


if __name__ == "__main__":
    unittest.main()
