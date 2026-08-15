"""Tests for SQLite-backed citation integrity and trusted source rendering."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from citation_validation import (  # noqa: E402
    INSUFFICIENT_ANSWER,
    CitationValidationError,
    EvidenceRecord,
    is_safe_source_url,
    validate_and_render_model_answer,
)


class CitationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.database = Path(cls.tempdir.name) / "citations.db"
        connection = sqlite3.connect(cls.database)
        connection.executescript(
            """
            CREATE TABLE documents (doc_id TEXT PRIMARY KEY, title TEXT, url TEXT);
            CREATE TABLE chunks (chunk_id TEXT PRIMARY KEY, doc_id TEXT, page TEXT, chunk_text TEXT, source_url TEXT);
            INSERT INTO documents VALUES ('DOC012', 'Science Plan', 'https://trusted.invalid/plan');
            INSERT INTO documents VALUES ('DOC023', 'Wetland Website', 'https://trusted.invalid/web');
            INSERT INTO chunks VALUES ('C12A', 'DOC012', '25-26', 'Restoration programs improve wetland habitat.', 'https://trusted.invalid/plan');
            INSERT INTO chunks VALUES ('C12B', 'DOC012', '25-26', 'Monitoring measures changes in wetland condition.', 'https://trusted.invalid/plan');
            INSERT INTO chunks VALUES ('C23A', 'DOC023', 'Web', 'Regional agencies publish wetland assessments.', 'https://trusted.invalid/web');
            """
        )
        connection.commit()
        connection.close()
        cls.records = (
            EvidenceRecord("E1", "C12A", "DOC012", "Science Plan", "25-26", "https://trusted.invalid/plan", "Restoration programs improve wetland habitat.", 0.92),
            EvidenceRecord("E2", "C23A", "DOC023", "Wetland Website", "Web", "https://trusted.invalid/web", "Regional agencies publish wetland assessments.", 0.88),
            EvidenceRecord("E3", "C12B", "DOC012", "Science Plan", "25-26", "https://trusted.invalid/plan", "Monitoring measures changes in wetland condition.", 0.84),
        )

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def validate(self, answer: str, records=None):
        return validate_and_render_model_answer(
            answer, records or self.records, database_path=self.database
        )

    def assert_rejected(self, answer: str, records=None):
        with self.assertRaises(CitationValidationError):
            self.validate(answer, records)

    def test_valid_single_reference_is_rendered_locally(self):
        result = self.validate("Restoration programs improve habitat [E1].")
        self.assertEqual(result.answer, "Restoration programs improve habitat [DOC012, pp. 25–26].")
        self.assertEqual(result.citations, ("[DOC012, pp. 25–26]",))
        self.assertEqual(result.sources[0].chunk_id, "C12A")

    def test_multiple_references_preserve_claim_placement(self):
        result = self.validate(
            "Restoration improves habitat [E1]. Regional agencies publish assessments [E2]."
        )
        self.assertIn("habitat [DOC012, pp. 25–26]", result.answer)
        self.assertIn("assessments [DOC023, Web]", result.answer)
        self.assertEqual(len(result.sources), 2)

    def test_unknown_and_malformed_references_are_rejected(self):
        for answer in ("A claim has support [E99].", "A claim has support [Eabc].", "A claim cites E1."):
            with self.subTest(answer=answer):
                self.assert_rejected(answer)

    def test_model_created_source_metadata_is_rejected(self):
        for answer in (
            "A claim [DOC012, p. 25].",
            "A claim occurs on page 999 [E1].",
            "A claim [E1]. Source: https://attacker.invalid",
            "A claim [E1](javascript:alert(1)).",
        ):
            with self.subTest(answer=answer):
                self.assert_rejected(answer)

    def test_wrong_document_chunk_location_url_title_and_excerpt_are_rejected(self):
        mutations = (
            replace(self.records[0], doc_id="DOC023"),
            replace(self.records[0], location="999"),
            replace(self.records[0], source_url="https://attacker.invalid"),
            replace(self.records[0], title="Invented title"),
            replace(self.records[0], excerpt="Invented evidence sentence."),
        )
        for record in mutations:
            with self.subTest(record=record):
                self.assert_rejected("Restoration supports habitat [E1].", (record,))

    def test_duplicate_ids_and_same_source_records_are_safely_deduplicated(self):
        result = self.validate("Restoration [E1] and monitoring [E3] support wetlands [E1].")
        self.assertEqual(result.citations, ("[DOC012, pp. 25–26]",))
        self.assertEqual(len(result.sources), 1)
        duplicate_mapping = (self.records[0], replace(self.records[1], evidence_id="E1"))
        self.assert_rejected("Restoration supports habitat [E1].", duplicate_mapping)

    def test_factual_answer_without_references_is_rejected(self):
        self.assert_rejected("Wetland restoration improves habitat.")
        self.assert_rejected("Restoration improves habitat. Monitoring tracks change [E1].")

    def test_insufficient_answer_without_references_is_valid(self):
        result = self.validate(INSUFFICIENT_ANSWER)
        self.assertTrue(result.insufficient)
        self.assertEqual(result.citations, ())
        self.assertEqual(result.sources, ())

    def test_multi_document_claim_requires_multiple_documents(self):
        self.assert_rejected("Across the corpus, restoration supports habitat [E1].")
        result = self.validate("Across the corpus, restoration and assessment are themes [E1][E2].")
        self.assertEqual(len(result.sources), 2)

    def test_trusted_local_aggregate_can_validate_multi_document_claim(self):
        result = validate_and_render_model_answer(
            "Across the corpus, restoration was counted in multiple documents [E1].",
            self.records,
            database_path=self.database,
            trusted_multi_document_claims=True,
        )
        self.assertIn("[DOC012, pp. 25–26]", result.answer)

    def test_unsafe_source_schemes_never_validate(self):
        for url in ("javascript:alert(1)", "data:text/plain,x", "file:///tmp/x"):
            self.assertFalse(is_safe_source_url(url))
            self.assert_rejected(
                "Restoration supports habitat [E1].",
                (replace(self.records[0], source_url=url),),
            )


if __name__ == "__main__":
    unittest.main()
