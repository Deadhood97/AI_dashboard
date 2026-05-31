import unittest
from unittest.mock import patch

from core.model_config import (
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_MODEL,
    model_for_role,
    resolve_llm_max_retries,
    resolve_llm_timeout,
)


class ModelConfigTests(unittest.TestCase):
    def test_model_for_role_prefers_explicit_then_role_then_shared_then_default(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(model_for_role("metric_code"), DEFAULT_MODEL)
            self.assertEqual(model_for_role("metric_code", "explicit-model"), "explicit-model")

        with patch.dict("os.environ", {"OPENAI_MODEL": "shared-model"}, clear=True):
            self.assertEqual(model_for_role("metric_code"), "shared-model")

        with patch.dict(
            "os.environ",
            {
                "OPENAI_MODEL": "shared-model",
                "OPENAI_METRIC_CODE_MODEL": "metric-code-model",
            },
            clear=True,
        ):
            self.assertEqual(model_for_role("metric_code"), "metric-code-model")

    def test_timeout_and_retry_env_parsing_is_bounded(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(resolve_llm_timeout(), DEFAULT_LLM_TIMEOUT_SECONDS)
            self.assertEqual(resolve_llm_max_retries(), DEFAULT_LLM_MAX_RETRIES)

        with patch.dict(
            "os.environ",
            {"OPENAI_TIMEOUT_SECONDS": "45.5", "OPENAI_MAX_RETRIES": "3"},
            clear=True,
        ):
            self.assertEqual(resolve_llm_timeout(), 45.5)
            self.assertEqual(resolve_llm_max_retries(), 3)

        with patch.dict(
            "os.environ",
            {"OPENAI_TIMEOUT_SECONDS": "-1", "OPENAI_MAX_RETRIES": "-2"},
            clear=True,
        ):
            self.assertEqual(resolve_llm_timeout(), DEFAULT_LLM_TIMEOUT_SECONDS)
            self.assertEqual(resolve_llm_max_retries(), 0)


if __name__ == "__main__":
    unittest.main()
