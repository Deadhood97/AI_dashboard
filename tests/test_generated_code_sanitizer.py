import ast
import unittest

from app import sanitize_generated_code


class GeneratedCodeSanitizerTest(unittest.TestCase):
    def test_sanitize_generated_code_dedents_structured_output_code(self) -> None:
        code = """
            df_work = df.copy()
            analysis_outputs = {}
        """

        sanitized = sanitize_generated_code(code)

        self.assertEqual(sanitized, "df_work = df.copy()\nanalysis_outputs = {}")
        ast.parse(sanitized)

    def test_sanitize_generated_code_removes_markdown_fences_and_allowed_imports(self) -> None:
        code = """```python
        import pandas as pd
        df_work = df.copy()
        analysis_outputs = {}
        ```"""

        sanitized = sanitize_generated_code(code)

        self.assertEqual(sanitized, "df_work = df.copy()\nanalysis_outputs = {}")
        ast.parse(sanitized)


if __name__ == "__main__":
    unittest.main()
