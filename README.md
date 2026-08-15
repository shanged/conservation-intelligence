---
title: Conservation Document Intelligence
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---

# Conservation Document Intelligence Prototype

A local, reproducible demonstration of public-document intelligence for
conservation research. The prototype organizes a 35-source corpus, extracts
citable text and structured facts, builds an evidence-backed wiki, and answers
questions with inspectable source citations.

This is an experimental research prototype analyzing public conservation
documents. Answers may be incomplete or incorrect. Verify important conclusions
against the cited source documents before relying on them.

## Privacy and safe use

When optional OpenAI synthesis is enabled, the submitted question and selected
excerpts from the public conservation corpus may be sent to OpenAI. The
application does not intentionally persist submitted questions, model responses,
retrieved excerpts, or session histories to application storage. Do not submit
confidential, sensitive, private, or personally identifying information. This
design does not imply that input is anonymous or cryptographically private, and
it makes no broader claim about provider data handling beyond the configured API
request behavior.

When OpenAI synthesis is disabled, chatbot answers remain on the local
deterministic retrieval/response path. Every answer identifies whether it used
AI synthesis or local deterministic fallback. Insufficient corpus evidence is
shown as a research limitation, distinct from temporary service errors and
request limits.

## Pipeline

```text
Public documents → ingestion → text extraction → page-aware chunks
                 → semantic search → entities/relations → wiki
                 → citation-grounded chatbot → heuristic evaluation
```

The system is a research prototype, not a production crawler or authoritative
conservation database. Source metadata and documented substitutions are kept in
`data/metadata.csv`.

## Setup on Windows

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The local embedding model is downloaded by `sentence-transformers` when first
needed. Subsequent builds and searches use its local cache.

## Full build order

Run these commands from the repository root:

```powershell
python scripts/01_download_sources.py
python scripts/02_extract_text.py
python scripts/03_build_chunks.py
python scripts/04_build_vector_index.py
python scripts/05_extract_entities.py
python scripts/06_generate_wiki.py
python scripts/07_run_evaluation.py
streamlit run app.py
```

Useful inspection commands:

```powershell
python scripts/01_download_sources.py --dry-run
python scripts/search_chunks.py "wetland restoration"
python scripts/semantic_search.py "wetland restoration" --top-k 5
```

Pipeline scripts are safe to rerun: existing downloads are retained by default,
and generated database, vector, entity, relation, wiki, and evaluation records
are rebuilt without duplicate rows.

## Application

The Streamlit application has exactly five main tabs:

- **Corpus** — metadata, statuses, agency/topic filters, and extraction counts.
- **Search** — keyword and local semantic retrieval.
- **Wiki** — 15 persistent entity-centered evidence pages.
- **Chatbot** — session-based cited answers with expandable source evidence.
- **Evaluation** — results for the ten required demonstration questions.

## Corpus status

- 35 metadata records (`DOC001`–`DOC035`)
- 32 locally usable sources: 20 PDFs and 12 saved web/text sources
- 3 sources requiring manual intervention: DOC014, DOC027, and DOC030
- 977 SQLite retrieval chunks
- 6,376 MiniLM embedding windows
- 8,681 provenance-bearing entity records
- 1,433 extracted relationships
- 15 generated wiki pages

See `data/metadata.csv` and `docs/source_classification.md` for download,
representative-selection, substitution, and failure details.

## Retrieval and citations

Semantic retrieval uses `sentence-transformers/all-MiniLM-L6-v2` and a local
Chroma index. Stored 600–900 word SQLite chunks are represented by overlapping
180-word embedding windows; results are regrouped by their original chunks.

PDF citations preserve extracted page or page-range metadata:

```text
[DOC012, p. 5]
[DOC012, pp. 5–6]
```

Saved web pages use:

```text
[DOC023, Web]
```

The chatbot diversifies semantic results across documents, uses approximately
five to eight evidence items, and exposes every used title, document ID,
location, URL, and snippet. Citations are validated against SQLite document and
chunk metadata during evaluation.

## Optional OpenAI configuration and deterministic fallback

