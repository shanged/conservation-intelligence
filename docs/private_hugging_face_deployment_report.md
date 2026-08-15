# Private Hugging Face Deployment Report

## Deployment

- **Space:** `shanged/conservation-intelligence`
- **Visibility:** PRIVATE
- **SDK:** Docker
- **Hardware:** `cpu-basic` (2 vCPU, 16 GB RAM)
- **Deployment commit:** `722eef5821439e69c6994c3cbba143c484898a83`
- **Final runtime state:** RUNNING
- **Repository storage:** Xet enabled; approximately 203 MB of large-file storage used

The reviewed 88-file deployment tree was uploaded with the authenticated Hugging Face client after the Space rejected ordinary Git and Git LFS pushes for packaged binary artifacts. The Space repository URL and configured Git remote contain no credentials. The existing GitHub `origin` was not changed.

## Build and startup

The first hosted build exposed one packaging omission: `outputs/hybrid_evaluation.json` was required by the Dockerfile but excluded by `.gitignore`. The existing, non-secret 10-record evaluation artifact and an explicit `.gitignore` exception were committed and uploaded. The corrected build completed successfully.

The container starts Streamlit/Uvicorn on `0.0.0.0:7860` as the non-root application user. The packaged SQLite database, Chroma index, wiki, evaluation outputs, and local sentence-transformer snapshot are copied into the image. Startup does not run the downloader, PDF extraction, database construction, embedding construction, entity extraction, wiki generation, or evaluation scripts.

The normal restart returned the app to Running in approximately 49 seconds. The kill-switch configuration restart returned in approximately 67 seconds. Model weights loaded from the packaged local snapshot when semantic functionality was first used; no runtime model download was observed.

At runtime, `scripts/runtime_artifacts.py` creates and caches a disposable temporary copy of the packaged Chroma index for query-time bookkeeping. Successful semantic searches after both startup and restart confirmed that the packaged index and recreated runtime copy were usable. SQLite and the packaged source artifacts remained read-only.

## Hosted functional verification

### Corpus

- PASS: 35 metadata records displayed.
- PASS: corpus diagnostics loaded without a raw error.

### Search

- PASS: semantic search for `wetland` returned results.
- PASS: results included trusted document identifiers, page/Web locations, excerpts, titles, and local source metadata.
- PASS after restart.

### Wiki

- PASS: all 15 tracked wiki pages were present in the deployed repository.
- PASS: the hosted Wiki tab rendered summaries, key facts, related documents/entities, evidence, open questions, and local DOC citations.
- PASS after restart.

### Deterministic routing

Question tested:

`What documents discuss wetlands or wetland management?`

- PASS: `Answer mode: Local response`.
- PASS: seven locally cited results were returned.
- PASS: no OpenAI synthesis was invoked for this local document-inventory route.
- PASS after restart.

### Hosted OpenAI synthesis

Exactly one initial paid hosted synthesis request was made:

`Generate a short cited summary of wetland conservation evidence in the corpus.`

- PASS: `Answer mode: AI synthesis`.
- PASS: the response coherently summarized wetland status reporting, protection/restoration, and partnership-based planning.
- PASS: final citations were rendered locally as `[DOC022, Web]`, `[DOC021, Web]`, and `[DOC003, pp. 15–17]`.
- PASS: three source links resolved to the trusted local source metadata associated with those records.
- PASS: no E-IDs, fabricated pages, arbitrary links, raw exception, or model-created source metadata appeared in the final answer.

### Insufficient evidence

Question tested:

`What is the recipe for chocolate cake?`

- PASS: `Answer mode: Local deterministic fallback`.
- PASS: the application returned the canonical insufficient-evidence response.
- PASS: zero citations and zero sources were rendered.

### Evaluation

- PASS: deterministic heuristic evaluation loaded with 10/10 checks passing.
- PASS: the deterministic-versus-hybrid comparison loaded for all ten questions.

## Restart verification

- PASS: the Space returned to Running after one normal restart.
- PASS: no corpus, database, index, entity, wiki, or embedding rebuild ran.
- PASS: packaged SQLite loaded.
- PASS: the disposable Chroma runtime copy supported semantic search.
- PASS: Search, Wiki, and the deterministic chatbot route worked after restart.
- PASS: prior chatbot conversation was not required or persisted across restart.

## OpenAI kill-switch verification

`USE_OPENAI_CHATBOT` was temporarily changed to `false` through the private Space Settings UI.

- PASS: the Space restarted and returned to Running.
- PASS: Corpus continued to show 35 records.
- PASS: Search and Wiki continued to work.
- PASS: Evaluation continued to show 10/10 deterministic checks.
- PASS: the synthesis-style question returned `Answer mode: Local deterministic fallback` and reported that OpenAI synthesis was disabled or unavailable.
- PASS: no OpenAI call was required.

`USE_OPENAI_CHATBOT` was then restored to `true`. `OPENAI_API_KEY` was not viewed, changed, or copied. The Space returned to Running on `cpu-basic`.

## Secret and log audit

- PASS: Space visibility remained PRIVATE throughout deployment and testing.
- PASS: `.env` was never committed, uploaded, or copied into the image.
- PASS: `OPENAI_API_KEY` exists only as a Hugging Face Repository Secret.
- PASS: no OpenAI key, Hugging Face token, authorization header, or environment dump appeared in the reviewed build/runtime logs.
- PASS: no user-question, evidence, or model-response persistence appeared in runtime logs.
- PASS: no raw traceback or unsafe stack trace appeared in the hosted UI or final runtime logs.
- PASS: no local Streamlit logs, raw PDFs, processed corpus, virtual environment, caches, temporary Chroma directory, or local database/index outside `deployment_artifacts/` entered the Space repository.

## Known limitations

- The private UI requires an authenticated Hugging Face session; unauthenticated requests correctly return a not-found response.
- Free `cpu-basic` hardware may sleep after inactivity and has slower cold-start/first-semantic-query latency.
- The packaged deployment is approximately 203 MB and requires Hugging Face Xet storage for binary artifacts; an ordinary Git push is rejected by current Hub policy.
- The normal restart API was not authorized by the browser-login OAuth credential, so the restart was performed through the authenticated Space Settings UI.
- Automated evaluation and citation-integrity checks do not replace expert review of answer completeness or conservation conclusions.
- Citation validation establishes local provenance and formatting integrity; it does not implement unrestricted natural-language entailment verification.

## Verdict

PRIVATE HUGGING FACE DEPLOYMENT VERIFIED
