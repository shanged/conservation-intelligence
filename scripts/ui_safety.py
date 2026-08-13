"""User-facing safety text and rendering decisions without Streamlit state."""

from __future__ import annotations

from html import escape
from urllib.parse import urlparse

RESEARCH_DISCLAIMER = (
    "Experimental research prototype analyzing public conservation documents. "
    "Answers may be incomplete or incorrect; verify important conclusions "
    "against the cited source documents."
)
PRIVACY_NOTICE = (
    "Privacy and data use: When optional OpenAI synthesis is enabled, your "
    "submitted question and selected excerpts from the public conservation "
    "corpus may be sent to OpenAI. This application does not intentionally "
    "persist submitted questions or model responses. Do not submit confidential, "
    "sensitive, private, or personally identifying information. When OpenAI "
    "synthesis is disabled, answers use the local deterministic retrieval and "
    "response path."
)
MODE_LABELS = {
    "openai": "Answer mode: AI synthesis",
    "deterministic_fallback": "Answer mode: Local deterministic fallback",
}
FALLBACK_LABELS = {
    "openai_unavailable": "OpenAI synthesis is disabled or unavailable.",
    "session_quota_reached": "Session AI quota reached.",
    "cooldown_active": "AI synthesis is cooling down briefly.",
    "duplicate_submission": "Duplicate submission protection was applied.",
    "invalid_openai_response": "AI output did not pass citation validation.",
    "openai_request_failed": "AI synthesis was temporarily unavailable.",
    "retrieval_failure": "Local evidence retrieval was temporarily unavailable.",
    "insufficient_evidence": "The corpus evidence was insufficient.",
    "question_too_long": "The question exceeded the public-demo limit.",
    "empty_question": "No question was submitted.",
    "sensitive_request": "The request was handled without exposing private configuration.",
}


def safe_source_url(url: object) -> str | None:
    if not isinstance(url, str):
        return None
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme.casefold() not in {"https", "http"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password:
        return None
    return cleaned


def safe_plain_text(value: object) -> str:
    return escape(str(value), quote=False)


def answer_mode_label(response: dict[str, object]) -> str:
    return MODE_LABELS.get(str(response.get("mode")), "Answer mode: Local response")


def fallback_status(response: dict[str, object]) -> str | None:
    reason = response.get("fallback_reason")
    return FALLBACK_LABELS.get(str(reason)) if reason else None
