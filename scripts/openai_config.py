"""Centralized, non-networking OpenAI configuration with safe diagnostics."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_MAX_OUTPUT_TOKENS = 600
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RETRIES = 1
DEFAULT_MAX_QUESTION_CHARS = 750
DEFAULT_MAX_EVIDENCE_ITEMS = 6
HARD_MAX_EVIDENCE_ITEMS = 8
DEFAULT_MAX_CONTEXT_CHARS = 12_000
DEFAULT_SESSION_REQUEST_QUOTA = 20
DEFAULT_REQUEST_COOLDOWN_SECONDS = 3.0
MAX_OUTPUT_TOKENS_LIMIT = 2_000
MAX_REQUEST_TIMEOUT_SECONDS = 60.0
MAX_RETRIES_LIMIT = 1
MAX_QUESTION_CHARS_LIMIT = 4_000
MAX_CONTEXT_CHARS_LIMIT = 50_000
MAX_SESSION_REQUEST_QUOTA = 100
MAX_COOLDOWN_SECONDS = 60.0
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")


@dataclass(frozen=True)
class OpenAIConfig:
    """Validated server-side settings; secret material is excluded from repr."""

    enabled_requested: bool
    model: str
    max_output_tokens: int
    request_timeout_seconds: float
    max_retries: int
    max_question_chars: int
    max_evidence_items: int
    max_context_chars: int
    session_request_quota: int
    request_cooldown_seconds: float
    errors: tuple[str, ...]
    _api_key: str | None = field(default=None, repr=False, compare=False)

    @property
    def api_configured(self) -> bool:
        return bool(self._api_key)

    @property
    def openai_available(self) -> bool:
        return self.enabled_requested and self.api_configured and not self.errors

    @property
    def deterministic_fallback_available(self) -> bool:
        return True

    def server_api_key(self) -> str | None:
        """Return the key only for future server-side client construction."""
        return self._api_key

    def safe_status(self) -> dict[str, object]:
        """Expose only non-sensitive operational status."""
        return {
            "openai_enabled": self.openai_available,
            "api_configured": self.api_configured,
            "model": self.model,
            "fallback_available": self.deterministic_fallback_available,
            "max_question_chars": self.max_question_chars,
            "max_evidence_items": self.max_evidence_items,
            "max_context_chars": self.max_context_chars,
            "session_request_quota": self.session_request_quota,
            "request_cooldown_seconds": self.request_cooldown_seconds,
        }

    def safe_diagnostics(self) -> tuple[str, ...]:
        """Return sanitized messages containing variable names, never values."""
        return self.errors


def _parse_bool(name: str, raw: str, errors: list[str]) -> bool:
    normalized = raw.strip().casefold()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    errors.append(f"{name} must be a boolean value.")
    return False


def _parse_int(
    name: str,
    raw: str,
    default: int,
    minimum: int,
    maximum: int,
    errors: list[str],
) -> int:
    try:
        value = int(raw.strip())
    except (TypeError, ValueError):
        errors.append(f"{name} must be an integer between {minimum} and {maximum}.")
        return default
    if not minimum <= value <= maximum:
        errors.append(f"{name} must be between {minimum} and {maximum}.")
        return default
    return value


def _parse_float(
    name: str,
    raw: str,
    default: float,
    minimum: float,
    maximum: float,
    errors: list[str],
) -> float:
    try:
        value = float(raw.strip())
    except (TypeError, ValueError):
        errors.append(f"{name} must be a number between {minimum:g} and {maximum:g}.")
        return default
    if not minimum <= value <= maximum:
        errors.append(f"{name} must be between {minimum:g} and {maximum:g}.")
        return default
    return value


def load_openai_config(environ: Mapping[str, str] | None = None) -> OpenAIConfig:
    """Load and validate configuration without constructing a client or logging."""
    source = os.environ if environ is None else environ
    errors: list[str] = []
    enabled = _parse_bool(
        "USE_OPENAI_CHATBOT", source.get("USE_OPENAI_CHATBOT", "false"), errors
    )

    model = source.get("OPENAI_MODEL", DEFAULT_MODEL).strip()
    if not MODEL_PATTERN.fullmatch(model):
        errors.append("OPENAI_MODEL must be a non-empty model identifier.")
        model = DEFAULT_MODEL

    max_output_tokens = _parse_int(
        "OPENAI_MAX_OUTPUT_TOKENS",
        source.get("OPENAI_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS)),
        DEFAULT_MAX_OUTPUT_TOKENS,
        1,
        MAX_OUTPUT_TOKENS_LIMIT,
        errors,
    )
    request_timeout_seconds = _parse_float(
        "OPENAI_REQUEST_TIMEOUT_SECONDS",
        source.get(
            "OPENAI_REQUEST_TIMEOUT_SECONDS", str(DEFAULT_REQUEST_TIMEOUT_SECONDS)
        ),
        DEFAULT_REQUEST_TIMEOUT_SECONDS,
        1.0,
        MAX_REQUEST_TIMEOUT_SECONDS,
        errors,
    )
    max_retries = _parse_int(
        "OPENAI_MAX_RETRIES",
        source.get("OPENAI_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)),
        DEFAULT_MAX_RETRIES,
        0,
        MAX_RETRIES_LIMIT,
        errors,
    )
    max_question_chars = _parse_int(
        "OPENAI_MAX_QUESTION_CHARS",
        source.get("OPENAI_MAX_QUESTION_CHARS", str(DEFAULT_MAX_QUESTION_CHARS)),
        DEFAULT_MAX_QUESTION_CHARS,
        1,
        MAX_QUESTION_CHARS_LIMIT,
        errors,
    )
    max_evidence_items = _parse_int(
        "OPENAI_MAX_EVIDENCE_ITEMS",
        source.get("OPENAI_MAX_EVIDENCE_ITEMS", str(DEFAULT_MAX_EVIDENCE_ITEMS)),
        DEFAULT_MAX_EVIDENCE_ITEMS,
        1,
        HARD_MAX_EVIDENCE_ITEMS,
        errors,
    )
    max_context_chars = _parse_int(
        "OPENAI_MAX_CONTEXT_CHARS",
        source.get("OPENAI_MAX_CONTEXT_CHARS", str(DEFAULT_MAX_CONTEXT_CHARS)),
        DEFAULT_MAX_CONTEXT_CHARS,
        500,
        MAX_CONTEXT_CHARS_LIMIT,
        errors,
    )
    session_request_quota = _parse_int(
        "OPENAI_SESSION_REQUEST_QUOTA",
        source.get("OPENAI_SESSION_REQUEST_QUOTA", str(DEFAULT_SESSION_REQUEST_QUOTA)),
        DEFAULT_SESSION_REQUEST_QUOTA,
        1,
        MAX_SESSION_REQUEST_QUOTA,
        errors,
    )
    request_cooldown_seconds = _parse_float(
        "OPENAI_REQUEST_COOLDOWN_SECONDS",
        source.get(
            "OPENAI_REQUEST_COOLDOWN_SECONDS",
            str(DEFAULT_REQUEST_COOLDOWN_SECONDS),
        ),
        DEFAULT_REQUEST_COOLDOWN_SECONDS,
        0.0,
        MAX_COOLDOWN_SECONDS,
        errors,
    )

    api_key = source.get("OPENAI_API_KEY", "").strip() or None
    if enabled and not api_key:
        errors.append(
            "OpenAI mode was requested but OPENAI_API_KEY is not configured; "
            "deterministic fallback remains available."
        )

    return OpenAIConfig(
        enabled_requested=enabled,
        model=model,
        max_output_tokens=max_output_tokens,
        request_timeout_seconds=request_timeout_seconds,
        max_retries=max_retries,
        max_question_chars=max_question_chars,
        max_evidence_items=max_evidence_items,
        max_context_chars=max_context_chars,
        session_request_quota=session_request_quota,
        request_cooldown_seconds=request_cooldown_seconds,
        errors=tuple(errors),
        _api_key=api_key,
    )
