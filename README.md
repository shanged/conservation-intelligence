---
title: Conservation Document Intelligence
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---

# Conservation Document Intelligence

An open, reproducible research prototype for searching and analyzing public
conservation documents with traceable citations.

The project turns a curated 35-source corpus into keyword and semantic search,
an evidence-backed wiki, structured entities and relationships, and a chatbot
that links its claims back to document and page-level evidence. It runs locally
without an external LLM by default; optional OpenAI synthesis can be enabled by
the operator after local evidence retrieval.

> [!IMPORTANT]
> This is an experimental research tool, not an authoritative conservation
> database or decision-making system. Results can be incomplete or incorrect.
> Verify important claims against the cited source documents.

## What is included

- A Streamlit interface with **Corpus**, **Search**, **Wiki**, **Chatbot**, and
  **Evaluation** tabs.
- Metadata for 35 public conservation sources (`DOC001`–`DOC035`).
- A packaged SQLite corpus, local Chroma index, and
  `sentence-transformers/all-MiniLM-L6-v2` snapshot for clean-checkout use.
- 15 generated, evidence-backed wiki pages.
- Deterministic cited answers that require no API key or paid service.
- Optional, bounded OpenAI synthesis with local citation validation and a
  deterministic fallback.
- Tests covering retrieval, citation integrity, request controls, UI safety,
  runtime artifact integrity, and Docker packaging.

## How it works

```text
Public sources → ingestion → page-aware text chunks → SQLite
                                                ├─→ keyword search
                                                ├─→ local embeddings → Chroma
                                                ├─→ entities/relations → wiki
                                                └─→ cited chatbot → evaluation
```

Semantic retrieval uses overlapping MiniLM embedding windows that are regrouped
into their original SQLite chunks. PDF evidence is cited by page or page range,
such as `[DOC012, pp. 5–6]`; saved web pages use citations such as
`[DOC023, Web]`. Source metadata and substitutions are documented in
[`data/metadata.csv`](data/metadata.csv) and
[`docs/source_classification.md`](docs/source_classification.md).

## Quick start

