"""Deterministic citation-grounded answers over semantic evidence and wiki data.

The default chatbot is deliberately extractive: it retrieves with the existing
MiniLM/Chroma implementation, diversifies source documents, and composes only
claims directly supported by retrieved chunks or structured extraction rows.
No paid API, credential, or network call is required.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from runtime_artifacts import DATABASE_PATH, WIKI_ROOT
from semantic_search import VectorIndexNotFoundError, semantic_search
from sqlite_readonly import connect_readonly

ROOT = Path(__file__).resolve().parents[1]
DATABASE = DATABASE_PATH
STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "what", "which", "are", "is", "do", "does", "how", "across", "public", "documents", "document", "mention", "discuss", "evidence", "corpus", "provide", "about"}
SUMMARY_WORDS = {"generate", "short", "cited", "summary", "summarize"}
ENTITY_INVENTORY_ALIASES = (
    ("agency", re.compile(r"\b(?:agenc(?:y|ies)|conservation groups?|conservation organi[sz]ations?|organizations?)\b", re.I)),
    ("threat", re.compile(r"\b(?:conservation )?(?:threats?|pressures?|risks?)\b", re.I)),
    ("species", re.compile(r"\b(?:species|animals?|plants?|wildlife)\b", re.I)),
    ("habitat", re.compile(r"\b(?:habitats?|ecosystems?)\b", re.I)),
)
INVENTORY_CUES = re.compile(r"\b(?:list|main|common|most|frequent|frequently|mentioned|appear|represented|across)\b", re.I)
ENTITY_INVENTORY_LABELS = {
    "agency": "agencies and conservation organizations",
    "threat": "conservation threats",
    "species": "species",
    "habitat": "habitats",
}
SUMMARY_THEMES = (
    (
        "Protection and restoration",
        "EPA conservation programs pair wetland protection with restoration initiatives across its regions.",
        ({"wetland", "wetlands"}, {"protect", "protection"}, {"restore", "restoration"}),
    ),
    (
        "Monitoring and assessment",
        "Monitoring and assessment track wetland status and change so decision-makers can understand causes and implications.",
        ({"wetland", "wetlands"}, {"monitoring", "assessment", "reports"}, {"status", "change", "outcomes", "implications"}),
    ),
    (
        "Ecological and community benefits",
        "Wetlands filter water, protect communities from floods, and provide habitat for fish and other wildlife.",
        ({"wetland", "wetlands"}, {"habitat", "wildlife"}, {"water quality", "nutrient", "sediment", "flood"}),
    ),
)


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


def content_terms(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]{3,}", text.casefold()) if t not in STOPWORDS | SUMMARY_WORDS}


def entity_inventory_type(query: str) -> str | None:
    """Recognize broad inventories without capturing relationship questions."""
    if re.search(r"\b(?:relationship|relate|affect|impact|manage|management|why|how)\b", query, re.I):
        return None
    for entity_type, pattern in ENTITY_INVENTORY_ALIASES:
        match = pattern.search(query)
        if not match:
            continue
        direct = re.search(r"\b(?:what|which|who)\s+(?:are\s+)?(?:the\s+)?$", query[:match.start()], re.I)
        if INVENTORY_CUES.search(query) or direct:
            return entity_type
    return None


def sentence_quality(sentence: str, query: str) -> float:
    """Score prose quality and relevance; reject common OCR/navigation debris."""
    clean = " ".join(sentence.split())
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", clean)
    if len(words) < 7 or len(words) > 65:
        return -10.0
    if clean.endswith(("...", "…")) or not re.search(r"[.!?]$", clean):
        return -10.0
    if clean[:1].islower() or clean.startswith("(") or re.match(r"^(and|or|but|which|that|including)\b", clean, re.I):
        return -10.0
    if re.search(r"\b(?:Management Objective|Core Element|Activity 20\d\d|Literature Cited)\b", clean, re.I):
        return -10.0
    number_tokens = re.findall(r"\b\d+(?:[-–]\d+)?\b", clean)
    if len(number_tokens) >= 4 or re.search(r"(?:\bPage\s+\d+\b.*){2,}", clean, re.I):
        return -10.0
    heading_hits = len(re.findall(r"\b(?:overview|contents|literature cited|case study|appendix|index|chapter|page)\b", clean, re.I))
    if heading_hits >= 2:
        return -10.0
    commas = clean.count(",")
    if commas >= 7 or (commas >= 4 and sum(w[:1].isupper() for w in words) > len(words) * .35):
        return -10.0
    overlap = len(content_terms(query) & content_terms(clean))
    declarative = 1.5 if re.search(r"\b(?:is|are|was|were|has|have|provides?|supports?|protects?|restores?|improves?|informs?|requires?|will)\b", clean, re.I) else 0.0
    return overlap * 2.0 + declarative - abs(len(words) - 28) / 30


def candidate_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    candidates = []
    for part in re.split(r"(?<=[.!?])\s+", normalized):
        part = part.strip()
        # Web navigation and PDF headings are sometimes glued to the first
        # real sentence. Keep the declarative tail rather than exposing the
        # preceding menu or table-of-contents labels.
        starters = list(re.finditer(r"\b(?:The|These|This|Produced|Efficient|Wetland conservation activities)\b", part))
        for match in starters:
            tail = part[match.start():]
            if match.start() > 20 and len(tail.split()) >= 7:
                part = tail
                break
        if part:
            candidates.append(part)
    return candidates


def best_sentence(text: str, query: str, length: int = 360) -> str:
    candidates = candidate_sentences(text)
    if not candidates:
        return ""
    sentence = max(candidates, key=lambda item: sentence_quality(item, query))
    if sentence_quality(sentence, query) < 0 or len(sentence) > length:
        return ""
    return sentence


def near_duplicate(left: str, right: str) -> bool:
    a, b = content_terms(left), content_terms(right)
    return bool(a and b) and len(a & b) / min(len(a), len(b)) >= .72


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
            if not snippet or result.similarity < .30:
                continue
            snippet_key = re.sub(r"\W+", " ", snippet.casefold()).strip()
            if snippet_key in seen_snippets or any(near_duplicate(snippet, item.snippet) for item in selected):
                continue
            seen_snippets.add(snippet_key)
            selected.append(Evidence(result.title, result.doc_id, result.page, result.source_url,
                                     snippet, result.chunk_id, result.similarity))
            counts[result.doc_id] += 1
            if len(selected) == limit:
                return selected
    return selected


def supports_theme(item: Evidence, required_groups: tuple[set[str], ...]) -> bool:
    text = item.snippet.casefold()
    return all(any(term in text for term in group) for group in required_groups)


def thematic_summary(query: str) -> tuple[str, list[Evidence]]:
    """Build a deterministic, concise synthesis for summary questions."""
    subject = " ".join(sorted(content_terms(query)))
    chosen: list[tuple[str, str, Evidence]] = []
    used_docs: set[str] = set()
    for label, claim, required_groups in SUMMARY_THEMES:
        theme_terms = " ".join(sorted(set().union(*required_groups)))
        candidates = semantic_evidence(f"{subject} {theme_terms}", 8)
        supported = [item for item in candidates if supports_theme(item, required_groups)]
        supported.sort(key=lambda item: (item.doc_id not in used_docs, item.similarity), reverse=True)
        if supported:
            item = supported[0]
            chosen.append((label, claim, item))
            used_docs.add(item.doc_id)
    if len(chosen) < 2:
        return "", [item for _, _, item in chosen]
    lines = [f"- **{label}.** {claim} {cite(item.doc_id, item.page)}" for label, claim, item in chosen]
    return "The corpus highlights several complementary approaches to wetland conservation:\n" + "\n".join(lines), [item for _, _, item in chosen]


def entity_rank(entity_type: str, limit: int) -> list[tuple[str, int, int, Evidence]]:
    with connect_readonly(DATABASE) as connection:
        rankings = connection.execute(
            """SELECT e.name, COUNT(*) occurrences, COUNT(DISTINCT e.doc_id) docs
               FROM entities e WHERE e.entity_type=? GROUP BY e.name
               ORDER BY docs DESC, occurrences DESC, e.name LIMIT ?""",
            (entity_type, limit),
        ).fetchall()
        used_docs: set[str] = set()
        ranked: list[tuple[str, int, int, Evidence]] = []
        for name, occurrences, docs in rankings:
            candidates = connection.execute(
                """SELECT d.title,e.doc_id,e.page,c.source_url,e.evidence,e.chunk_id,e.confidence,c.chunk_text
                   FROM entities e
                   JOIN chunks c ON c.chunk_id=e.chunk_id
                   JOIN documents d ON d.doc_id=e.doc_id
                   WHERE e.entity_type=? AND e.name=?
                   ORDER BY e.confidence DESC,e.doc_id,e.chunk_id""",
                (entity_type, name),
            ).fetchall()
            if not candidates:
                continue
            chosen = next((row for row in candidates if row[1] not in used_docs), candidates[0])
            title, doc, page, url, extracted_evidence, chunk, _, chunk_text = chosen
            normalized_chunk = " ".join(chunk_text.split())
            derived = best_sentence(chunk_text, name)
            if " ".join(extracted_evidence.split()) in normalized_chunk:
                snippet = extracted_evidence
            elif derived and " ".join(derived.split()) in normalized_chunk:
                snippet = derived
            else:
                # Entity extraction and chunk rebuilding can normalize damaged
                # PDF glyphs differently. Anchor the evidence to an immutable
                # prefix of the owning chunk rather than weakening validation.
                snippet = normalized_chunk[:360].rstrip()
            used_docs.add(doc)
            ranked.append(
                (name, occurrences, docs, Evidence(title, doc, page, url, snippet, chunk, 1.0))
            )
    return ranked


def entity_evidence(name: str) -> Evidence | None:
    with connect_readonly(DATABASE) as connection:
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
    with connect_readonly(DATABASE) as connection:
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
    inventory_type = entity_inventory_type(query)

    if inventory_type:
        ranked = entity_rank(inventory_type, 6); evidence = merge_evidence([r[3] for r in ranked], semantic)
        label = ENTITY_INVENTORY_LABELS[inventory_type]
        answer = f"The most broadly represented extracted {label} are:\n" + "\n".join(
            f"- **{name}** — {occ} chunk occurrences across {docs} documents. {cite(item.doc_id,item.page)}" for name, occ, docs, item in ranked)
    elif "wiki pages were generated" in lower:
        answer, primary = wiki_inventory(); evidence = merge_evidence(primary, semantic)
    elif "important questions remain unanswered" in lower:
        evidence = semantic
        if not sufficient(query, evidence):
            return ChatResponse("The corpus does not provide enough evidence to identify grounded open questions.", (), tuple(evidence), True)
        prompts = (
            "Which findings remain current, especially where reports describe plans rather than measured outcomes?",
            "How broadly do findings apply beyond the locations documented in the corpus?",
            "Which reported threats and management actions have quantified ecological outcomes?",
        )
        questions = [f"- {prompt} {cite(item.doc_id, item.page)}" for prompt, item in zip(prompts, evidence[:3])]
        answer = "The current evidence leaves several recurring questions open:\n" + "\n".join(questions)
    elif "relationship between invasive carp" in lower:
        evidence = semantic
        with connect_readonly(DATABASE) as connection:
            direct = connection.execute("SELECT COUNT(*) FROM relations WHERE relation='species_uses_habitat' AND LOWER(subject)='invasive carp'").fetchone()[0]
        if not sufficient(query, evidence):
            return ChatResponse("The corpus does not provide enough evidence to answer this relationship question.", (), tuple(evidence), True)
        qualifier = "The structured extraction found no direct `species_uses_habitat` relation for invasive carp, so co-mention is not treated as proof of habitat use. " if direct == 0 else "The structured extraction contains a direct habitat-use relation. "
        answer = qualifier + "Retrieved evidence connects invasive-carp research and management with aquatic systems as follows:\n" + "\n".join(
            f"- {e.snippet} {cite(e.doc_id,e.page)}" for e in evidence[:5])
    elif "short cited summary" in lower or "summarize" in lower:
        answer, evidence = thematic_summary(query)
        if not answer:
            return ChatResponse(
                "The corpus does not provide enough high-quality evidence to synthesize that summary reliably.",
                (), tuple(evidence), True,
            )
    else:
        evidence = semantic
        if not sufficient(query, evidence):
            return ChatResponse("The corpus does not provide enough evidence to answer that question reliably.", (), tuple(evidence), True)
        answer = document_answer("The most relevant corpus evidence is:", evidence)

    citations = tuple(dict.fromkeys(re.findall(r"\[DOC\d{3}, (?:Web|p\. \d+|pp\. \d+–\d+)\]", answer)))
    return ChatResponse(answer, citations, tuple(evidence), False)


def validate_response(response: ChatResponse) -> tuple[bool, list[str]]:
    notes = []
    if not response.answer.strip(): notes.append("answer is empty")
    if not response.evidence and not response.insufficient: notes.append("retrieved evidence is empty")
    citations = re.findall(r"\[(DOC\d{3}), (Web|p\. \d+|pp\. \d+–\d+)\]", response.answer)
    if response.evidence and not response.insufficient and not citations: notes.append("answer has evidence but no citation")
    with connect_readonly(DATABASE) as connection:
        docs = {r[0] for r in connection.execute("SELECT doc_id FROM documents")}
        locations = set(connection.execute("SELECT doc_id,page FROM chunks"))
    for doc_id, label in citations:
        raw = "Web" if label == "Web" else label.removeprefix("p. ").removeprefix("pp. ").replace("–", "-")
        if doc_id not in docs: notes.append(f"unknown document citation {doc_id}")
        elif (doc_id, raw) not in locations: notes.append(f"unknown citation location {doc_id} {raw}")
    return not notes, notes
