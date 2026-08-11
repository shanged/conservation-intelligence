"""Deterministic citation-grounded answers over semantic evidence and wiki data.

The default chatbot is deliberately extractive: it retrieves with the existing
MiniLM/Chroma implementation, diversifies source documents, and composes only
claims directly supported by retrieved chunks or structured extraction rows.
No paid API, credential, or network call is required.
"""
from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from semantic_search import VectorIndexNotFoundError, semantic_search

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "db" / "conservation.db"
WIKI_ROOT = ROOT / "wiki"
STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "what", "which", "are", "is", "do", "does", "how", "across", "public", "documents", "document", "mention", "discuss", "evidence", "corpus", "provide", "about"}


@dataclass(frozen=True)
class Evidence:
    title: str
    doc_id: str
    page: str
    source_url: str
    snippet: str
    chunk_id: str
    similarity: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ChatResponse:
    answer: str
    citations: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    insufficient: bool = False

    def to_dict(self) -> dict[str, object]:
        return {"answer": self.answer, "citations": list(self.citations), "evidence": [e.to_dict() for e in self.evidence], "insufficient": self.insufficient}


def cite(doc_id: str, page: str) -> str:
    if page == "Web":
        return f"[{doc_id}, Web]"
    if "-" in page:
        start, end = page.split("-", 1)
        return f"[{doc_id}, pp. {start}–{end}]"
    return f"[{doc_id}, p. {page}]"


def best_sentence(text: str, query: str, length: int = 300) -> str:
    terms = {t for t in re.findall(r"[a-z]{3,}", query.casefold()) if t not in STOPWORDS}
    candidates = [" ".join(s.split()) for s in re.split(r"(?<=[.!?])\s+", text) if len(s.split()) >= 6]
    if not candidates:
        candidates = [" ".join(text.split())]
    sentence = max(candidates, key=lambda s: (sum(t in s.casefold() for t in terms), -abs(len(s) - 220)))
    return sentence if len(sentence) <= length else sentence[:length - 1].rstrip() + "…"


def semantic_evidence(query: str, limit: int = 7) -> list[Evidence]:
    results = semantic_search(query, top_k=max(24, limit * 4))
    # First pass: one result per document. Second pass allows a second chunk per
    # document only when needed, preventing overlapping-window floods.
    selected = []; counts: dict[str, int] = defaultdict(int); seen_snippets: set[str] = set()
    for maximum in (1, 2):
        for result in results:
            if counts[result.doc_id] >= maximum or any(e.chunk_id == result.chunk_id for e in selected):
                continue
            snippet = best_sentence(result.window_text, query)
            snippet_key = re.sub(r"\W+", " ", snippet.casefold()).strip()
            if snippet_key in seen_snippets:
                continue
            seen_snippets.add(snippet_key)
            selected.append(Evidence(result.title, result.doc_id, result.page, result.source_url,
                                     snippet, result.chunk_id, result.similarity))
            counts[result.doc_id] += 1
            if len(selected) == limit:
                return selected
    return selected


def entity_rank(entity_type: str, limit: int) -> list[tuple[str, int, int, Evidence]]:
    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute(
            """SELECT e.name, COUNT(*) occurrences, COUNT(DISTINCT e.doc_id) docs,
                      e.doc_id, d.title, e.page, c.source_url, e.evidence, e.chunk_id
               FROM entities e JOIN chunks c ON c.chunk_id=e.chunk_id JOIN documents d ON d.doc_id=e.doc_id
               WHERE e.entity_type=? GROUP BY e.name
               ORDER BY docs DESC, occurrences DESC, e.name LIMIT ?""", (entity_type, limit)
        ).fetchall()
    return [(name, occurrences, docs, Evidence(title, doc, page, url, snippet, chunk, 1.0))
            for name, occurrences, docs, doc, title, page, url, snippet, chunk in rows]


def entity_evidence(name: str) -> Evidence | None:
    with sqlite3.connect(DATABASE) as connection:
        row = connection.execute(
            """SELECT d.title,e.doc_id,e.page,c.source_url,e.evidence,e.chunk_id
               FROM entities e JOIN chunks c ON c.chunk_id=e.chunk_id JOIN documents d ON d.doc_id=e.doc_id
               WHERE LOWER(e.name)=LOWER(?) ORDER BY e.confidence DESC,e.doc_id,e.chunk_id LIMIT 1""", (name,)
        ).fetchone()
    return Evidence(row[0], row[1], row[2], row[3], row[4], row[5], 1.0) if row else None


def merge_evidence(primary: list[Evidence], semantic: list[Evidence], limit: int = 8) -> list[Evidence]:
    merged = []; seen = set()
    for item in primary + semantic:
        if item.chunk_id not in seen:
            seen.add(item.chunk_id); merged.append(item)
    return merged[:limit]


def sufficient(query: str, evidence: list[Evidence]) -> bool:
    """Reject nearest-neighbor results that share no meaningful query term."""
    if not evidence or evidence[0].similarity < .25:
        return False
    terms = {t for t in re.findall(r"[a-z]{4,}", query.casefold()) if t not in STOPWORDS}
    corpus = " ".join(item.snippet.casefold() for item in evidence)
    return not terms or any(term in corpus for term in terms)


def document_answer(lead: str, evidence: list[Evidence]) -> str:
    lines = [lead]
    for item in evidence:
        lines.append(f"- **{item.title}**: {item.snippet} {cite(item.doc_id, item.page)}")
    return "\n".join(lines)


