import json
import tempfile
import unittest
from pathlib import Path

import nbformat
import pandas as pd

from notebook_export import build_dashboard_notebook, write_dashboard_notebook
from tests.test_agents_contracts import (
    sample_dashboard_plan,
    sample_insights,
    sample_metric_plan,
    sample_semantic,
    sample_validation_report,
)


class NotebookExportTests(unittest.TestCase):
    def test_build_dashboard_notebook_includes_pipeline_sections_and_outputs(self):
        notebook = build_dashboard_notebook(
            metadata={
                "source_file": "athletes.csv",
                "file_sha256": "abc123",
                "row_count": 2,
                "column_count": 2,
            },
            semantic_understanding=sample_semantic(),
            metric_plan=sample_metric_plan(),
            analysis_outputs={
                "fatigue_by_intensity": pd.DataFrame(
                    {
                        "Training_Intensity": ["High", "Low"],
                        "Fatigue_Score": [62.1, 61.8],
                    }
                ),
                "missing_counts": pd.Series([0, 1], index=["Age", "Gender"]),
                "scalar_score": 0.42,
            },
            dashboard_plan=sample_dashboard_plan(),
            validation_report=sample_validation_report(),
            critique=None,
            analytical_insights=sample_insights(),
            df_preview=pd.DataFrame(
                {
                    "Training_Intensity": ["High", "Low"],
                    "Fatigue_Score": [62.1, 61.8],
                }
            ),
            artifact_paths={"metric_plan": "artifacts/metric_plans/test.json"},
        )

        nbformat.validate(notebook)
        sources = "\n".join("".join(cell.source) for cell in notebook.cells)

        self.assertIn("Dataset Context", sources)
        self.assertIn("Compact Metadata", sources)
        self.assertIn("Semantic Understanding", sources)
        self.assertIn("Metric Plan", sources)
        self.assertIn("Executed Metric Outputs", sources)
        self.assertIn("Dashboard Plan", sources)
        self.assertIn("Analytical Brain", sources)
        self.assertIn("analysis_outputs['fatigue_by_intensity']", sources)
        self.assertIn("analysis_outputs['missing_counts']", sources)
        self.assertIn("analysis_outputs['scalar_score']", sources)
        self.assertNotIn("unique_values", sources)

    def test_write_dashboard_notebook_creates_renderable_ipynb(self):
        notebook = build_dashboard_notebook(
            metadata={"source_file": "athletes.csv", "file_sha256": "abc123"},
            semantic_understanding=sample_semantic(),
            metric_plan=sample_metric_plan(),
            analysis_outputs={"scalar_score": 0.42},
            dashboard_plan=sample_dashboard_plan(),
            validation_report=sample_validation_report(),
            critique=None,
            analytical_insights=None,
            df_preview=pd.DataFrame({"score": [1, 2]}),
            artifact_paths={},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_dashboard_notebook(Path(temp_dir) / "analysis.ipynb", notebook)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["nbformat"], 4)
        self.assertGreater(len(payload["cells"]), 5)


if __name__ == "__main__":
    unittest.main()