Python 3.10 or newer is recommended. From the repository root on Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.runtime.txt
streamlit run app.py
```

The application automatically uses the packaged runtime artifacts in
`deployment_artifacts/` when local build outputs are absent. No API key is
needed for search, wiki browsing, evaluation, or deterministic chatbot answers.

To install the additional ingestion and corpus-building tools instead:

```powershell
python -m pip install -r requirements.txt
```

## Build the corpus from source metadata

The precomputed runtime artifacts make a full rebuild optional. To reproduce
the pipeline from the public source list, run:

```powershell
python scripts/01_download_sources.py
python scripts/02_extract_text.py
python scripts/03_build_chunks.py
python scripts/04_build_vector_index.py
python scripts/05_extract_entities.py
python scripts/06_generate_wiki.py
python scripts/07_run_evaluation.py
```

Useful inspection commands:

```powershell
python scripts/01_download_sources.py --dry-run
python scripts/search_chunks.py "wetland restoration"
python scripts/semantic_search.py "wetland restoration" --top-k 5
```

Existing downloads are retained by default. Generated database, vector,
entity, relation, wiki, and evaluation records are rebuilt rather than appended
with duplicate rows.

## Optional OpenAI synthesis

OpenAI synthesis is disabled by default. When enabled, the local retrieval
pipeline sends only the current question and a bounded set of selected public
corpus excerpts—not full documents or chat history. Model-provided evidence IDs
must match immutable local SQLite metadata before the application renders the
corresponding `DOC` citations and source links.

To configure it locally, copy `.env.example` to an ignored `.env` file, then
load those values into the server process. The application does not
automatically load `.env` files.

Required operator settings are:

```text
OPENAI_API_KEY=<server-side secret>
USE_OPENAI_CHATBOT=true
```

Keep API keys in environment variables or hosting-platform secrets. Never put a
key in source code, a Docker build argument, the Streamlit UI, or a committed
`.env`/`.streamlit/secrets.toml` file. `USE_OPENAI_CHATBOT=false` is the
immediate kill switch.

Request length, evidence count, output tokens, timeout, retries, per-session
quota, and cooldown are bounded with conservative defaults in `.env.example`.
Failures fall back to the deterministic local response. These application
controls complement—but do not replace—provider-side budgets, rate limits, usage
alerts, and key restrictions.

## Privacy and safe use

Do not submit confidential, sensitive, private, or personally identifying
information. The application intentionally keeps chat history in Streamlit
session state and does not write questions, answers, retrieved excerpts, or
session history to its application database or output files. Hosting platforms,
network intermediaries, and optional API providers may have their own logging
and retention practices.

When OpenAI synthesis is enabled, the question and selected excerpts are sent
to OpenAI. This design does not make input anonymous or cryptographically
private and makes no broader claim about provider data handling.

The corpus is derived from public sources, but public availability does not
necessarily grant unrestricted redistribution rights. Raw downloads and
processed full text are intentionally excluded from Git. Review the original
publisher's terms before redistributing source material or derived bulk data.

## Security design

- The hosted container runs as a non-root user.
- Runtime model downloads are disabled in the Docker image; the reviewed model
  snapshot is packaged locally.
- Ingestion, extraction, and index-building scripts are excluded from the
  runtime image.
- SQLite is opened read-only, while Chroma uses a disposable temporary copy of
  the packaged index for its query-time bookkeeping.
- User-facing source links are restricted to validated HTTP(S) metadata URLs.
- Retrieved documents are treated as untrusted data; optional synthesis has no
  tools, browsing, code execution, or arbitrary URL authority.
- ChromaDB is used only as an embedded `PersistentClient` over the packaged
  local index. The project does not start or expose Chroma's HTTP/FastAPI server.
- `.env`, Streamlit secrets, credentials, logs, raw documents, virtual
  environments, caches, and transient database files are excluded from the
  deployment context.

### Current ChromaDB advisory

As of August 16, 2026, `chromadb==1.5.9` is affected by
`CVE-2026-45829` / `PYSEC-2026-311`, and no patched PyPI release is available.
The published pre-authentication exploit targets Chroma's network server API;
that API is not started or exposed by this application. Do not modify this
deployment to run `chroma run`, expose port `8000`, use an untrusted Chroma
server, or load an untrusted/remote collection configuration. Reassess and
upgrade when Chroma publishes a compatible fix. See [`SECURITY.md`](SECURITY.md)
for the supported boundary and reporting process.

Before publishing a fork, scan both the current tree and Git history for
credentials. If a real secret was ever committed, removing the file is not
enough: revoke the secret and rewrite the affected history before publication.

## Testing and evaluation

Run the offline test suite:

```powershell
python -m unittest discover -s tests -v
```

Run the deterministic evaluation:

```powershell
python scripts/07_run_evaluation.py
```

Run the hybrid path with a fake Responses client and no paid request:

```powershell
python scripts/08_run_hybrid_evaluation.py
```

Evaluation pass/fail values are automated integrity checks, not expert ratings.
They test evidence presence, known document IDs, valid locations, citation
mapping, and selected safety behavior; they do not establish factual
completeness or general natural-language entailment.

## Current corpus snapshot

| Item | Count |
|---|---:|
| Source metadata records | 35 |
| Locally usable sources | 32 |
| Sources requiring manual intervention | 3 |
| SQLite retrieval chunks | 977 |
| MiniLM embedding windows | 6,376 |
| Provenance-bearing entity records | 8,681 |
| Extracted relationships | 1,433 |
| Generated wiki pages | 15 |

The three records requiring manual intervention are `DOC014`, `DOC027`, and
`DOC030`. Several sources use documented substitutions or representative
documents when the originally specified page was unavailable or unsuitable for
automated extraction.

## Repository layout

```text
app.py                  Streamlit application
data/                   Public-source metadata (raw/full text is ignored)
deployment_artifacts/   Verified database, vector index, and local model
docs/                   Architecture, deployment, audit, and user guides
outputs/                Derived entities, relationships, and evaluations
scripts/                Ingestion, build, retrieval, chatbot, and safety code
tests/                  Offline regression and security-behavior tests
wiki/                   Generated evidence-backed Markdown pages
```

## Deployment note

The Hugging Face Space associated with this project is private and requires an
authorized Hugging Face session. Making this GitHub repository public does not
make that hosted application public. The included Dockerfile is the reviewed
deployment path and listens on port `7860`.

## Known limitations

- Three remote sources still require manual intervention.
- PDF extraction can preserve broken hyphenation and OCR-like artifacts.
- `DOC007` and `DOC008` represent the same underlying report.
- Rule-based entities and relationships favor inspectability over exhaustive
  language understanding.
- Semantic similarity is not proof of relevance.
- Citation validation establishes provenance and formatting integrity; it does
  not prove that every generated claim is fully entailed by its evidence.
- The packaged model and indexes make the repository comparatively large.

For deeper implementation and deployment detail, see
[`docs/implementation_report.md`](docs/implementation_report.md),
[`docs/deployment_security_audit.md`](docs/deployment_security_audit.md), and
[`docs/private_hugging_face_deployment_report.md`](docs/private_hugging_face_deployment_report.md).
