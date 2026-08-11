"""Regression tests for deterministic chatbot evidence quality and synthesis."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from chatbot import answer_question, best_sentence, validate_response  # noqa: E402


WETLAND_SUMMARY = "Generate a short cited summary of wetland conservation evidence in the corpus."


class EvidenceQualityTests(unittest.TestCase):
    def test_rejects_table_of_contents_and_species_lists(self) -> None:
        contents = "Memorial Wetlands 135 Forested Swamp 136 Case Study 137 Literature Cited 140 Conservation Overview 141…"
        species = "97 species including: American black duck, Blue-winged teal, Ruddy duck, Glossy ibis, Yellow rail, Sedge wren, Queen snake."
        self.assertEqual(best_sentence(contents, WETLAND_SUMMARY), "")
        self.assertEqual(best_sentence(species, WETLAND_SUMMARY), "")

    def test_wetland_summary_is_synthesized_and_cited(self) -> None:
        response = answer_question(WETLAND_SUMMARY)
        valid, notes = validate_response(response)

        self.assertTrue(valid, notes)
        self.assertFalse(response.insufficient)
        self.assertGreaterEqual(len(response.citations), 2)
        self.assertRegex(response.answer.casefold(), r"wetland conservation|wetland protection")
        self.assertNotIn("Memorial Wetlands 135", response.answer)
        self.assertNotRegex(response.answer, r"American black duck|Blue-winged teal|Ruddy duck")
        self.assertNotRegex(response.answer, r"\.\.\.|…")

        bullets = [line for line in response.answer.splitlines() if line.startswith("- ")]
        self.assertGreaterEqual(len(bullets), 3)
        self.assertLessEqual(len(bullets), 5)
        for bullet in bullets:
            self.assertRegex(bullet, r"[.!?] \[DOC\d{3}, (?:Web|p\. \d+|pp\. \d+[–-]\d+)\]$")


if __name__ == "__main__":
    unittest.main()
