import unittest

from app import failed_metric_plan_path_for


class ArtifactPathTests(unittest.TestCase):
    def test_failed_metric_plan_paths_are_unique_for_fast_retries(self):
        metadata = {
            "source_file": "example.csv",
            "file_sha256": "1234567890abcdef",
        }

        paths = {failed_metric_plan_path_for(metadata).name for _ in range(5)}

        self.assertEqual(len(paths), 5)


if __name__ == "__main__":
    unittest.main()
