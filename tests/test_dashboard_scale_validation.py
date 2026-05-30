import unittest

import pandas as pd

from agents.dashboard_planner import DashboardChartSpec
from dashboard_validation import validate_chart_spec


class DashboardScaleValidationTest(unittest.TestCase):
    def test_clustered_bar_chart_requires_declared_scale(self) -> None:
        chart = DashboardChartSpec(
            title="Mental Wellbeing by Group",
            chart_type="bar",
            source_output_key="wellbeing_by_group",
            x="group",
            y="score",
            rationale="Compare group averages.",
        )
        outputs = {
            "wellbeing_by_group": pd.DataFrame(
                {
                    "group": ["A", "B", "C"],
                    "score": [62.7, 63.1, 62.9],
                }
            )
        }

        issues = validate_chart_spec(chart, outputs)

        self.assertTrue(any("tightly clustered" in issue.message for issue in issues))

    def test_declared_scale_and_note_satisfy_clustered_bar_chart(self) -> None:
        chart = DashboardChartSpec(
            title="Mental Wellbeing by Group",
            chart_type="bar",
            source_output_key="wellbeing_by_group",
            x="group",
            y="score",
            value_axis_min=62.0,
            value_axis_max=64.0,
            scale_note="Axis narrowed to show small differences; it does not start at zero.",
            rationale="Compare group averages.",
        )
        outputs = {
            "wellbeing_by_group": pd.DataFrame(
                {
                    "group": ["A", "B", "C"],
                    "score": [62.7, 63.1, 62.9],
                }
            )
        }

        issues = validate_chart_spec(chart, outputs)

        self.assertFalse(any("tightly clustered" in issue.message for issue in issues))

    def test_declared_line_scale_must_not_clip_values(self) -> None:
        chart = DashboardChartSpec(
            title="Price Trend",
            chart_type="line",
            source_output_key="price_trend",
            x="month",
            y="price",
            value_axis_min=300.0,
            value_axis_max=380.0,
            scale_note="Axis narrowed to highlight variation.",
            rationale="Show price movement over time.",
        )
        outputs = {
            "price_trend": pd.DataFrame(
                {
                    "month": ["2021-01", "2021-02", "2021-03"],
                    "price": [320.0, 375.0, 581.0],
                }
            )
        }

        issues = validate_chart_spec(chart, outputs)

        self.assertTrue(any("clips data values" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
