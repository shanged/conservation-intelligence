# Conservation Document Intelligence Prototype

A small, reproducible prototype for organizing public conservation documents and preparing them for document intelligence workflows. The eventual system will combine a curated public corpus, OpenFOIA-style analysis, LLM Wiki pages, and a citation-grounded chatbot in a local Streamlit application.

## Current scope

The current prototype covers `DOC001` through `DOC005` and provides:

- the recommended repository structure;
- source metadata for the five documents;
- a downloader that saves source PDFs locally;
- text extraction with page markers;
- overlapping, page-aware chunks stored in SQLite;
- literal keyword and local semantic search; and
- Streamlit Corpus and Search tabs.

Entity and relationship extraction, wiki generation, and chatbot features are intentionally deferred.

## Setup

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Usage

Review the source records before downloading:

```powershell
python scripts/01_download_sources.py --dry-run
```

Download `DOC001` through `DOC005`:

```powershell
python scripts/01_download_sources.py
```

Extract text from downloaded files:

```powershell
python scripts/02_extract_text.py
```

Build page-aware chunks and the SQLite database:

```powershell
python scripts/03_build_chunks.py
```

Build or refresh the local Chroma semantic index:

```powershell
python scripts/04_build_vector_index.py
```

Run a command-line keyword or semantic search:

```powershell
python scripts/search_chunks.py "wetland restoration"
python scripts/semantic_search.py "wetland restoration" --top-k 5
```

Launch the minimal application:

```powershell
streamlit run app.py
```

## Repository layout

```text
data/raw/          Downloaded source files
data/processed/    Extracted plain text
data/metadata.csv  Source metadata and processing status
db/                Generated SQLite database and local Chroma vector index
scripts/           Reproducible pipeline steps
wiki/              Future entity-centered wiki pages
outputs/           Future structured analysis outputs
tests/             Future evaluation questions and tests
```

The original source URL remains in `data/metadata.csv` so every local document can be traced to its public source.
