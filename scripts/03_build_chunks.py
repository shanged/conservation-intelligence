"""Build page-aware text chunks and store them in SQLite.

Milestone 2A uses deterministic word-based chunks with an 800-word target and
100-word overlap. Re-running this script rebuilds the two milestone tables in
one transaction, so rows are replaced rather than duplicated.
"""

from __future__ import annotations

import csv
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_PATH = PROJECT_ROOT / "db" / "conservation.db"

PAGE_MARKER = re.compile(r"^--- Page (\d+) ---\s*$", re.MULTILINE)
TARGET_WORDS = 800
OVERLAP_WORDS = 100


@dataclass(frozen=True)
class PageWord:
    """A word paired with the source page on which it appeared."""

    text: str
    page: str


@dataclass(frozen=True)
class Chunk:
    """A database-ready chunk plus its normalized document metadata."""

    chunk_id: str
    doc_id: str
    title: str
    page: str
    chunk_text: str
    source_url: str


def read_metadata(path: Path) -> list[dict[str, str]]:
    """Read document metadata while preserving all values as strings."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_page_words(text: str) -> list[PageWord]:
    """Parse exact page markers and attach a page number to every word."""
    markers = list(PAGE_MARKER.finditer(text))
    if not markers:
        # HTML-derived sources have no real pages; never manufacture them.
        return [PageWord(word, "Web") for word in text.split()]

    page_words: list[PageWord] = []
    for index, marker in enumerate(markers):
        page = marker.group(1)
        body_start = marker.end()
        body_end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        page_words.extend(PageWord(word, page) for word in text[body_start:body_end].split())
    return page_words


def page_label(words: list[PageWord]) -> str:
    """Return a single page or an inclusive readable page range."""
    first_page = words[0].page
    last_page = words[-1].page
    return first_page if first_page == last_page else f"{first_page}-{last_page}"


def chunk_words(words: list[PageWord]) -> list[list[PageWord]]:
    """Split words near the target size with deterministic overlap.

    The number of chunks is chosen first so the average chunk remains near 800
    words. Boundaries are then distributed evenly, with exactly 100 words of
    overlap whenever the document needs more than one chunk.
    """
    if not words:
        return []
    if len(words) <= TARGET_WORDS:
        return [words]

    effective_words = TARGET_WORDS - OVERLAP_WORDS
    chunk_count = math.ceil((len(words) - OVERLAP_WORDS) / effective_words)
    total_slots = len(words) + OVERLAP_WORDS * (chunk_count - 1)
    base_size, extra = divmod(total_slots, chunk_count)

    chunks: list[list[PageWord]] = []
    start = 0
    for index in range(chunk_count):
        size = base_size + (1 if index < extra else 0)
        end = min(start + size, len(words))
        chunks.append(words[start:end])
        if end == len(words):
            break
        start = end - OVERLAP_WORDS
    return chunks


def build_document_chunks(metadata: dict[str, str], path: Path) -> list[Chunk]:
    """Create all chunks for one extracted document."""
    doc_id = metadata["doc_id"]
    words = parse_page_words(path.read_text(encoding="utf-8"))
    chunks: list[Chunk] = []
    for number, word_chunk in enumerate(chunk_words(words), start=1):
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}_CHUNK_{number:04d}",
                doc_id=doc_id,
                title=metadata["title"],
                page=page_label(word_chunk),
                chunk_text=" ".join(word.text for word in word_chunk),
                source_url=metadata["url"],
            )
        )
    return chunks


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the Milestone 2A schema and useful lookup indexes."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT,
            year TEXT,
            agency TEXT,
            topic TEXT,
            url TEXT,
            local_file TEXT,
            file_type TEXT
        );

        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT,
            page TEXT,
            chunk_text TEXT,
            source_url TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
        """
    )


