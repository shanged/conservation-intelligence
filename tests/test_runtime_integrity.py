"""Verify representative runtime reads never mutate canonical artifacts."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from runtime_artifacts import (  # noqa: E402
    RuntimeArtifactPreparationError,
    _create_disposable_vector_index,
)
from sqlite_readonly import connect_readonly  # noqa: E402


class RuntimeIntegrityTests(unittest.TestCase):
    def protected_hashes(self) -> dict[str, str]:
        paths = [
            path
            for path in (ROOT / "deployment_artifacts").rglob("*")
            if path.is_file()
        ]
        paths.extend(sorted((ROOT / "wiki").rglob("*.md")))
        paths.append(ROOT / "outputs" / "demo_answers.json")
        return {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
        }

    def test_representative_runtime_operations_preserve_artifacts(self) -> None:
        before = self.protected_hashes()
        environment = os.environ.copy()
        environment["CONSERVATION_ARTIFACT_ROOT"] = str(
            ROOT / "deployment_artifacts"
        )
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        for name in (
            "OPENAI_API_KEY",
            "USE_OPENAI_CHATBOT",
            "OPENAI_MODEL",
            "OPENAI_MAX_OUTPUT_TOKENS",
            "OPENAI_REQUEST_TIMEOUT_SECONDS",
            "OPENAI_MAX_RETRIES",
        ):
            environment.pop(name, None)

        program = """
import json
import sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from chatbot import answer_question, validate_response
from search_chunks import search_chunks
from semantic_search import semantic_search

assert search_chunks('wetland restoration')
assert semantic_search('wetland restoration', 3)
response = answer_question('What documents discuss aquatic invasive species?')
assert validate_response(response)[0]
assert len(list(Path('wiki').rglob('*.md'))) == 15
json.loads(Path('outputs/demo_answers.json').read_text(encoding='utf-8'))
"""
        completed = subprocess.run(
            [sys.executable, "-c", program],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(before, self.protected_hashes())

    def test_packaged_sqlite_connection_rejects_writes(self) -> None:
        database = ROOT / "deployment_artifacts" / "db" / "conservation.db"
        with connect_readonly(database) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("CREATE TABLE runtime_write_probe(value TEXT)")

    def test_runtime_copy_failure_is_sanitized(self) -> None:
        source = ROOT / "deployment_artifacts" / "db" / "vector_index"
        with patch(
            "runtime_artifacts.tempfile.TemporaryDirectory",
            side_effect=OSError("sensitive internal detail"),
        ):
            with self.assertRaises(RuntimeArtifactPreparationError) as caught:
                _create_disposable_vector_index(source)
        message = str(caught.exception)
        self.assertIn("packaged index was not modified", message)
        self.assertNotIn("sensitive internal detail", message)


if __name__ == "__main__":
    unittest.main()
