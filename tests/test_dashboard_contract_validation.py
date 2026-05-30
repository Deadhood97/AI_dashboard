import unittest

import pandas as pd

from agents.dashboard_planner import DashboardChartSpec
from agents.metric_code_planner import (
    AnalysisOutputSpec,
    DashboardMetricSpec,
    PandasMetricPlan,
)
from dashboard_validation import validate_chart_spec, validate_dashboard_plan


class DashboardContractValidationTests(unittest.TestCase):
    def test_wide_form_multi_line_can_use_metrics_without_y(self):
        outputs = {
            "trend": pd.DataFrame(
                {
                    "month": ["Jan", "Feb", "Mar"],
                    "fatigue": [60, 62, 63],
                    "performance": [75, 76, 78],
                }
            )
        }
        spec = DashboardChartSpec(
            title="Fatigue and Performance",
            chart_type="multi_line",
            source_output_key="trend",
            x="month",
            metrics=["fatigue", "performance"],
            rationale="Compare two metrics over time.",
        )

        issues = validate_chart_spec(spec, outputs)

        self.assertFalse([issue for issue in issues if issue.severity == "error"])

    def test_missing_wide_form_metric_is_an_error(self):
        outputs = {
            "trend": pd.DataFrame(
                {
                    "month": ["Jan", "Feb", "Mar"],
                    "fatigue": [60, 62, 63],
                }
            )
        }
        spec = DashboardChartSpec(
            title="Fatigue and Performance",
            chart_type="multi_line",
            source_output_key="trend",
            x="month",
            metrics=["fatigue", "performance"],
            rationale="Compare two metrics over time.",
        )

        issues = validate_chart_spec(spec, outputs)

        self.assertTrue(
            any("Metric column 'performance'" in issue.message for issue in issues)
        )

    def test_many_bar_categories_without_top_n_warns(self):
        outputs = {
            "ranking": pd.DataFrame(
                {
                    "category": [f"category_{index}" for index in range(30)],
                    "score": list(range(30)),
                }
            )
        }
        spec = DashboardChartSpec(
            title="Crowded Ranking",
            chart_type="bar",
            source_output_key="ranking",
            x="category",
            y="score",
            top_n=None,
            rationale="Show all categories.",
        )

        issues = validate_chart_spec(spec, outputs)

        self.assertTrue(any("many categories" in issue.message for issue in issues))

    def test_unused_metric_output_schema_drift_is_warning_not_failure(self):
        from tests.test_agents_contracts import sample_dashboard_plan

        metric_plan = PandasMetricPlan(
            agent_summary="Test metric contract drift.",
            required_columns=["group", "score"],
            dashboard_metrics=[
                DashboardMetricSpec(
                    name="Used score",
                    business_purpose="Show used score.",
                    calculation="Average score by group.",
                    output_key="used_output",
                    required_columns=["group", "score"],
                    missing_data_strategy="Drop missing rows.",
                )
            ],
            question_analyses=[],
            analysis_outputs=[
                AnalysisOutputSpec(
                    key="used_output",
                    output_type="dataframe",
                    semantic_role="categorical_comparison",
                    columns=["Training_Intensity", "Fatigue_Score"],
                    recommended_views=["bar_chart"],
                    description="Used dashboard output.",
                    render_hint="Bar chart.",
                ),
                AnalysisOutputSpec(
                    key="unused_output",
                    output_type="dataframe",
                    semantic_role="categorical_comparison",
                    columns=["wide_a", "wide_b"],
                    recommended_views=["table"],
                    description="Unused output with stale schema.",
                    render_hint="Table.",
                ),
            ],
            pandas_code="analysis_outputs = {}",
            assumptions=[],
            limitations=[],
        )
        dashboard_plan = sample_dashboard_plan()
        outputs = {
            "used_output": pd.DataFrame(
                {
                    "Training_Intensity": ["High", "Low"],
                    "Fatigue_Score": [95, 40],
                }
            ),
            "unused_output": pd.DataFrame(
                {
                    "long_name": ["wide_a", "wide_b"],
                    "value": [1, 2],
                }
            ),
        }
        dashboard_plan.kpis[0].source_output_key = "used_output"
        dashboard_plan.overview_charts[0].source_output_key = "used_output"
        dashboard_plan.question_views[0].chart.source_output_key = "used_output"

        report = validate_dashboard_plan(dashboard_plan, metric_plan, outputs)

        self.assertEqual(report.status, "passed_with_warnings")
        self.assertTrue(
            any(
                issue.component == "metric_output" and issue.severity == "warning"
                for issue in report.issues
            )
        )


if __name__ == "__main__":
    unittest.main()