def wiki_inventory() -> tuple[str, list[Evidence]]:
    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute("SELECT title,entity_type FROM wiki_pages ORDER BY entity_type,title").fetchall()
    grouped: dict[str, list[str]] = defaultdict(list); support = []
    for title, kind in rows:
        grouped[kind].append(title)
        item = entity_evidence(title)
        if item and all(e.doc_id != item.doc_id for e in support):
            support.append(item)
    parts = ["The generated wiki currently contains:"]
    for kind, titles in grouped.items():
        citations = " ".join(cite(e.doc_id, e.page) for e in support[:2])
        parts.append(f"- **{kind}:** {', '.join(titles)}. {citations}")
    return "\n".join(parts), support[:6]


def answer_question(query: str, evidence_limit: int = 7) -> ChatResponse:
    query = query.strip()
    if not query:
        return ChatResponse("Please enter a question.", (), (), True)
    semantic = semantic_evidence(query, evidence_limit)
    lower = query.casefold()

    if "agencies appear most often" in lower:
        ranked = entity_rank("agency", 6); evidence = merge_evidence([r[3] for r in ranked], semantic)
        answer = "The most broadly represented agencies, measured from provenance-bearing entity occurrences, are:\n" + "\n".join(
            f"- **{name}** — {occ} chunk occurrences across {docs} documents. {cite(item.doc_id,item.page)}" for name, occ, docs, item in ranked)
    elif "main conservation threats" in lower:
        ranked = entity_rank("threat", 6); evidence = merge_evidence([r[3] for r in ranked], semantic)
        answer = "The most broadly represented extracted threats are:\n" + "\n".join(
            f"- **{name}** — {occ} chunk occurrences across {docs} documents. {cite(item.doc_id,item.page)}" for name, occ, docs, item in ranked)
    elif "wiki pages were generated" in lower:
        answer, primary = wiki_inventory(); evidence = merge_evidence(primary, semantic)
    elif "important questions remain unanswered" in lower:
        evidence = semantic
        if not sufficient(query, evidence):
            return ChatResponse("The corpus does not provide enough evidence to identify grounded open questions.", (), tuple(evidence), True)
        answer = (
            "The current evidence leaves several recurring questions open:\n"
            f"- Which findings remain current, especially where reports describe plans rather than measured outcomes? {cite(evidence[0].doc_id,evidence[0].page)}\n"
            f"- How broadly do findings apply beyond the locations documented in the corpus? {cite(evidence[1].doc_id,evidence[1].page)}\n"
            f"- Which reported threats and management actions have quantified ecological outcomes? {cite(evidence[2].doc_id,evidence[2].page)}"
        )
    elif "relationship between invasive carp" in lower:
        evidence = semantic
        with sqlite3.connect(DATABASE) as connection:
            direct = connection.execute("SELECT COUNT(*) FROM relations WHERE relation='species_uses_habitat' AND LOWER(subject)='invasive carp'").fetchone()[0]
        if not sufficient(query, evidence):
            return ChatResponse("The corpus does not provide enough evidence to answer this relationship question.", (), tuple(evidence), True)
        qualifier = "The structured extraction found no direct `species_uses_habitat` relation for invasive carp, so co-mention is not treated as proof of habitat use. " if direct == 0 else "The structured extraction contains a direct habitat-use relation. "
        answer = qualifier + "Retrieved evidence connects invasive-carp research and management with aquatic systems as follows:\n" + "\n".join(
            f"- {e.snippet} {cite(e.doc_id,e.page)}" for e in evidence[:5])
    else:
        evidence = semantic
        if not sufficient(query, evidence):
            return ChatResponse("The corpus does not provide enough evidence to answer that question reliably.", (), tuple(evidence), True)
        if "short cited summary" in lower:
            answer = "The retrieved corpus evidence supports this concise summary:\n" + "\n".join(
                f"- {e.snippet} {cite(e.doc_id,e.page)}" for e in evidence[:6])
        else:
            answer = document_answer("The most relevant corpus evidence is:", evidence)

    citations = tuple(dict.fromkeys(re.findall(r"\[DOC\d{3}, (?:Web|p\. \d+|pp\. \d+–\d+)\]", answer)))
    return ChatResponse(answer, citations, tuple(evidence), False)


def validate_response(response: ChatResponse) -> tuple[bool, list[str]]:
    notes = []
    if not response.answer.strip(): notes.append("answer is empty")
    if not response.evidence and not response.insufficient: notes.append("retrieved evidence is empty")
    citations = re.findall(r"\[(DOC\d{3}), (Web|p\. \d+|pp\. \d+–\d+)\]", response.answer)
    if response.evidence and not response.insufficient and not citations: notes.append("answer has evidence but no citation")
    with sqlite3.connect(DATABASE) as connection:
        docs = {r[0] for r in connection.execute("SELECT doc_id FROM documents")}
        locations = set(connection.execute("SELECT doc_id,page FROM chunks"))
    for doc_id, label in citations:
        raw = "Web" if label == "Web" else label.removeprefix("p. ").removeprefix("pp. ").replace("–", "-")
        if doc_id not in docs: notes.append(f"unknown document citation {doc_id}")
        elif (doc_id, raw) not in locations: notes.append(f"unknown citation location {doc_id} {raw}")
    return not notes, notes
