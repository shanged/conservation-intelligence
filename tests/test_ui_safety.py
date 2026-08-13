"""Regression tests for visible disclosures and safe UI rendering decisions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ui_safety import (  # noqa: E402
    PRIVACY_NOTICE,
    RESEARCH_DISCLAIMER,
    answer_mode_label,
    fallback_status,
    safe_plain_text,
    safe_source_url,
)


class UISafetyTests(unittest.TestCase):
    def test_research_disclaimer_contains_required_warning(self):
        lowered = RESEARCH_DISCLAIMER.casefold()
        for phrase in ("experimental research prototype", "public conservation documents", "incomplete or incorrect", "cited source documents"):
            self.assertIn(phrase, lowered)

    def test_privacy_notice_describes_both_modes_and_no_persistence(self):
        lowered = PRIVACY_NOTICE.casefold()
        for phrase in ("question", "selected excerpts", "sent to openai", "does not intentionally persist", "do not submit confidential", "local deterministic"):
            self.assertIn(phrase, lowered)

    def test_answer_mode_and_sanitized_fallback_labels(self):
        self.assertEqual(answer_mode_label({"mode": "openai"}), "Answer mode: AI synthesis")
        self.assertEqual(answer_mode_label({"mode": "deterministic_fallback"}), "Answer mode: Local deterministic fallback")
        self.assertEqual(fallback_status({"fallback_reason": "invalid_openai_response"}), "AI output did not pass citation validation.")

    def test_unsafe_and_malformed_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "data:text/html,x", "file:///tmp/x", "https://", "not a url", "https://user:password@example.org/x"):
            with self.subTest(url=url):
                self.assertIsNone(safe_source_url(url))
        self.assertEqual(safe_source_url("https://example.org/source"), "https://example.org/source")
        self.assertEqual(safe_source_url("http://legacy.example.org/source"), "http://legacy.example.org/source")

    def test_raw_html_and_script_text_is_escaped(self):
        rendered = safe_plain_text('<script>alert("x")</script><img src=x onerror=alert(1)>')
        self.assertNotIn("<script", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_app_contains_disclosures_without_unsafe_html(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("RESEARCH_DISCLAIMER", source)
        self.assertIn("PRIVACY_NOTICE", source)
        self.assertNotIn("unsafe_allow_html=True", source)
        self.assertNotIn("st.session_state)", source)


if __name__ == "__main__":
    unittest.main()
