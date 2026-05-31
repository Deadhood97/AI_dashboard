import importlib
import subprocess
import sys
import unittest


class CoreBoundaryTests(unittest.TestCase):
    def test_core_modules_import_without_streamlit(self):
        modules = [
            "core.config",
            "core.csv_io",
            "core.kaggle_import",
            "core.dataset_metadata",
            "core.artifacts",
            "core.metric_execution",
            "core.pipeline",
            "core.run_tracing",
            "core.run_orchestration",
        ]
        code = (
            "import importlib, sys; "
            f"modules = {modules!r}; "
            "[importlib.import_module(name) for name in modules]; "
            "assert 'streamlit' not in sys.modules, sorted(name for name in sys.modules if name == 'streamlit')"
        )

        subprocess.run([sys.executable, "-c", code], check=True)

    def test_api_import_does_not_import_streamlit_app(self):
        code = (
            "import sys; import api; "
            "assert 'app' not in sys.modules, 'api imported app.py'; "
            "assert 'streamlit' not in sys.modules, 'api imported streamlit'"
        )

        subprocess.run([sys.executable, "-c", code], check=True)

    def test_app_compatibility_reexports_still_work(self):
        app = importlib.import_module("app")

        from core.artifacts import failed_metric_plan_path_for
        from core.config import notebook_view_enabled
        from core.kaggle_import import fetch_kaggle_dataset
        from core.metric_execution import sanitize_generated_code

        self.assertIs(app.notebook_view_enabled, notebook_view_enabled)
        self.assertIs(app.fetch_kaggle_dataset, fetch_kaggle_dataset)
        self.assertIs(app.sanitize_generated_code, sanitize_generated_code)
        self.assertIs(app.failed_metric_plan_path_for, failed_metric_plan_path_for)
        self.assertTrue(callable(app.bar_plot_fields))


if __name__ == "__main__":
    unittest.main()