No OpenAI key, paid service, or external LLM is required. The default chatbot
is deterministic and extractive: it selects relevant sentences from retrieved
chunks, adds structured entity/relation evidence for aggregate questions, and
refuses to answer when relevance and lexical-support checks indicate that the
corpus evidence is insufficient.

Optional OpenAI synthesis uses the Responses API only after the existing local
MiniLM/Chroma pipeline retrieves and filters a bounded evidence set. The model
receives the current question and approximately five to eight strong excerpts,
identified as `E1` through `E8`; it receives neither full documents nor chat
history. Model evidence references are validated and mapped to the existing
local document/page citations before display. Retrieved text is explicitly
treated as untrusted data, and tools, web search, browsing, code execution, and
response storage are disabled.

Citation integrity is enforced by `scripts/citation_validation.py`, not by the
model. Each temporary evidence record contains its E-ID, chunk ID, document ID,
stored title, page/Web location, stored source URL, exact excerpt, and semantic
score. Every referenced record must match the immutable SQLite document and
chunk rows, including document ownership, location, URL, title, and excerpt.
The Responses API is constrained to return claim text plus an `evidence_ids`
array selected from the supplied E-IDs. Local code converts that structured
output into claim-adjacent citations, replaces E-IDs with final `DOC` citations,
and populates the Sources panel from validated local records. A bounded repair
request remains available for malformed legacy/free-text output.

Answers with unknown E-IDs, invented document/page/URL metadata, unsafe links,
mismatched SQLite provenance, or unsupported multi-document claims are rejected.
Locally computed structured aggregates may establish corpus-wide counts without
requiring the model to infer them from semantic excerpts. Sources are
deduplicated by document, location, and trusted URL. The remaining validation is
intentionally conservative and does not attempt general natural-language
entailment.

Natural-language inventory variants for agencies/organizations, threats,
species, and habitats are routed through the structured entity database before
synthesis. Aggregate answers must preserve every ranked row and its exact chunk
and document counts. Representative citations are greedily diversified across
documents so a corpus-wide result does not appear to come from one source.

### Public-demo request controls

Application-level controls use conservative defaults: questions are limited to
750 normalized characters, at most 6 evidence items (hard ceiling 8) and 12,000
combined request characters are sent, output is capped at 600 tokens, timeout
is 20 seconds, and transient failures receive at most one retry. Authentication,
invalid-request, safety/policy, configuration, and citation-validation failures
are not retried.

Each browser session receives 20 attempted OpenAI requests with a three-second
cooldown. During quota, cooldown, or duplicate-rerun blocks, OpenAI is not
called and the deterministic local answer is used with a short notice. Guards,
quota counts, chat history, and bounded usage diagnostics live only in that
Streamlit session; questions, answers, evidence, and diagnostics are not written
to SQLite, JSON, logs, analytics, or other runtime files. Usage diagnostics
contain only mode, latency, configured model, token counts when returned by the
API, and a broad fallback reason.

`USE_OPENAI_CHATBOT=false` is the immediate kill switch even when a key exists.
These application safeguards do not replace OpenAI project budgets, usage
alerts, rate limits, key restrictions, or billing controls, which must be
configured separately on the server-side account.

All limits are configurable with `OPENAI_MAX_QUESTION_CHARS`,
`OPENAI_MAX_EVIDENCE_ITEMS`, `OPENAI_MAX_CONTEXT_CHARS`,
`OPENAI_MAX_OUTPUT_TOKENS`, `OPENAI_REQUEST_TIMEOUT_SECONDS`,
`OPENAI_MAX_RETRIES`, `OPENAI_SESSION_REQUEST_QUOTA`, and
`OPENAI_REQUEST_COOLDOWN_SECONDS`. Invalid or out-of-range settings disable
OpenAI synthesis and preserve deterministic fallback.

`USE_OPENAI_CHATBOT` defaults to `false`. The existing deterministic chatbot
remains the fallback when OpenAI is disabled, unavailable, misconfigured, times
out, raises any request error, or returns empty, malformed, unsafe, or unknown
evidence references. No OpenAI client is constructed while the feature is
disabled.

