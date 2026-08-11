"""Generate a deterministic, evidence-backed conservation wiki.

No LLM or API is required. Pages are compiled only from entity occurrences,
extracted relations, and their SQLite chunks. Explicit relationships and mere
chunk co-occurrence are presented separately so association is not overstated.
"""
from __future__ import annotations

import csv
import hashlib
import math
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITIES_CSV = ROOT / "outputs" / "entities.csv"
RELATIONS_CSV = ROOT / "outputs" / "relations.csv"
DATABASE = ROOT / "db" / "conservation.db"
WIKI_ROOT = ROOT / "wiki"

CATEGORY_CONFIG = {
    "species": ({"species"}, 3, "species"),
    "habitats": ({"habitat", "wetland"}, 3, "habitats"),
    "locations": ({"location"}, 2, "locations"),
    "threats": ({"threat"}, 3, "threats"),
    "agencies": ({"agency"}, 4, "agencies"),
}
# Transparent relevance adjustments keep the small wiki aligned with the
# project's Missouri/wetland/AIS focus instead of selecting only broad terms.
RELEVANCE_BOOST = {
    "Missouri": 30, "Missouri Department of Conservation": 25,
    "wetland": 20, "aquatic habitat": 15, "invasive carp": 15,
    "zebra mussel": 10, "Great Lakes": 10,
}
EXCLUDED = {"United States", "North America", "disease", "flooding"}
REQUIRED_SECTIONS = ["Summary", "Key Facts", "Related Documents", "Related Entities", "Evidence", "Open Questions"]


@dataclass(frozen=True)
class Candidate:
    name: str
    entity_type: str
    category: str
    occurrences: int
    documents: int
    relationships: int
    confidence: float
    score: float


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def citation(doc_id: str, page: str) -> str:
    if page == "Web":
        return f"[{doc_id}, Web]"
    if "-" in page:
        start, end = page.split("-", 1)
        return f"[{doc_id}, pp. {start}–{end}]"
    return f"[{doc_id}, p. {page}]"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return slug or hashlib.sha1(name.encode()).hexdigest()[:12]


def select_entities(entities: list[dict[str, str]], relations: list[dict[str, str]]) -> list[Candidate]:
    relation_counts = Counter()
    for row in relations:
        relation_counts[row["subject"].casefold()] += 1
        relation_counts[row["object"].casefold()] += 1
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in entities:
        grouped[(row["entity_type"], row["name"])].append(row)

    selected: list[Candidate] = []
    for category, (types, quota, _) in CATEGORY_CONFIG.items():
        candidates = []
        for (entity_type, name), rows in grouped.items():
            if entity_type not in types or name in EXCLUDED:
                continue
            confidence = sum(float(row["confidence"]) for row in rows) / len(rows)
            if confidence < .80:  # Never build a page solely from open-ended candidates.
                continue
            documents = len({row["doc_id"] for row in rows})
            relationships = relation_counts[name.casefold()]
            score = documents * 6 + math.log1p(len(rows)) * 3 + relationships * .35 + confidence * 5 + RELEVANCE_BOOST.get(name, 0)
            candidates.append(Candidate(name, entity_type, category, len(rows), documents, relationships, confidence, score))
        selected.extend(sorted(candidates, key=lambda c: (-c.score, -c.documents, -c.occurrences, c.name))[:quota])
    return selected


def unique_evidence(rows: list[dict[str, str]], limit: int = 8) -> list[dict[str, str]]:
    """Prefer independent documents and remove exact overlap-derived repeats."""
    seen_text: set[str] = set(); by_doc: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = re.sub(r"\W+", " ", row["evidence"].casefold()).strip()
        if key and key not in seen_text:
            seen_text.add(key); by_doc[row["doc_id"]].append(row)
    chosen = [items[0] for _, items in sorted(by_doc.items())]
    if len(chosen) < limit:
        used = {(r["doc_id"], r["chunk_id"], r["evidence"]) for r in chosen}
        chosen.extend(r for items in by_doc.values() for r in items if (r["doc_id"], r["chunk_id"], r["evidence"]) not in used)
    return chosen[:limit]


def trim(text: str, length: int = 240) -> str:
    clean = " ".join(text.split()).replace("\n", " ")
    return clean if len(clean) <= length else clean[:length - 1].rstrip() + "…"


