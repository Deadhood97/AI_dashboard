import unittest

from agents.dashboard_planner import DashboardChartSpec
from app import bar_plot_fields


class ChartRenderingContractTests(unittest.TestCase):
    def test_horizontal_bar_uses_numeric_x_and_category_y_from_spec(self):
        spec = DashboardChartSpec(
            title="Top Communities by Avg Rental Price",
            chart_type="bar",
            source_output_key="top_communities_by_rental_price",
            x="avg_rental_price_per_sqft_annual_usd",
            y="community",
            orientation="horizontal",
            rationale="Rank communities by rental price.",
        )

        plot_x, plot_y = bar_plot_fields(spec, spec.x, spec.y)

        self.assertEqual(plot_x, "avg_rental_price_per_sqft_annual_usd")
        self.assertEqual(plot_y, "community")


if __name__ == "__main__":
    unittest.main()
