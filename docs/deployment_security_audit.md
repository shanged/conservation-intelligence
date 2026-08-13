# Deployment security and readiness audit

Audit date: 2026-08-13  
Scope: current pre-OpenAI local prototype; repository working tree and all seven Git commits.  
Constraint: no deployment, dependency changes, OpenAI calls, or application-behavior changes were made.

## Executive summary

The local prototype is functional: the Streamlit UI exposes all five required tabs, 35 metadata records and 15 wiki pages load, semantic search and the deterministic chatbot respond, the evaluation reports 10/10 heuristic passes, and both regression tests pass. No credentials were found in tracked files or Git history.

The repository is not yet ready to publish unchanged. Its `.gitignore` excludes the SQLite database and Chroma index that the deployed runtime requires; semantic queries update the Chroma SQLite file's modification time; runtime dependencies are unpinned; and local Streamlit logs contain absolute user-profile paths. The chatbot also failed an intentionally unsupported-question probe by returning tangential evidence instead of an insufficient-evidence response.

## Critical risks

None identified. No API key, Hugging Face token, password assignment, authorization header, Streamlit secret, or committed `.env` file was found. A history scan across all seven commits found no credential-pattern candidate files.

Two strings in public source text matched a broad `sk-...` pattern. Redacted inspection showed identical dictionary/prose fragments ending in `...ies`, not credentials. They are false positives and are confined to ignored processed copies of DOC007 and DOC008.

## High risks

### Required runtime artifacts are ignored by Git

`.gitignore` excludes `db/*.db` and `db/vector_index/*`. The current application requires `db/conservation.db` for Corpus diagnostics, keyword search, Wiki, chatbot structured evidence, and citation validation, and requires the Chroma index for semantic search and chatbot retrieval. A clean clone or Hugging Face Space built from the currently tracked repository will therefore not reproduce the working local application.

Required fix: define an explicit, reviewed artifact-publication strategy before deployment (commit suitable precomputed artifacts, use Git LFS/a Dataset repository, or use another immutable artifact download mechanism). Verify checksums and startup availability in a clean environment.

### Chroma is not operationally read-only

A normal semantic-search/evaluation run changed the modification timestamp of `db/vector_index/chroma.sqlite3` without changing its size. The application opens Chroma using a persistent client. On a read-only filesystem this may fail; on writable ephemeral storage it can create nondeterministic runtime state.

Required fix: test the exact packaged index under read-only permissions. If Chroma cannot operate read-only, copy the precomputed index to bounded ephemeral storage at startup or replace the runtime access pattern in a later, explicitly authorized behavior-change phase.

### Unsupported-question refusal is unreliable

The baseline probe, “What does this corpus say about coral reef restoration on Mars?”, did not set the insufficient-evidence flag. It returned tangential evidence and citations. The existing 10/10 evaluation checks structural integrity, not answer relevance or factual completeness.

Required fix: before public release, add relevance/refusal tests and strengthen insufficient-evidence gating in a separate behavior-change phase.

## Medium risks

### Dependencies are unpinned and not separated by runtime role

`requirements.txt` contains package names without versions or hashes. A future Space rebuild may resolve incompatible releases, and `sentence-transformers`/`chromadb` bring a large transitive stack and model/runtime resource cost.

Classification:

| Package | Classification | Reason |
|---|---|---|
| `streamlit` | Deployed runtime | Application UI and session state. |
| `pandas` | Deployed runtime | Metadata, entity diagnostics, and wiki database queries in `app.py`. |
| `sentence-transformers` | Deployed runtime for current behavior | Embeds semantic-search and chatbot queries locally. Also used offline to build the index. |
| `chromadb` | Deployed runtime for current behavior | Reads the persistent semantic index. Also used offline to build it. |
| `requests` | Offline ingestion only | Downloads source documents in `scripts/01_download_sources.py`; not imported by the app path. |
| `beautifulsoup4` | Offline ingestion only | Converts downloaded HTML to text during ingestion; not imported by the app path. |
| `pypdf` | Offline ingestion only | Extracts PDF text; not imported by the app path. |

No listed package is demonstrably unnecessary for the repository as a whole. The last three are unnecessary for a deployment image that contains only precomputed artifacts and does not expose ingestion. Do not remove or split packages until a clean-environment runtime test is available.

Required fix: produce and test a pinned runtime dependency set separately from offline ingestion/build dependencies. Preserve the current file until that change is explicitly authorized.

### Local logs expose workstation paths and grow during normal use

Untracked `streamlit.stderr.log` and `streamlit.stdout.log` exist at repository root. During this audit the stderr log grew substantially and contained absolute `C:\Users\...` paths. No credential was printed during the redacted scan, but logs may expose usernames, local paths, stack traces, queries, or future secret-bearing exceptions.

Required fix: keep both logs untracked, remove them from any publication bundle, and configure bounded/ephemeral platform logging. Never publish logs without review and redaction.

### Public-source personal data is propagated into derived artifacts

Email-address patterns occur in several public corpus documents and derived entity/relation/wiki outputs. Names and organizational contact details can also be extracted. No private MDC dataset was identified; project documentation and metadata describe the corpus as public. Public availability does not automatically establish that every contact detail should be republished in derived bulk data.

Required fix: review redistribution terms and minimize contact details in any publicly downloadable derived dataset. Document the public provenance and removal process.

### Corpus redistribution and provenance need a release check

The local raw and processed corpora are ignored. The project states that all sources are public, with three manual-intervention records and several substitutions/representative selections. Public access is not the same as unrestricted redistribution, and derived text can retain source-specific notices.

Required fix: review source terms, licenses, substitutions, and attribution before bundling raw PDFs or extracted text. Prefer linking to sources when redistribution rights are unclear.

## Low risks

