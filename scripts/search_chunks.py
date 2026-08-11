"""Reusable case-insensitive SQLite keyword search for Milestone 2A."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "db" / "conservation.db"


@dataclass(frozen=True)
class SearchResult:
    """A retrieval result with the source fields required by the milestone."""

    doc_id: str
    title: str
    page: str
    text_snippet: str
    source_url: str


def make_snippet(text: str, query: str, length: int = 240) -> str:
    """Return a compact excerpt centered near the first keyword match."""
    match_at = text.casefold().find(query.casefold())
    if match_at < 0:
        match_at = 0
    start = max(0, match_at - length // 3)
    end = min(len(text), start + length)
    snippet = text[start:end].strip()
    if start:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def search_chunks(
    query: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    limit: int = 5,
) -> list[SearchResult]:
    """Return chunks containing the literal query, ignoring case."""
    query = query.strip()
    if not query:
        return []
    if limit < 1:
        raise ValueError("limit must be at least 1")

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT c.doc_id, d.title, c.page, c.chunk_text, c.source_url
            FROM chunks AS c
            JOIN documents AS d ON d.doc_id = c.doc_id
            WHERE INSTR(LOWER(c.chunk_text), LOWER(?)) > 0
            ORDER BY c.doc_id, c.chunk_id
            """,
            (query,),
        ).fetchall()

    normalized_query = query.casefold()
    rows.sort(key=lambda row: (-row[3].casefold().count(normalized_query), row[0], row[2]))
    return [
        SearchResult(
            doc_id=doc_id,
            title=title,
            page=page,
            text_snippet=make_snippet(text, query),
            source_url=source_url,
        )
        for doc_id, title, page, text, source_url in rows[:limit]
    ]


def parse_args() -> argparse.Namespace:
    """Parse a query and optional result limit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Literal keyword or phrase to find")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
    return parser.parse_args()


def main() -> int:
    """Run a query and print its source-aware results."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    results = search_chunks(args.query, args.database, args.limit)
    print(f"QUERY: {args.query!r} | RESULTS: {len(results)}")
    for index, result in enumerate(results, start=1):
        print(
            f"{index}. {result.doc_id} | {result.title} | page {result.page}\n"
            f"   {result.text_snippet}\n"
            f"   {result.source_url}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
