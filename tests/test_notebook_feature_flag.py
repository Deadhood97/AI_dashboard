import unittest
from unittest.mock import patch

from core.config import notebook_view_enabled


class NotebookFeatureFlagTests(unittest.TestCase):
    def test_notebook_view_is_disabled_by_default(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(notebook_view_enabled())

    def test_notebook_view_accepts_explicit_truthy_values(self):
        for value in ["1", "true", "yes", "on", "TRUE"]:
            with self.subTest(value=value):
                with patch.dict("os.environ", {"ENABLE_NOTEBOOK_VIEW": value}):
                    self.assertTrue(notebook_view_enabled())

    def test_notebook_view_rejects_false_values(self):
        for value in ["0", "false", "no", "off", ""]:
            with self.subTest(value=value):
                with patch.dict("os.environ", {"ENABLE_NOTEBOOK_VIEW": value}):
                    self.assertFalse(notebook_view_enabled())


if __name__ == "__main__":
    unittest.main()
