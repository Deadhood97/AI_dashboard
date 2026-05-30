import unittest

import pandas as pd

from agents.dashboard_planner import DashboardChartSpec
from dashboard_validation import validate_chart_spec


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


if __name__ == "__main__":
    unittest.main()
