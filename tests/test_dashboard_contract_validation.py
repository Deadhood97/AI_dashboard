import unittest

import pandas as pd

from contracts.dashboard import DashboardChartSpec, DashboardPlan
from contracts.metrics import (
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
                    "fatigue": [40, 62, 85],
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

    def test_chart_spec_raw_payload_is_validated_before_validation(self):
        outputs = {
            "trend": pd.DataFrame(
                {
                    "month": ["Jan", "Feb", "Mar"],
                    "fatigue": [40, 62, 85],
                }
            )
        }
        spec = {
            "title": "Fatigue Trend",
            "chart_type": "line",
            "source_output_key": "trend",
            "x": "month",
            "y": "fatigue",
            "rationale": "Show fatigue over time.",
        }

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

    def test_bar_chart_rejects_unrepresented_extra_categorical_dimension(self):
        metric_plan = PandasMetricPlan(
            dashboard_metrics=[],
            question_analyses=[],
            analysis_outputs=[
                AnalysisOutputSpec(
                    key="outcome_by_weight_location",
                    output_type="dataframe",
                    semantic_role="categorical_comparison",
                    columns=["weight_class", "event_location", "method", "proportion"],
                    recommended_views=["bar_chart"],
                    description="Outcome proportions by weight class, event location, and method.",
                    render_hint="Use a table or aggregate one categorical dimension before charting.",
                )
            ],
            agent_summary="Test mixed-grain chart validation.",
            required_columns=["weight_class", "event_location", "method"],
            assumptions=[],
            limitations=[],
            pandas_code="analysis_outputs = {}",
        )
        plan = DashboardPlan(
            dashboard_title="Fight dashboard",
            dashboard_summary="Summary",
            data_integrity_notes=[],
            kpis=[],
            overview_charts=[
                DashboardChartSpec(
                    title="Outcome Distribution",
                    chart_type="bar",
                    source_output_key="outcome_by_weight_location",
                    x="weight_class",
                    y="proportion",
                    color="method",
                    top_n=12,
                    rationale="Compare outcomes.",
                )
            ],
            question_views=[],
            assumptions=[],
            limitations=[],
        )
        outputs = {
            "outcome_by_weight_location": pd.DataFrame(
                {
                    "weight_class": ["Bantamweight", "Bantamweight", "Lightweight", "Lightweight"],
                    "event_location": ["Abu Dhabi", "London", "Abu Dhabi", "London"],
                    "method": ["Decision", "Decision", "KO/TKO", "KO/TKO"],
                    "proportion": [0.5, 0.6, 0.4, 0.3],
                }
            )
        }

        report = validate_dashboard_plan(plan, metric_plan, outputs)

        self.assertEqual(report.status, "failed")
        self.assertIn("Outcome Distribution", report.rejected_chart_titles)
        self.assertIn("event_location", report.issues[0].message)

    def test_metric_output_column_validation_tolerates_spacing_and_underscores(self):
        from tests.test_agents_contracts import sample_dashboard_plan

        metric_plan = PandasMetricPlan(
            agent_summary="Test normalized output columns.",
            required_columns=["region", "sales"],
            dashboard_metrics=[
                DashboardMetricSpec(
                    name="Sales by region",
                    business_purpose="Compare regions.",
                    calculation="Sum sales by region.",
                    output_key="sales_by_region",
                    required_columns=["region", "sales"],
                    missing_data_strategy="Drop missing rows.",
                )
            ],
            question_analyses=[],
            analysis_outputs=[
                AnalysisOutputSpec(
                    key="sales_by_region",
                    output_type="dataframe",
                    semantic_role="ranked_table",
                    columns=["Region", "Order Count", "Average Sales"],
                    recommended_views=["table"],
                    description="Region sales.",
                    render_hint="Table.",
                )
            ],
            pandas_code="analysis_outputs = {}",
            assumptions=[],
            limitations=[],
        )
        dashboard_plan = sample_dashboard_plan()
        dashboard_plan.kpis[0].source_output_key = "sales_by_region"
        dashboard_plan.overview_charts[0].source_output_key = "sales_by_region"
        dashboard_plan.question_views[0].chart.source_output_key = "sales_by_region"
        dashboard_plan.overview_charts[0].chart_type = "table"
        dashboard_plan.question_views[0].chart.chart_type = "table"
        outputs = {
            "sales_by_region": pd.DataFrame(
                {
                    "Region": ["West"],
                    "Order_Count": [10],
                    "Average_Sales": [123.45],
                }
            )
        }

        report = validate_dashboard_plan(dashboard_plan, metric_plan, outputs)

        self.assertFalse(
            [
                issue
                for issue in report.issues
                if issue.component == "metric_output" and issue.severity == "error"
            ]
        )


if __name__ == "__main__":
    unittest.main()