- The Hugging Face deployment guide is currently untracked. It is documentation rather than a runtime dependency, but its publication status should be intentional.
- `outputs/demo_answers.md` and `outputs/demo_answers.json` are regenerated by `scripts/07_run_evaluation.py`; normal Streamlit usage only reads them. Re-running evaluation overwrites both files.
- Chat history is stored only in `st.session_state`; it is not written to disk by application code. It is ephemeral per Streamlit session but may still appear in platform telemetry or error logs depending on hosting configuration.
- The app catches broad exceptions and displays exception text to users. This can expose internal paths or implementation details in a public UI.
- The local model may attempt a network download when its cache is absent. A clean deployment must package/cache the model or explicitly allow and verify startup download behavior.
- Generated answers and wiki pages contain OCR artifacts, broken hyphenation, duplicated-source effects (DOC007/DOC008), and occasionally tangential retrieved passages.

## Runtime-write review

| Target | Normal Streamlit behavior | Audit result |
|---|---|---|
| SQLite corpus database | Read queries via `sqlite3.connect` | No content/size change observed during UI verification. Connections are not opened with SQLite URI `mode=ro`, so read-only intent is not enforced. |
| Chroma index | Persistent semantic reads | `chroma.sqlite3` modification time changed during semantic retrieval/evaluation. Treat as runtime-writable until proven otherwise. |
| Wiki Markdown files | Read with `Path.read_text` | No writes in `app.py`; generation script overwrites them offline. |
| Evaluation outputs | Read by Streamlit | No UI write. `scripts/07_run_evaluation.py` overwrites `outputs/demo_answers.md` and `.json`. |
| Entity/relation outputs | Not written by Streamlit | Offline extraction overwrites CSVs and corresponding database tables. |
| Logs | External Streamlit/process logging | Local log files exist and stderr grew during verification. Exclude from artifacts. |
| User history | `st.session_state` only | No repository/database/file write found. Ephemeral in-process session state. |
| Feedback files | None implemented | No feedback persistence path found. |

## Required fixes

1. Decide how the required SQLite and Chroma artifacts will be packaged and verify a clean clone contains everything the app needs.
2. Make the deployed artifact access model genuinely read-only, with an explicit strategy for Chroma's observed writes.
3. Pin and clean-test a deployment-only dependency set; separately retain offline ingestion/build dependencies.
4. Exclude and remove local logs from the deployment bundle; use bounded platform logging and redact errors shown to users.
5. Add relevance and insufficient-evidence tests, then fix the demonstrated unsupported-question failure in a later authorized behavior-change phase.
6. Review corpus/derived-data redistribution rights and personal-contact minimization.
7. Run the app from a clean, isolated environment with no pre-existing model cache and verify startup, memory, disk, and network requirements.

## Optional hardening

- Open SQLite with enforced read-only URI mode and fail clearly if an artifact is missing or mismatched.
- Record checksums/version metadata for the database, vector index, wiki, and evaluation outputs.
- Run the Space as a non-root user with a read-only application filesystem and a small dedicated temporary directory.
- Add request-length, concurrency, memory, and execution-time limits before public access.
- Replace raw exception text in the UI with stable user messages while retaining sanitized diagnostic logs.
- Add dependency vulnerability and license scanning to CI.
- Add secret scanning/pre-commit checks and a CI history scan.
- Add a Content Security Policy and review outbound source links.
- Add a research-prototype disclaimer and an external feedback mechanism in the later deployment phase.

## Files safe to publish

Safe based on this audit, subject to normal code review and source-license confirmation:

- `.gitignore`, `README.md`, `app.py`, and `requirements.txt` (after the required dependency review).
- `scripts/` and `tests/` source files; ingestion scripts may be omitted from the minimal runtime image.
- `data/metadata.csv` and `docs/source_classification.md`, which describe public sources and substitutions.
- The three project/deployment DOCX documents, if their authors approve publication; no embedded credentials were detected by the repository scan.
- `wiki/` Markdown pages after a personal-contact/provenance review.
- `outputs/demo_answers.md`, `outputs/demo_answers.json`, and the pre-OpenAI baseline after reviewing extracted public text.
- `outputs/entities.csv` and `outputs/relations.csv` only after contact-detail minimization and redistribution review.
- `db/conservation.db` and `db/vector_index/` only if intentionally versioned/distributed, integrity-checked, license-reviewed, and the Chroma write issue is handled.

## Files that should remain local/private

- `.venv/`, `__pycache__/`, test/tool caches, model caches, and editor/OS metadata.
- `.env`, `.env.*`, `.streamlit/secrets.toml`, key files, tokens, or any future credential-bearing configuration.
- `streamlit.stdout.log`, `streamlit.stderr.log`, temporary files, crash dumps, and unreviewed platform logs.
- Raw or processed corpus copies whose redistribution rights have not been confirmed, even when source URLs are public.
- Any future user chat transcripts, feedback exports, analytics identifiers, or contact information unless collection, retention, and access controls are explicitly approved.
- Any private or embargoed MDC/conservation material. None was identified in the current corpus, but public-source provenance should be verified before release.

## Validation evidence

- Streamlit UI: all five tabs rendered; Corpus displayed 35; semantic Search returned scored results; Wiki rendered a generated page; Chatbot returned a cited deterministic answer; Evaluation displayed 10/10.
- Data: 35 metadata rows, 15 wiki files, 15 `wiki_pages` database rows, 977 chunks, and 10 evaluation records.
- Tests: `python -m unittest discover -s tests -v` passed 2/2 tests.
- Existing evaluation: `scripts/07_run_evaluation.py` completed with 10/10 heuristic passes.
- Git history: seven commits scanned; no secret-pattern candidate file was found.
- Source behavior: no application source or requirements file was changed.
