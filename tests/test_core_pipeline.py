import unittest
from unittest.mock import Mock, patch

import core.pipeline as pipeline
from contracts import DashboardCritique, DashboardValidationReport
from tests.test_agents_contracts import (
    sample_dashboard_plan,
    sample_metric_plan,
    sample_semantic,
)


class CorePipelineTests(unittest.TestCase):
    def test_passing_validation_does_not_call_critic(self):
        dashboard_plan = sample_dashboard_plan()
        passed_report = DashboardValidationReport(status="passed", issues=[])

        with (
            patch.object(pipeline, "generate_dashboard_plan", return_value=dashboard_plan) as planner,
            patch.object(pipeline, "validate_dashboard_plan", return_value=passed_report) as validator,
            patch.object(pipeline, "repair_dashboard_plan") as critic,
        ):
            result_plan, result_report, critique = pipeline.generate_validated_dashboard_plan(
                metadata={"source_file": "sample.csv"},
                semantic_understanding=sample_semantic(),
                metric_plan=sample_metric_plan(),
                analysis_outputs={"sample": 1},
                df_context="context",
            )

        self.assertIs(result_plan, dashboard_plan)
        self.assertIs(result_report, passed_report)
        self.assertIsNone(critique)
        planner.assert_called_once()
        validator.assert_called_once()
        critic.assert_not_called()

    def test_failed_validation_calls_critic_and_revalidates_repaired_plan(self):
        original_plan = sample_dashboard_plan()
        repaired_plan = sample_dashboard_plan()
        repaired_plan.dashboard_title = "Repaired Dashboard"
        failed_report = DashboardValidationReport(
            status="failed",
            issues=[],
            rejected_chart_titles=["Bad Chart"],
            rejected_kpi_titles=[],
        )
        passed_report = DashboardValidationReport(status="passed", issues=[])
        critique = DashboardCritique(
            critique_summary="Fixed weak chart.",
            repaired_dashboard_plan=repaired_plan,
            repair_notes=["Changed chart."],
            remaining_risks=[],
        )

        with (
            patch.object(pipeline, "generate_dashboard_plan", return_value=original_plan),
            patch.object(
                pipeline,
                "validate_dashboard_plan",
                side_effect=[failed_report, passed_report],
            ) as validator,
            patch.object(pipeline, "repair_dashboard_plan", return_value=critique) as critic,
        ):
            result_plan, result_report, result_critique = pipeline.generate_validated_dashboard_plan(
                metadata={"source_file": "sample.csv"},
                semantic_understanding=sample_semantic(),
                metric_plan=sample_metric_plan(),
                analysis_outputs={"sample": 1},
                df_context="context",
            )

        self.assertIs(result_plan, repaired_plan)
        self.assertIs(result_report, passed_report)
        self.assertIs(result_critique, critique)
        self.assertEqual(validator.call_count, 2)
        critic.assert_called_once()

    def test_failed_critic_repair_keeps_original_dashboard_and_validation_report(self):
        original_plan = sample_dashboard_plan()
        failed_report = DashboardValidationReport(
            status="failed",
            issues=[],
            rejected_chart_titles=["Fatigue by Intensity"],
            rejected_kpi_titles=[],
        )

        with (
            patch.object(pipeline, "generate_dashboard_plan", return_value=original_plan),
            patch.object(pipeline, "validate_dashboard_plan", return_value=failed_report),
            patch.object(pipeline, "repair_dashboard_plan", return_value={"not": "a critique"}),
        ):
            result_plan, result_report, result_critique = pipeline.generate_validated_dashboard_plan(
                metadata={"source_file": "sample.csv"},
                semantic_understanding=sample_semantic(),
                metric_plan=sample_metric_plan(),
                analysis_outputs={"sample": 1},
                df_context="context",
            )

        self.assertIs(result_plan, original_plan)
        self.assertIs(result_report, failed_report)
        self.assertIsNone(result_critique)

    def test_pipeline_validates_raw_agent_and_validator_payloads(self):
        dashboard_plan = sample_dashboard_plan()
        report = DashboardValidationReport(status="passed", issues=[])

        with (
            patch.object(pipeline, "generate_dashboard_plan", return_value=dashboard_plan.model_dump()),
            patch.object(pipeline, "validate_dashboard_plan", return_value=report.model_dump()),
            patch.object(pipeline, "repair_dashboard_plan") as critic,
        ):
            result_plan, result_report, critique = pipeline.generate_validated_dashboard_plan(
                metadata={"source_file": "sample.csv"},
                semantic_understanding=sample_semantic().model_dump(),
                metric_plan=sample_metric_plan().model_dump(),
                analysis_outputs={"sample": 1},
                df_context="context",
            )

        self.assertEqual(result_plan.dashboard_title, dashboard_plan.dashboard_title)
        self.assertEqual(result_report.status, "passed")
        self.assertIsNone(critique)
        critic.assert_not_called()


if __name__ == "__main__":
    unittest.main()
