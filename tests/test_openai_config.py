"""Security and validation tests for non-networking OpenAI configuration."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from openai_config import (  # noqa: E402
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    load_openai_config,
)


FAKE_TEST_KEY = "unit-test-credential-never-use"


class OpenAIConfigurationTests(unittest.TestCase):
    def assert_safe_fallback(self, config: object) -> None:
        self.assertFalse(config.openai_available)
        self.assertTrue(config.deterministic_fallback_available)

    def test_openai_disabled(self) -> None:
        config = load_openai_config({"USE_OPENAI_CHATBOT": "false"})
        self.assert_safe_fallback(config)
        self.assertFalse(config.api_configured)
        self.assertEqual(config.safe_diagnostics(), ())

    def test_missing_api_key(self) -> None:
        config = load_openai_config({"USE_OPENAI_CHATBOT": "true"})
        self.assert_safe_fallback(config)
        self.assertFalse(config.api_configured)
        self.assertTrue(config.safe_diagnostics())

    def test_valid_looking_configuration_makes_no_request(self) -> None:
        config = load_openai_config(
            {
                "USE_OPENAI_CHATBOT": "true",
                "OPENAI_API_KEY": FAKE_TEST_KEY,
                "OPENAI_MODEL": "gpt-5.6-luna",
                "OPENAI_MAX_OUTPUT_TOKENS": "500",
                "OPENAI_REQUEST_TIMEOUT_SECONDS": "15",
                "OPENAI_MAX_RETRIES": "0",
            }
        )
        self.assertTrue(config.openai_available)
        self.assertTrue(config.api_configured)
        self.assertEqual(config.safe_diagnostics(), ())

    def test_invalid_token_limit_uses_safe_fallback(self) -> None:
        config = load_openai_config(
            {
                "USE_OPENAI_CHATBOT": "true",
                "OPENAI_API_KEY": FAKE_TEST_KEY,
                "OPENAI_MAX_OUTPUT_TOKENS": "not-an-integer",
            }
        )
        self.assert_safe_fallback(config)
        self.assertEqual(config.max_output_tokens, DEFAULT_MAX_OUTPUT_TOKENS)

    def test_invalid_timeout_uses_safe_fallback(self) -> None:
        config = load_openai_config(
            {
                "USE_OPENAI_CHATBOT": "true",
                "OPENAI_API_KEY": FAKE_TEST_KEY,
                "OPENAI_REQUEST_TIMEOUT_SECONDS": "forever",
            }
        )
        self.assert_safe_fallback(config)
        self.assertEqual(
            config.request_timeout_seconds, DEFAULT_REQUEST_TIMEOUT_SECONDS
        )

    def test_invalid_retry_count_uses_safe_fallback(self) -> None:
        config = load_openai_config(
            {
                "USE_OPENAI_CHATBOT": "true",
                "OPENAI_API_KEY": FAKE_TEST_KEY,
                "OPENAI_MAX_RETRIES": "2",
            }
        )
        self.assert_safe_fallback(config)
        self.assertEqual(config.max_retries, DEFAULT_MAX_RETRIES)

    def test_invalid_boolean_and_model_are_sanitized(self) -> None:
        config = load_openai_config(
            {
                "USE_OPENAI_CHATBOT": "sometimes",
                "OPENAI_API_KEY": FAKE_TEST_KEY,
                "OPENAI_MODEL": "invalid model value",
            }
        )
        self.assert_safe_fallback(config)
        self.assertGreaterEqual(len(config.safe_diagnostics()), 2)

    def test_secret_never_appears_in_safe_outputs(self) -> None:
        config = load_openai_config(
            {
                "USE_OPENAI_CHATBOT": "true",
                "OPENAI_API_KEY": FAKE_TEST_KEY,
                "OPENAI_MAX_OUTPUT_TOKENS": FAKE_TEST_KEY,
                "OPENAI_REQUEST_TIMEOUT_SECONDS": FAKE_TEST_KEY,
                "OPENAI_MAX_RETRIES": FAKE_TEST_KEY,
            }
        )
        exposed = " ".join(
            (
                repr(config),
                repr(config.safe_status()),
                repr(config.safe_diagnostics()),
                " ".join(config.safe_diagnostics()),
            )
        )
        self.assertNotIn(FAKE_TEST_KEY, exposed)
        self.assert_safe_fallback(config)


if __name__ == "__main__":
    unittest.main()