def rebuild_database(
    connection: sqlite3.Connection,
    metadata_rows: list[dict[str, str]],
    chunks: list[Chunk],
) -> None:
    """Replace document and chunk contents atomically."""
    with connection:
        connection.execute("DELETE FROM chunks")
        connection.execute("DELETE FROM documents")
        connection.executemany(
            """
            INSERT INTO documents
                (doc_id, title, year, agency, topic, url, local_file, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["doc_id"],
                    row["title"],
                    row["year"],
                    row["agency"],
                    row["topic"],
                    row["url"],
                    row["local_file"],
                    row["file_type"],
                )
                for row in metadata_rows
            ],
        )
        connection.executemany(
            """
            INSERT INTO chunks (chunk_id, doc_id, page, chunk_text, source_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (chunk.chunk_id, chunk.doc_id, chunk.page, chunk.chunk_text, chunk.source_url)
                for chunk in chunks
            ],
        )


def print_validation(connection: sqlite3.Connection) -> None:
    """Print required validation statistics and representative chunks."""
    document_count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    rows = connection.execute(
        """
        SELECT doc_id, COUNT(*) AS chunk_count
        FROM chunks
        GROUP BY doc_id
        ORDER BY doc_id
        """
    ).fetchall()
    word_counts = [
        len(row[0].split())
        for row in connection.execute("SELECT chunk_text FROM chunks").fetchall()
    ]
    invalid_doc_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM chunks AS c
        LEFT JOIN documents AS d ON d.doc_id = c.doc_id
        WHERE d.doc_id IS NULL
        """
    ).fetchone()[0]
    missing_urls = connection.execute(
        "SELECT COUNT(*) FROM chunks WHERE source_url IS NULL OR TRIM(source_url) = ''"
    ).fetchone()[0]
    missing_pages = connection.execute(
        "SELECT COUNT(*) FROM chunks WHERE page IS NULL OR TRIM(page) = ''"
    ).fetchone()[0]

    print("\nVALIDATION")
    print(f"Documents stored: {document_count}")
    print(f"Total chunks: {sum(count for _, count in rows)}")
    for doc_id, count in rows:
        print(f"  {doc_id}: {count}")
    if word_counts:
        print(f"Average words per chunk: {sum(word_counts) / len(word_counts):.2f}")
        print(f"Minimum chunk size: {min(word_counts)}")
        print(f"Maximum chunk size: {max(word_counts)}")
    print(f"Every chunk has a valid doc_id: {invalid_doc_ids == 0}")
    print(f"Every chunk has a source URL: {missing_urls == 0}")
    print(f"Page information preserved: {missing_pages == 0}")

    samples = connection.execute(
        """
        SELECT chunk_id, page, chunk_text
        FROM chunks
        WHERE chunk_id IN (
            SELECT MIN(chunk_id) FROM chunks GROUP BY doc_id
        )
        ORDER BY chunk_id
        LIMIT 5
        """
    ).fetchall()
    print("\nSAMPLE CHUNKS")
    for chunk_id, page, text in samples:
        snippet = text[:300].replace("\n", " ")
        print(f"{chunk_id} | page {page} | {snippet}...")


def main() -> int:
    """Build all available processed documents into the local database."""
    metadata_rows = read_metadata(METADATA_PATH)
    metadata_by_id = {row["doc_id"]: row for row in metadata_rows}
    all_chunks: list[Chunk] = []

    for path in sorted(PROCESSED_DIR.glob("DOC*.txt")):
        doc_id = path.stem.upper()
        metadata = metadata_by_id.get(doc_id)
        if metadata is None:
            print(f"SKIP {path.name}: no matching metadata row")
            continue
        document_chunks = build_document_chunks(metadata, path)
        all_chunks.extend(document_chunks)
        print(f"BUILT {doc_id}: {len(document_chunks)} chunks")

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        create_schema(connection)
        rebuild_database(connection, metadata_rows, all_chunks)
        print_validation(connection)

    print(f"\nDatabase written: {DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
