"""Local-only authority for OpenAI evidence validation and citation rendering."""

from __future__ import annotations

import re
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from chatbot import Evidence, cite
from runtime_artifacts import DATABASE_PATH
from sqlite_readonly import connect_readonly


INSUFFICIENT_ANSWER = (
    "The corpus does not provide enough evidence to answer that question reliably."
)
EVIDENCE_REFERENCE = re.compile(r"\[E([1-9]\d*)\]")
ANY_EVIDENCE_TOKEN = re.compile(r"\bE\d+\b|\[E", re.IGNORECASE)
RAW_DOCUMENT_CITATION = re.compile(r"\bDOC\d{3}\b", re.IGNORECASE)
RAW_URL = re.compile(r"(?:https?://|javascript\s*:|data\s*:|file\s*:)", re.IGNORECASE)
RAW_PAGE_REFERENCE = re.compile(r"\b(?:p{1,2}\.|pages?)\s*\d", re.IGNORECASE)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\s*\(", re.IGNORECASE)
SOURCE_LABEL = re.compile(r"\b(?:source|sources|reference|references)\s*:", re.IGNORECASE)
MULTI_SOURCE_CLAIM = re.compile(
    r"\b(?:across the corpus|multiple agencies|several documents|"
    r"across (?:the )?documents|multiple documents)\b",
    re.IGNORECASE,
)


class CitationValidationError(ValueError):
    """A model answer or evidence mapping failed mandatory local validation."""


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    chunk_id: str
    doc_id: str
    title: str
    location: str
    source_url: str
    excerpt: str
    semantic_score: float | None

    def to_evidence(self) -> Evidence:
        return Evidence(
            title=self.title,
            doc_id=self.doc_id,
            page=self.location,
            source_url=self.source_url,
            snippet=self.excerpt,
            chunk_id=self.chunk_id,
            similarity=self.semantic_score or 0.0,
        )


@dataclass(frozen=True)
class ValidatedCitationAnswer:
    answer: str
    citations: tuple[str, ...]
    sources: tuple[EvidenceRecord, ...]
    insufficient: bool


def build_evidence_records(evidence: list[Evidence]) -> tuple[EvidenceRecord, ...]:
    """Assign temporary IDs without deriving metadata from prompt text."""
    return tuple(
        EvidenceRecord(
            evidence_id=f"E{index}",
            chunk_id=item.chunk_id,
            doc_id=item.doc_id,
            title=item.title,
            location=item.page,
            source_url=item.source_url,
            excerpt=item.snippet,
            semantic_score=item.similarity,
        )
        for index, item in enumerate(evidence, 1)
    )


def is_safe_source_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme.casefold() in {"https", "http"} and bool(parsed.netloc)


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _validate_record_in_sqlite(record: EvidenceRecord, database_path: str | Path) -> None:
    if not is_safe_source_url(record.source_url):
        raise CitationValidationError("unsafe_source_url")
    with closing(connect_readonly(database_path)) as connection:
        row = connection.execute(
            """
            SELECT c.doc_id, c.page, c.source_url, c.chunk_text, d.title, d.url
            FROM chunks AS c
            JOIN documents AS d ON d.doc_id = c.doc_id
            WHERE c.chunk_id = ?
            """,
            (record.chunk_id,),
        ).fetchone()
    if row is None:
        raise CitationValidationError("unknown_chunk")
    doc_id, page, chunk_url, chunk_text, title, document_url = row
    if record.doc_id != doc_id:
        raise CitationValidationError("wrong_document_chunk_relationship")
    if record.location != page:
        raise CitationValidationError("location_mismatch")
    if record.title != title:
        raise CitationValidationError("title_mismatch")
    approved_urls = {value for value in (chunk_url, document_url) if value}
    if record.source_url not in approved_urls:
        raise CitationValidationError("source_url_mismatch")
    if _normalized(record.excerpt) not in _normalized(chunk_text):
        raise CitationValidationError("excerpt_not_in_chunk")


def _validate_claim_association(answer: str) -> None:
    """Require each substantive sentence or semicolon clause to carry support."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", answer):
        sentence = sentence.strip(" \t-*#")
        if not sentence:
            continue
        clauses = [part.strip() for part in sentence.split(";") if part.strip()]
        for clause in clauses:
            words = re.findall(r"[A-Za-z][A-Za-z'-]*", clause)
            if len(words) <= 5 and clause.endswith(":"):
                continue
            if len(words) >= 3 and not EVIDENCE_REFERENCE.search(clause):
                raise CitationValidationError("uncited_factual_claim")


def validate_and_render_model_answer(
    text: str,
    records: tuple[EvidenceRecord, ...],
    *,
    database_path: str | Path = DATABASE_PATH,
) -> ValidatedCitationAnswer:
    """Validate model E-IDs against SQLite, then render trusted local citations."""
    answer = text.strip()
    if not answer:
        raise CitationValidationError("empty_answer")
    if answer == INSUFFICIENT_ANSWER:
        return ValidatedCitationAnswer(answer, (), (), True)
    if (
        RAW_DOCUMENT_CITATION.search(answer)
        or RAW_URL.search(answer)
        or RAW_PAGE_REFERENCE.search(answer)
        or MARKDOWN_LINK.search(answer)
        or SOURCE_LABEL.search(answer)
    ):
        raise CitationValidationError("model_created_source_metadata")

    references = EVIDENCE_REFERENCE.findall(answer)
    remainder = EVIDENCE_REFERENCE.sub("", answer)
    if not references or ANY_EVIDENCE_TOKEN.search(remainder):
        raise CitationValidationError("missing_or_malformed_evidence_reference")

    by_id: dict[str, EvidenceRecord] = {}
    for record in records:
        if record.evidence_id in by_id:
            raise CitationValidationError("duplicate_evidence_mapping")
        by_id[record.evidence_id] = record
    referenced_records: list[EvidenceRecord] = []
    for number in references:
        evidence_id = f"E{number}"
        if evidence_id not in by_id:
            raise CitationValidationError("unknown_evidence_id")
        record = by_id[evidence_id]
        _validate_record_in_sqlite(record, database_path)
        referenced_records.append(record)

    _validate_claim_association(answer)
    if MULTI_SOURCE_CLAIM.search(answer):
        if len({record.doc_id for record in referenced_records}) < 2:
            raise CitationValidationError("unsupported_multi_source_claim")

    citations: list[str] = []
    sources: list[EvidenceRecord] = []
    source_keys: set[tuple[str, str, str]] = set()
    for record in referenced_records:
        rendered_citation = cite(record.doc_id, record.location)
        if rendered_citation not in citations:
            citations.append(rendered_citation)
        key = (record.doc_id, record.location, record.source_url)
        if key not in source_keys:
            source_keys.add(key)
            sources.append(record)

    rendered = EVIDENCE_REFERENCE.sub(
        lambda match: cite(by_id[f"E{match.group(1)}"].doc_id, by_id[f"E{match.group(1)}"].location),
        answer,
    )
    return ValidatedCitationAnswer(rendered, tuple(citations), tuple(sources), False)
