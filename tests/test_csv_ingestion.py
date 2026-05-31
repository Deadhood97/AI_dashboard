import unittest

from core.csv_io import make_named_bytes_file, read_csv_with_fallbacks


class CsvIngestionTests(unittest.TestCase):
    def test_valid_comma_csv_parses_with_default_parser(self):
        file_obj = make_named_bytes_file(b"name,value\nA,1\nB,2\n", "sample.csv")

        df, parser = read_csv_with_fallbacks(file_obj)

        self.assertEqual(parser, "default pandas C parser")
        self.assertEqual(df.shape, (2, 2))

    def test_semicolon_csv_parses_with_fallback_parser(self):
        file_obj = make_named_bytes_file(b"name;value\nA;1\nB;2\n", "sample.csv")

        df, parser = read_csv_with_fallbacks(file_obj)

        self.assertEqual(parser, "python parser with inferred delimiter")
        self.assertEqual(list(df.columns), ["name", "value"])

    def test_malformed_rows_are_handled_by_fallback_parser(self):
        file_obj = make_named_bytes_file(b"name,value\nA,1\nB,2,extra\nC,3\n", "sample.csv")

        df, parser = read_csv_with_fallbacks(file_obj)

        self.assertEqual(parser, "python parser skipping malformed rows")
        self.assertEqual(df["name"].tolist(), ["A", "C"])

    def test_invalid_csv_raises_clear_value_error(self):
        file_obj = make_named_bytes_file(b"", "broken.csv")

        with self.assertRaisesRegex(ValueError, "Could not parse the CSV"):
            read_csv_with_fallbacks(file_obj)

    def test_make_named_bytes_file_preserves_bytes_and_filename(self):
        file_obj = make_named_bytes_file(b"a,b\n1,2\n", "named.csv")

        self.assertEqual(file_obj.name, "named.csv")
        self.assertEqual(file_obj.read(), b"a,b\n1,2\n")


if __name__ == "__main__":
    unittest.main()