def build_page(candidate: Candidate, occurrences: list[dict[str, str]], relations: list[dict[str, str]],
               all_entities: list[dict[str, str]], titles: dict[str, str]) -> str:
    evidence_rows = unique_evidence(occurrences)
    citations = " ".join(citation(r["doc_id"], r["page"]) for r in evidence_rows[:3])
    lines = [f"# {candidate.name}", "", f"**Type:** {candidate.entity_type} {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}", "", "## Summary", ""]
    lines.append(f"The corpus identifies **{candidate.name}** as a conservation {candidate.entity_type}. It appears in {candidate.documents} documents across {candidate.occurrences} chunk-level occurrences. {citations}")

    lines += ["", "## Key Facts", ""]
    for row in evidence_rows[:5]:
        lines.append(f"- {trim(row['evidence'], 220)} {citation(row['doc_id'], row['page'])}")

    lines += ["", "## Related Documents", ""]
    per_doc = Counter(row["doc_id"] for row in occurrences)
    first_by_doc = {row["doc_id"]: row for row in occurrences}
    for doc_id, count in sorted(per_doc.items(), key=lambda x: (-x[1], x[0]))[:8]:
        row = first_by_doc[doc_id]
        lines.append(f"- **{titles.get(doc_id, doc_id)}** — {count} supporting occurrence{'s' if count != 1 else ''}. {citation(doc_id, row['page'])}")

    lines += ["", "## Related Entities", "", "### Explicit extracted relationships", ""]
    explicit = [r for r in relations if r["subject"].casefold() == candidate.name.casefold() or r["object"].casefold() == candidate.name.casefold()]
    if explicit:
        explicit.sort(key=lambda r: (r["relation"].startswith("document_mentions_"), r["relation"], r["doc_id"], r["chunk_id"]))
        for row in explicit[:8]:
            lines.append(f"- **{row['subject']}** `{row['relation']}` **{row['object']}**. {citation(row['doc_id'], row['page'])}")
    else:
        lines.append(f"- No explicit relationship involving this entity was extracted from the current evidence. {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")

    lines += ["", "### Co-occurrence only", ""]
    chunk_ids = {row["chunk_id"] for row in occurrences}
    co = Counter(row["name"] for row in all_entities if row["chunk_id"] in chunk_ids and row["name"].casefold() != candidate.name.casefold() and float(row["confidence"]) >= .80)
    co_evidence = {(row["chunk_id"], row["name"]): row for row in all_entities if row["chunk_id"] in chunk_ids}
    for name, count in co.most_common(6):
        match = next((row for (chunk, n), row in co_evidence.items() if n == name), None)
        if match:
            lines.append(f"- **{name}** co-occurs in {count} entity records; this does not establish a stronger relationship. {citation(match['doc_id'], match['page'])}")
    if not co:
        lines.append(f"- No recurring co-occurring entity was identified. {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")

    lines += ["", "## Evidence", ""]
    for row in evidence_rows:
        lines.append(f"> {trim(row['evidence'])}  \n> — {citation(row['doc_id'], row['page'])}, `{row['chunk_id']}`")
        lines.append("")

    lines += ["## Open Questions", ""]
    if candidate.documents == 1:
        lines.append(f"- Evidence currently comes from only one document. What independent sources corroborate or update it? {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")
    else:
        lines.append(f"- The evidence spans {candidate.documents} documents, but does not establish whether every statement remains current. Which sources provide the most recent status? {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")
    location_mentions = {r["name"] for r in all_entities if r["chunk_id"] in chunk_ids and r["entity_type"] == "location"}
    if location_mentions:
        lines.append(f"- The evidence mentions {', '.join(sorted(location_mentions)[:4])}. Is the geographic scope broader than these documented locations? {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")
    else:
        lines.append(f"- The extracted evidence does not consistently identify geographic scope. Which locations should be added? {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")
    if explicit:
        lines.append(f"- Extracted relationships are qualitative. What evidence quantifies their strength, extent, or outcomes? {citation(explicit[0]['doc_id'], explicit[0]['page'])}")
    else:
        lines.append(f"- No explicit relationship was extracted. Which documented relationships should be investigated? {citation(evidence_rows[0]['doc_id'], evidence_rows[0]['page'])}")
    return "\n".join(lines).rstrip() + "\n"


def validate_page(text: str, valid_docs: set[str], valid_locations: set[tuple[str, str]]) -> None:
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in text:
            raise ValueError(f"missing section: {section}")
    citations = re.findall(r"\[(DOC\d{3}), (Web|p\. \d+|pp\. \d+–\d+)\]", text)
    if not citations:
        raise ValueError("page contains no citations")
    for doc_id, label in citations:
        if doc_id not in valid_docs:
            raise ValueError(f"unknown cited document: {doc_id}")
        raw = "Web" if label == "Web" else label.removeprefix("p. ").removeprefix("pp. ").replace("–", "-")
        if (doc_id, raw) not in valid_locations:
            raise ValueError(f"citation location not found in SQLite: {doc_id} {raw}")


def main() -> int:
    entities = load_csv(ENTITIES_CSV); relations = load_csv(RELATIONS_CSV)
    selected = select_entities(entities, relations)
    with sqlite3.connect(DATABASE) as connection:
        titles = dict(connection.execute("SELECT doc_id, title FROM documents"))
        valid_locations = set(connection.execute("SELECT doc_id, page FROM chunks"))
    valid_docs = set(titles)
    selected_rows = []
    for directory in CATEGORY_CONFIG:
        folder = WIKI_ROOT / directory; folder.mkdir(parents=True, exist_ok=True)
        for stale in folder.glob("*.md"):
            stale.unlink()
    for candidate in selected:
        occurrences = [r for r in entities if r["entity_type"] == candidate.entity_type and r["name"] == candidate.name]
        page = build_page(candidate, occurrences, relations, entities, titles)
        validate_page(page, valid_docs, valid_locations)
        relative = Path("wiki") / candidate.category / f"{slugify(candidate.name)}.md"
        target = ROOT / relative; target.write_text(page, encoding="utf-8")
        page_id = "WIKI_" + hashlib.sha1(f"{candidate.entity_type}:{candidate.name.casefold()}".encode()).hexdigest()[:16].upper()
        selected_rows.append((page_id, candidate.name, candidate.entity_type, relative.as_posix(), candidate))

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS wiki_pages(page_id TEXT PRIMARY KEY, title TEXT, entity_type TEXT, file_path TEXT, updated_at TEXT)")
        connection.execute("DELETE FROM wiki_pages")
        connection.executemany("INSERT INTO wiki_pages VALUES (?,?,?,?,?)", [(p, n, t, f, generated_at) for p, n, t, f, _ in selected_rows])
    print(f"Generated {len(selected_rows)} wiki pages")
    for _, name, kind, path, candidate in selected_rows:
        print(f"{kind:8} | {name:45} | docs={candidate.documents:2} occurrences={candidate.occurrences:3} relations={candidate.relationships:3} score={candidate.score:.2f} | {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
