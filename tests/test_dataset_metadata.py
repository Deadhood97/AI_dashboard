import unittest

import pandas as pd

from core.dataset_metadata import (
    analyze_columns,
    build_dataframe_context,
    build_dataset_metadata,
    compact_metadata_for_agent_context,
    data_integrity_summary,
    infer_column_role,
    normalize_dataset_metadata,
)


class DatasetMetadataTests(unittest.TestCase):
    def test_infers_core_column_roles(self):
        df = pd.DataFrame(
            {
                "numeric": list(range(10)),
                "boolean": [True, False] * 5,
                "categorical": ["A"] * 8 + ["B"] * 2,
                "text": [f"label-{index}" for index in range(10)],
                "temporal": pd.date_range("2026-01-01", periods=10),
            }
        )

        self.assertEqual(infer_column_role(df["numeric"]), "numeric")
        self.assertEqual(infer_column_role(df["boolean"]), "boolean")
        self.assertEqual(infer_column_role(df["categorical"]), "categorical")
        self.assertEqual(infer_column_role(df["text"]), "text")
        self.assertEqual(infer_column_role(df["temporal"]), "temporal")

    def test_analyze_columns_records_stats_nulls_samples_and_top_values(self):
        df = pd.DataFrame(
            {
                "amount": [1.0, 2.0, None],
                "segment": ["Consumer", "Consumer", "Business"],
            }
        )

        columns = {column["name"]: column for column in analyze_columns(df)}

        self.assertEqual(columns["amount"]["null_count"], 1)
        self.assertEqual(columns["amount"]["statistics"]["max"], 2.0)
        self.assertEqual(columns["segment"]["top_values"][0], {"value": "Consumer", "count": 2})
        self.assertIn("Business", columns["segment"]["unique_values"])

    def test_large_text_column_uses_representative_values(self):
        df = pd.DataFrame({"identifier": [f"id-{index:03d}" for index in range(501)]})

        column = analyze_columns(df)[0]

        self.assertNotIn("unique_values", column)
        self.assertLessEqual(len(column["representative_values"]), 40)

    def test_build_dataset_metadata_includes_stable_contract_fields(self):
        raw_bytes = b"name,value\nA,1\n"
        df = pd.DataFrame({"name": ["A"], "value": [1]})

        metadata = build_dataset_metadata(df, "sample.csv", raw_bytes, "demo data")

        self.assertEqual(metadata["source_file"], "sample.csv")
        self.assertEqual(metadata["row_count"], 1)
        self.assertEqual(metadata["column_count"], 2)
        self.assertEqual(metadata["dataset_description"], "demo data")
        self.assertEqual(metadata["schema"]["columns"], metadata["columns"])
        self.assertEqual(metadata["columns"][1]["pandas_dtype"], "int64")
        self.assertEqual(metadata["columns"][1]["dtype"], "int64")
        self.assertEqual(metadata["columns"][1]["inferred_role"], "numeric")
        self.assertEqual(len(metadata["file_sha256"]), 64)

    def test_normalizes_metadata_to_single_column_language(self):
        metadata = {
            "source_file": "legacy.csv",
            "row_count": 10,
            "column_count": 2,
            "columns": [
                {"name": "amount", "dtype": "float64", "missing_count": 2, "non_null_count": 8},
                {"name": "label", "pandas_dtype": "object", "null_count": 0, "unique_count": 3},
            ],
            "schema": {"columns": ["amount", "label"]},
        }

        normalized = normalize_dataset_metadata(metadata)

        self.assertEqual(normalized["columns"][0]["pandas_dtype"], "float64")
        self.assertEqual(normalized["columns"][0]["inferred_role"], "numeric")
        self.assertEqual(normalized["columns"][0]["null_count"], 2)
        self.assertEqual(normalized["columns"][0]["null_percentage"], 20.0)
        self.assertEqual(normalized["columns"][0]["unique_count"], 8)
        self.assertEqual(normalized["columns"][1]["dtype"], "object")
        self.assertEqual(normalized["schema"]["columns"], normalized["columns"])

    def test_dataframe_context_includes_metadata_json_and_preview_rows(self):
        df = pd.DataFrame({"name": ["A", "B"], "value": [1, 2]})
        metadata = build_dataset_metadata(df, "sample.csv", b"name,value\nA,1\nB,2\n", "demo")

        context = build_dataframe_context(metadata, df, rows=1)

        self.assertIn("Dataset context JSON:", context)
        self.assertIn('"source_file": "sample.csv"', context)
        self.assertIn("First 1 dataframe rows:", context)
        self.assertIn("| A", context)

    def test_agent_context_compacts_long_descriptions_and_unique_values(self):
        df = pd.DataFrame({"category": [f"value-{index}" for index in range(30)]})
        metadata = build_dataset_metadata(df, "sample.csv", b"raw", "x" * 3000)
        metadata["columns"][0]["unique_values"] = [f"value-{index}" for index in range(30)]

        context = compact_metadata_for_agent_context(metadata)

        self.assertLessEqual(len(context["dataset_description"]), 1600)
        self.assertEqual(len(context["columns"][0]["unique_values"]), 20)
        self.assertIn("top_values", context["columns"][0])

    def test_data_integrity_summary_counts_missing_and_duplicates(self):
        df = pd.DataFrame({"name": ["A", "A", None], "value": [1, 1, None]})

        summary = data_integrity_summary(df)

        self.assertEqual(summary["row_count"], 3)
        self.assertEqual(summary["column_count"], 2)
        self.assertEqual(summary["missing_cells"], 2)
        self.assertEqual(summary["duplicate_rows"], 1)


if __name__ == "__main__":
    unittest.main()
