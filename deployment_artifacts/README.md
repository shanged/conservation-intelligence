# Precomputed deployment artifacts

This directory contains the immutable runtime database, Chroma index, and local
embedding model needed by the Streamlit application. It is a copy of the
verified pre-OpenAI local artifacts; the offline build outputs under `db/`
remain untouched and ignored.

Runtime selection is handled by `scripts/runtime_artifacts.py`:

1. `CONSERVATION_ARTIFACT_ROOT`, when explicitly set;
2. local build outputs under the project root, when complete;
3. this packaged directory as the clean-checkout fallback.

The package intentionally excludes raw PDFs, extracted text, logs, virtual
environments, secrets, lock files, and Hugging Face cache bookkeeping. The
model directory is a standalone model snapshot required for offline query
embedding, not a general-purpose cache.

At runtime, `scripts/runtime_artifacts.py` copies only the Chroma index into a
process-scoped directory created with Python's cross-platform temporary-file
support. Chroma queries use that disposable writable copy because Chroma's
persistent client performs internal write-lock bookkeeping even for queries.
The canonical package is never passed to Chroma. Runtime reads of
`conservation.db` use immutable SQLite read-only connections, while the offline
build scripts retain their existing writable local database behavior.

`MANIFEST.sha256` records the packaged binary/model file checksums. From this
directory, verify it with a SHA-256 checksum tool before publishing or after
transferring the package.

Other required runtime files remain in their existing tracked locations:

- `data/metadata.csv`
- `wiki/**/*.md`
- `outputs/demo_answers.json`

Entity and relation rows required by the app are already stored in the packaged
SQLite database. The CSV exports, Markdown evaluation report, and demo-question
file are retained in the repository for inspection/offline evaluation but are
not read during normal Streamlit runtime.
