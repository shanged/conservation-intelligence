# Hugging Face deployment inventory

## Included

- `Dockerfile`, `requirements.runtime.txt`, and `.dockerignore`
- `app.py`
- Runtime modules explicitly copied from `scripts/` by the Dockerfile
- `data/metadata.csv`
- `deployment_artifacts/db/conservation.db`
- `deployment_artifacts/db/vector_index/`
- `deployment_artifacts/model/all-MiniLM-L6-v2/`
- `wiki/`
- `outputs/demo_answers.json`
- `outputs/hybrid_evaluation.json`

The Dockerfile uses an explicit allow-list. Offline ingestion, extraction,
index-building, entity-generation, wiki-generation, and evaluation scripts are
not copied into the image.

## Excluded

- `.env`, Streamlit secrets, API/Hugging Face tokens, credentials, and keys
- `.git`, editor files, caches, virtual environments, bytecode, and logs
- `data/raw/`, `data/processed/`, and all raw PDFs
- Local development `db/`, model/download caches, and SQLite sidecars
- Tests, project documentation, live evaluation records, CSV exports, and
  baseline reports not read by normal Streamlit runtime

## Hugging Face Secret

- `OPENAI_API_KEY` — optional. Configure only as a private Space secret, never
  as a Docker build argument, repository file, or ordinary variable.

## Hugging Face Variables

- `USE_OPENAI_CHATBOT`
- `OPENAI_MODEL`
- `OPENAI_MAX_OUTPUT_TOKENS`
- `OPENAI_REQUEST_TIMEOUT_SECONDS`
- `OPENAI_MAX_RETRIES`
- `OPENAI_MAX_QUESTION_CHARS`
- `OPENAI_MAX_EVIDENCE_ITEMS`
- `OPENAI_MAX_CONTEXT_CHARS`
- `OPENAI_SESSION_REQUEST_QUOTA`
- `OPENAI_REQUEST_COOLDOWN_SECONDS`
- `OPENAI_INPUT_COST_PER_MILLION_TOKENS` (optional reporting only)
- `OPENAI_OUTPUT_COST_PER_MILLION_TOKENS` (optional reporting only)
- `CONSERVATION_ARTIFACT_ROOT` (optional override; not required in the image)

No environment value is printed during normal startup. If OpenAI is disabled,
missing, or invalid, the application starts and uses deterministic fallback.

## Startup command

```text
streamlit run app.py --server.address=0.0.0.0 --server.port=7860 --server.headless=true
```

## Expected artifact/runtime behavior

The packaged SQLite database is opened immutable and read-only. Chroma performs
query-time bookkeeping, so the packaged vector index is copied once per process
to a process-scoped temporary directory. Only that disposable copy is writable;
the canonical deployment index remains unchanged. A clean container restart
creates a new temporary copy and requires no persisted application state.

Startup checks require metadata, packaged SQLite, Chroma, the local embedding
model, wiki pages, and deterministic evaluation JSON. Missing artifacts produce
a configuration error and never trigger downloading, PDF extraction, chunking,
embedding, entity extraction, or wiki generation.

## Local Docker validation

- Image: `conservation-intelligence:step10`
- Image size: 746,639,344 bytes (approximately 712 MiB)
- First uncached build: approximately 4.3 minutes on the test workstation
- Clean restart to HTTP 200: 1.24 seconds
- First semantic-path check, including local model/index initialization: about
  12.1 seconds
- Disposable Chroma copy: 102,566,340 bytes (approximately 97.8 MiB), measured
  at 628 ms on the first check and 119 ms after restart
- Idle container memory after restart: approximately 50 MiB
- Runtime identity: unprivileged `app` user (UID/GID 999)
- CPU-only inference: verified with three semantic results; no GPU is required
- Canonical packaged index: SHA-256 unchanged before and after queries/restart
- Visible UI: Corpus, Search, Wiki, Chatbot, and Evaluation tabs all rendered;
  keyword Search returned results and deterministic Chatbot operation passed

The optional real-key container request was intentionally skipped. The key was
never passed to the build or container, and the previously completed local live
hybrid smoke/evaluation tests already verified OpenAI operation.
