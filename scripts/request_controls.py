"""Session-local OpenAI quota, cooldown, and duplicate-submit controls."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from openai_config import OpenAIConfig


@dataclass
class OpenAISessionState:
    """User-session state only; never store raw questions or responses."""

    attempted_requests: int = 0
    last_request_at: float | None = None
    processed_request_ids: set[str] = field(default_factory=set)
    usage_diagnostics: list[dict[str, object]] = field(default_factory=list)


@dataclass(frozen=True)
class RequestDecision:
    allowed: bool
    reason: str | None = None
    status_message: str | None = None


def stable_request_id(normalized_question: str) -> str:
    """Return a non-reversible guard ID without retaining user content."""
    return hashlib.sha256(normalized_question.encode("utf-8")).hexdigest()


def authorize_openai_request(
    state: OpenAISessionState,
    config: OpenAIConfig,
    request_id: str,
    now: float,
) -> RequestDecision:
    if request_id in state.processed_request_ids:
        return RequestDecision(
            False,
            "duplicate_submission",
            "That question was already processed in this session; using the local answer.",
        )
    if state.attempted_requests >= config.session_request_quota:
        return RequestDecision(
            False,
            "session_quota_reached",
            "Hosted AI synthesis quota has been reached for this session; using the local answer.",
        )
    if state.last_request_at is not None:
        remaining = config.request_cooldown_seconds - (now - state.last_request_at)
        if remaining > 0:
            return RequestDecision(
                False,
                "cooldown_active",
                "Hosted AI synthesis is cooling down briefly; using the local answer.",
            )
    state.processed_request_ids.add(request_id)
    state.attempted_requests += 1
    state.last_request_at = now
    return RequestDecision(True)
