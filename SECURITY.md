# Security policy

## Supported deployment

Security fixes are applied to the current `master` branch. This research
prototype is supported only in the deployment shape described by its Dockerfile:

- Streamlit is the only network-facing application service.
- ChromaDB runs only through an embedded `PersistentClient` against the
  packaged, locally controlled index.
- No Chroma HTTP/FastAPI server or port `8000` is started or exposed.
- Runtime model downloads are disabled, and collection/model configuration is
  not accepted from users.
- Secrets are supplied only through server-side environment or hosting-platform
  secret storage.

Running ingestion scripts or a Chroma server as a public service is outside the
supported security boundary.

## Known dependency advisory

`chromadb==1.5.9` is affected by `CVE-2026-45829` / `PYSEC-2026-311`. The
published pre-authentication code-injection path targets Chroma's network API
and malicious remote model configuration. This repository does not start that
API and does not accept remote collection configuration. No patched ChromaDB
release is available on PyPI as of August 16, 2026.

Until a compatible patched release is available:

1. Do not run or expose `chroma run` or Chroma's HTTP/FastAPI server.
2. Do not connect this application to an untrusted Chroma server or collection.
3. Do not replace the packaged index or model snapshot with unreviewed files.
4. Keep the container non-root and expose only Streamlit port `7860`.
5. Re-run the dependency audit before every public deployment.

## Reporting a vulnerability

Please do not include secrets, personal data, exploit payloads, or sensitive
deployment details in a public issue. Contact the repository owner privately
through the security-reporting channel configured on the GitHub repository. If
private reporting is unavailable, open a minimal issue asking the maintainer to
enable a private channel without disclosing the vulnerability details.

Include the affected commit, deployment mode, reproduction preconditions,
impact, and suggested mitigation. Reports concerning an exposed Chroma server
should also be treated as deployment incidents because that configuration is
outside this project's supported boundary.
