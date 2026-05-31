import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

import core.metric_execution as metric_execution
from contracts import PandasMetricPlan
from tests.test_agents_contracts import sample_semantic


def metric_plan_with_code(code: str) -> PandasMetricPlan:
    return PandasMetricPlan(
        agent_summary="Test plan",
        required_columns=["value"],
        dashboard_metrics=[],
        question_analyses=[],
        analysis_outputs=[],
        pandas_code=code,
        assumptions=[],
        limitations=[],
    )


class MetricExecutionTests(unittest.TestCase):
    def test_validate_generated_code_blocks_unsafe_constructs(self):
        unsafe_snippets = [
            "import os\nanalysis_outputs = {}",
            "analysis_outputs = open('x')",
            "analysis_outputs = df.__class__",
            "analysis_outputs = os.environ",
            "while True:\n    pass\nanalysis_outputs = {}",
        ]

        for snippet in unsafe_snippets:
            with self.subTest(snippet=snippet):
                with self.assertRaises((ValueError, SyntaxError)):
                    metric_execution.validate_generated_code(snippet)

    def test_safe_generated_code_executes_and_returns_analysis_outputs(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        plan = metric_plan_with_code("analysis_outputs = {'total': int(df['value'].sum())}")

        outputs = metric_execution.execute_metric_plan(df, plan)

        self.assertEqual(outputs, {"total": 6})

    def test_missing_or_non_dict_analysis_outputs_raises(self):
        df = pd.DataFrame({"value": [1]})

        with self.assertRaisesRegex(ValueError, "analysis_outputs"):
            metric_execution.execute_metric_plan(df, metric_plan_with_code("result = 1"))

        with self.assertRaisesRegex(ValueError, "analysis_outputs"):
            metric_execution.execute_metric_plan(df, metric_plan_with_code("analysis_outputs = []"))

    def test_repair_loop_calls_repair_agent_after_execution_failure(self):
        bad_plan = metric_plan_with_code("raise ValueError('broken')").model_dump()
        fixed_plan = metric_plan_with_code("analysis_outputs = {'ok': 1}").model_dump()

        with (
            patch.object(metric_execution, "generate_metric_code_plan", return_value=bad_plan),
            patch.object(metric_execution, "repair_metric_code_plan", return_value=fixed_plan) as repair_mock,
        ):
            plan, outputs = metric_execution.generate_executable_metric_plan(
                df=pd.DataFrame({"value": [1]}),
                semantic_understanding=sample_semantic(),
                df_head="context",
                max_repairs=1,
            )

        self.assertIsInstance(plan, PandasMetricPlan)
        self.assertEqual(outputs, {"ok": 1})
        repair_mock.assert_called_once()

    def test_final_failed_repair_raises_and_persists_attempts_when_metadata_is_provided(self):
        bad_plan = metric_plan_with_code("raise ValueError('still broken')")
        metadata = {"source_file": "sample.csv", "file_sha256": "abcdef1234567890"}

        with tempfile.TemporaryDirectory() as temp_dir:
            def fake_save_failed_metric_plan(metadata_arg, metric_plan, error_message, sanitized_code):
                path = Path(temp_dir) / f"failed-{len(list(Path(temp_dir).glob('*')))}.json"
                path.write_text(error_message, encoding="utf-8")
                return path

            with (
                patch.object(metric_execution, "generate_metric_code_plan", return_value=bad_plan),
                patch.object(metric_execution, "repair_metric_code_plan", return_value=bad_plan),
                patch.object(
                    metric_execution,
                    "save_failed_metric_plan",
                    side_effect=fake_save_failed_metric_plan,
                ) as save_mock,
            ):
                with self.assertRaisesRegex(ValueError, "still broken"):
                    metric_execution.generate_executable_metric_plan(
                        df=pd.DataFrame({"value": [1]}),
                        semantic_understanding=sample_semantic(),
                        df_head="context",
                        metadata=metadata,
                        max_repairs=1,
                    )

        self.assertEqual(save_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
