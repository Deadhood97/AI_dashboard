import unittest

import pandas as pd

from agents.analytical_brain import compact_analysis_outputs as compact_for_insights
from agents.dashboard_critic import compact_analysis_outputs as compact_for_critic


class AnalysisOutputCompactionTests(unittest.TestCase):
    def test_dashboard_critic_compacts_series_outputs(self):
        compacted = compact_for_critic(
            {"scores": pd.Series([10, 12], index=["a", "b"])}
        )

        self.assertEqual(compacted["scores"]["type"], "Series")
        self.assertEqual(compacted["scores"]["sample"], {"a": 10, "b": 12})

    def test_analytical_brain_compacts_series_outputs(self):
        compacted = compact_for_insights(
            {"scores": pd.Series([10, 12], index=["a", "b"])}
        )

        self.assertEqual(compacted["scores"]["type"], "Series")
        self.assertEqual(compacted["scores"]["sample"], {"a": 10, "b": 12})

    def test_dataframe_outputs_still_use_record_samples(self):
        compacted = compact_for_critic(
            {"table": pd.DataFrame({"group": ["a", "b"], "score": [10, 12]})}
        )

        self.assertEqual(compacted["table"]["type"], "DataFrame")
        self.assertEqual(
            compacted["table"]["sample"],
            [{"group": "a", "score": 10}, {"group": "b", "score": 12}],
        )


if __name__ == "__main__":
    unittest.main()
