"""Reusable local semantic retrieval for the Conservation prototype."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from search_chunks import make_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "db" / "conservation.db"
VECTOR_INDEX_DIR = PROJECT_ROOT / "db" / "vector_index"
MODEL_CACHE_DIR = VECTOR_INDEX_DIR / "model_cache"
COLLECTION_NAME = "conservation_chunks"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class VectorIndexNotFoundError(RuntimeError):
    """Raised when semantic search is requested before the index is built."""


@dataclass(frozen=True)
class SemanticSearchResult:
    """A semantic match with normalized source and scoring information."""

    chunk_id: str
    doc_id: str
    title: str
    page: str
    source_url: str
    chunk_text: str
    text_snippet: str
    distance: float
    similarity: float


@lru_cache(maxsize=1)
def load_model() -> SentenceTransformer:
    """Load the local embedding model once per Python process."""
    return SentenceTransformer(
        MODEL_NAME,
        cache_folder=str(MODEL_CACHE_DIR),
        local_files_only=True,
    )


def document_titles(database_path: Path) -> dict[str, str]:
    """Load normalized document titles from SQLite."""
    if not database_path.exists():
        raise VectorIndexNotFoundError(
            f"SQLite database not found: {database_path}. Run 03_build_chunks.py first."
        )
    with sqlite3.connect(database_path) as connection:
        return dict(connection.execute("SELECT doc_id, title FROM documents").fetchall())


def semantic_search(
    query: str,
    top_k: int = 5,
    *,
    database_path: str | Path = DATABASE_PATH,
    vector_index_dir: str | Path = VECTOR_INDEX_DIR,
) -> list[SemanticSearchResult]:
    """Embed a query and return the nearest Chroma chunks by cosine distance."""
    query = query.strip()
    if not query:
        return []
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    database_path = Path(database_path)
    vector_index_dir = Path(vector_index_dir)
    if not (vector_index_dir / "chroma.sqlite3").exists():
        raise VectorIndexNotFoundError(
            "Semantic index not found. Run scripts/04_build_vector_index.py first."
        )

    client = chromadb.PersistentClient(path=str(vector_index_dir))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise VectorIndexNotFoundError(
            "Semantic collection not found. Run scripts/04_build_vector_index.py first."
        ) from exc

    available = collection.count()
    if available == 0:
        return []
    query_embedding = load_model().encode(
        [query], normalize_embeddings=True, show_progress_bar=False
    ).tolist()
    response = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, available),
        include=["documents", "metadatas", "distances"],
    )
    titles = document_titles(database_path)

    ids = response["ids"][0]
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    distances = response["distances"][0]
    results: list[SemanticSearchResult] = []
    for chunk_id, text, metadata, distance in zip(
        ids, documents, metadatas, distances, strict=True
    ):
        doc_id = str(metadata["doc_id"])
        numeric_distance = float(distance)
        results.append(
            SemanticSearchResult(
                chunk_id=chunk_id,
                doc_id=doc_id,
                title=titles.get(doc_id, doc_id),
                page=str(metadata["page"]),
                source_url=str(metadata["source_url"]),
                chunk_text=text,
                text_snippet=make_snippet(text, query),
                distance=numeric_distance,
                similarity=1.0 - numeric_distance,
            )
        )
    return results


def parse_args() -> argparse.Namespace:
    """Parse a semantic query and requested result count."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5, choices=(3, 5, 10))
    return parser.parse_args()


def main() -> int:
    """Run semantic search from the command line."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    try:
        results = semantic_search(args.query, args.top_k)
    except VectorIndexNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"QUERY: {args.query!r} | RESULTS: {len(results)}")
    for index, result in enumerate(results, start=1):
        print(
            f"{index}. {result.doc_id} | {result.title} | page {result.page} | "
            f"similarity {result.similarity:.4f}\n"
            f"   {result.text_snippet}\n"
            f"   {result.source_url}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
