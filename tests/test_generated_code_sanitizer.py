import ast
import unittest

from core.metric_execution import sanitize_generated_code


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

    def test_dangling_else_still_fails_ast_parse_for_repair_loop(self) -> None:
        code = """
        analysis_outputs = {}
        else:
            analysis_outputs['x'] = 1
        """

        sanitized = sanitize_generated_code(code)

        with self.assertRaises(SyntaxError):
            ast.parse(sanitized)


if __name__ == "__main__":
    unittest.main()
