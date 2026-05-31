import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from contracts import PandasMetricPlan
from scripts import benchmark_metric_models as benchmark
from tests.test_agents_contracts import sample_semantic


def sample_plan() -> PandasMetricPlan:
    return PandasMetricPlan(
        agent_summary="Benchmark sample",
        required_columns=["value"],
        dashboard_metrics=[],
        question_analyses=[],
        analysis_outputs=[],
        pandas_code="analysis_outputs = {'total': 3}",
        assumptions=[],
        limitations=[],
    )


class BenchmarkMetricModelsTests(unittest.TestCase):
    def test_metric_model_environment_restores_previous_values(self):
        os.environ["OPENAI_METRIC_CODE_MODEL"] = "old-code"
        os.environ.pop("OPENAI_METRIC_REPAIR_MODEL", None)

        with benchmark.metric_model_environment("new-model", 12):
            self.assertEqual(os.environ["OPENAI_METRIC_CODE_MODEL"], "new-model")
            self.assertEqual(os.environ["OPENAI_METRIC_REPAIR_MODEL"], "new-model")
            self.assertEqual(os.environ["OPENAI_TIMEOUT_SECONDS"], "12")

        self.assertEqual(os.environ["OPENAI_METRIC_CODE_MODEL"], "old-code")
        self.assertNotIn("OPENAI_METRIC_REPAIR_MODEL", os.environ)

    def test_run_single_model_benchmark_records_success(self):
        def fake_runner(**kwargs):
            return sample_plan(), {"total": 3}

        result = benchmark.run_single_model_benchmark(
            model="test-model",
            df=pd.DataFrame({"value": [1, 2]}),
            metadata={"source_file": "sample.csv", "file_sha256": "abcdef1234567890", "columns": []},
            semantic_understanding=sample_semantic(),
            df_context="context",
            max_repairs=1,
            timeout_seconds=30,
            runner=fake_runner,
        )

        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["model"], "test-model")
        self.assertEqual(result["produced_output_count"], 1)
        self.assertEqual(result["output_summaries"]["total"]["value"], 3)

    def test_run_single_model_benchmark_records_failure(self):
        def fake_runner(**kwargs):
            raise ValueError("broken")

        result = benchmark.run_single_model_benchmark(
            model="test-model",
            df=pd.DataFrame({"value": [1, 2]}),
            metadata={"source_file": "sample.csv", "file_sha256": "abcdef1234567890", "columns": []},
            semantic_understanding=sample_semantic(),
            df_context="context",
            max_repairs=1,
            timeout_seconds=None,
            runner=fake_runner,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_type"], "ValueError")
        self.assertIn("broken", result["error_message"])

    def test_write_report_creates_json_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = benchmark.write_report({"results": []}, Path(temp_dir))

            self.assertTrue(path.exists())
            self.assertTrue(path.name.endswith("_metric_model_benchmark.json"))


if __name__ == "__main__":
    unittest.main()
