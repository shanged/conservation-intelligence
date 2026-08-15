"""Static production-container contract checks."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DockerPackagingTests(unittest.TestCase):
    def test_dockerfile_uses_runtime_allowlist_non_root_and_required_command(self):
        text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM python:3.11-slim", text)
        self.assertIn("USER app", text)
        self.assertIn("EXPOSE 7860", text)
        self.assertIn("COPY .streamlit/config.toml", text)
        self.assertIn('"--server.address=0.0.0.0"', text)
        self.assertIn('"--server.port=7860"', text)
        self.assertNotIn("OPENAI_API_KEY=", text)
        for forbidden in ("01_download_sources.py", "02_extract_text.py", "04_build_vector_index.py"):
            self.assertNotIn(f"COPY {forbidden}", text)

    def test_dockerignore_excludes_secrets_raw_corpus_logs_and_local_db(self):
        rules = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        for required in (".env", ".env.*", ".venv", "data/raw", "data/processed", "**/*.pdf", "db", "*.log"):
            self.assertIn(required, rules)
        self.assertNotIn("deployment_artifacts", rules)
        self.assertNotIn("wiki", rules)

    def test_runtime_requirements_exclude_ingestion_packages(self):
        requirements = (ROOT / "requirements.runtime.txt").read_text(encoding="utf-8").casefold()
        for required in ("streamlit", "pandas", "sentence-transformers", "chromadb", "openai"):
            self.assertIn(required, requirements)
        for offline_only in ("pypdf", "beautifulsoup4", "requests"):
            self.assertNotIn(offline_only, requirements)


if __name__ == "__main__":
    unittest.main()