For local development, copy `.env.example` to an ignored `.env` file and add a
key only on the developer machine. The application does not currently load
`.env` automatically; export the variables into the server process if testing
configuration. Never commit `.env` or `.streamlit/secrets.toml`. A future
Hugging Face deployment will store `OPENAI_API_KEY` in Hugging Face Secrets,
not in source code, build arguments, or image layers. Users must never be asked
to enter an API key through the application UI.

Supported variables are `OPENAI_API_KEY`, `USE_OPENAI_CHATBOT`, `OPENAI_MODEL`,
`OPENAI_MAX_OUTPUT_TOKENS`, `OPENAI_REQUEST_TIMEOUT_SECONDS`, and
`OPENAI_MAX_RETRIES`. See `.env.example` for safe non-secret defaults.

### One future manual API smoke test (do not run during automated validation)

1. Outside Codex, place one real key in the ignored local `.env` file, confirm
   `git check-ignore .env`, and load those values into the Streamlit server
   process without printing them. Alternatively, configure the same variables
   as private Hugging Face Space Secrets when deployment is eventually allowed.
2. Set `USE_OPENAI_CHATBOT=true`, keep `OPENAI_MAX_RETRIES=0`, and retain the
   conservative token and timeout limits from `.env.example`.
3. Start Streamlit locally, ask one known demo question, and confirm a grounded
   answer with locally rendered `DOC` citations. Check only sanitized status;
   never log request headers, environment values, or SDK exception payloads.
4. Stop the server, disable OpenAI mode, and remove the key from the process.

This is preparation only; the Step 4 validation suite uses fake clients and
credentials and makes no network request.

## Evaluation

`tests/demo_questions.txt` contains exactly the ten questions required by the
project specification. `scripts/07_run_evaluation.py` runs them through the same
answering function used by Streamlit and writes:

- `outputs/demo_answers.md` — readable evaluation report
- `outputs/demo_answers.json` — structured data for the Evaluation tab

Pass/fail statuses are automated integrity checks, not human ratings. They
check answer presence, retrieved evidence, citation presence, known document
IDs, and valid SQLite page/location values.

### Deterministic vs hybrid comparison

Run the separate offline comparison without an API key or paid request:

```powershell
python scripts/08_run_hybrid_evaluation.py
```

This preserves the original `demo_answers` baseline and writes
`outputs/hybrid_evaluation.json` plus `outputs/hybrid_evaluation.md`. Offline
mode uses a fake Responses client while exercising local retrieval, citation
validation, latency/usage capture, comparative heuristics, and security cases.
Completeness, extractiveness, source diversity, and wetland-summary checks are
conservative indicators—not human factual-quality judgments.

Token usage is recorded when supplied by the response. Estimated cost remains
unavailable unless the time-sensitive, non-secret
`OPENAI_INPUT_COST_PER_MILLION_TOKENS` and
`OPENAI_OUTPUT_COST_PER_MILLION_TOKENS` variables are configured. Pricing is
never fetched dynamically or treated as permanent truth.

Live mode is disabled by default. A future one-question paid smoke test requires
an explicitly enabled OpenAI configuration and both flags:

```powershell
python scripts/08_run_hybrid_evaluation.py --live --limit 1
```

The command prints a paid-usage warning and never prints the API key. Do not run
it until a real key and server-side spend controls have been configured outside
Codex.

## Known limitations

- Three remote sources still require manual intervention.
- PDF extraction sometimes retains broken hyphenation or OCR-like artifacts.
- DOC007 and DOC008 represent the same underlying report, although repeated
  snippets are deduplicated during wiki and chatbot evidence selection.
- Rule-based entities and relationships favor transparency over exhaustive NLP.
- Wiki summaries and chatbot responses are conservative evidence compilations,
  not free-form LLM synthesis.
- Semantic similarity is not proof of relevance; the chatbot therefore applies
  document diversification, lexical support checks, and an explicit
  insufficient-evidence response.

## Repository layout

```text
data/        Source metadata, raw downloads, and extracted text
db/          SQLite database and local Chroma index
scripts/     Reproducible pipeline and shared retrieval/chatbot code
outputs/     Entities, relationships, and evaluation results
wiki/        Generated evidence-backed Markdown pages
tests/       Required demonstration questions
docs/        Project specification and source classification
```
