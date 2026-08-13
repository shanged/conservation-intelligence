"""Reusable local semantic retrieval for the Conservation prototype."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from runtime_artifacts import (
    DATABASE_PATH,
    MODEL_PATH,
    RuntimeArtifactPreparationError,
    runtime_vector_index_dir,
)
from search_chunks import make_snippet
from sqlite_readonly import connect_readonly


COLLECTION_NAME = "conservation_chunks"


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
    embedding_window_id: str
    window_text: str
    text_snippet: str
    distance: float
    similarity: float


@lru_cache(maxsize=1)
def load_model() -> SentenceTransformer:
    """Load the local embedding model once per Python process."""
    return SentenceTransformer(
        str(MODEL_PATH),
        local_files_only=True,
    )


def sqlite_records(database_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load normalized titles and original chunk text from SQLite."""
    if not database_path.exists():
        raise VectorIndexNotFoundError(
            f"Precomputed SQLite database not found: {database_path}."
        )
    with connect_readonly(database_path) as connection:
        titles = dict(connection.execute("SELECT doc_id, title FROM documents").fetchall())
        chunks = dict(connection.execute("SELECT chunk_id, chunk_text FROM chunks").fetchall())
    return titles, chunks


def semantic_search(
    query: str,
    top_k: int = 5,
    *,
    database_path: str | Path = DATABASE_PATH,
    vector_index_dir: str | Path | None = None,
) -> list[SemanticSearchResult]:
    """Embed a query and return the nearest Chroma chunks by cosine distance."""
    query = query.strip()
    if not query:
        return []
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    database_path = Path(database_path)
    if vector_index_dir is None:
        try:
            vector_index_dir = runtime_vector_index_dir()
        except RuntimeArtifactPreparationError as exc:
            raise VectorIndexNotFoundError(str(exc)) from None
    vector_index_dir = Path(vector_index_dir)
    if not (vector_index_dir / "chroma.sqlite3").exists():
        raise VectorIndexNotFoundError(
            f"Precomputed semantic index not found: {vector_index_dir}."
        )

    settings = Settings(anonymized_telemetry=False, migrations="validate")
    with chromadb.PersistentClient(path=str(vector_index_dir), settings=settings) as client:
        try:
            collection = client.get_collection(COLLECTION_NAME)
        except Exception as exc:
            raise VectorIndexNotFoundError(
                "The precomputed semantic collection is unavailable in the runtime copy."
            ) from exc

        available = collection.count()
        if available == 0:
            return []
        query_embedding = load_model().encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        ).tolist()
        titles, original_chunks = sqlite_records(database_path)

        # Over-fetch windows and expand if necessary until enough unique original
        # chunks are represented. Only the best-scoring window survives per chunk.
        request_count = min(available, max(50, top_k * 10))
        grouped: dict[str, tuple[str, str, dict[str, object], float]] = {}
        while True:
            response = collection.query(
                query_embeddings=query_embedding,
                n_results=request_count,
                include=["documents", "metadatas", "distances"],
            )
            grouped.clear()
            for window_id, window_text, metadata, distance in zip(
                response["ids"][0],
                response["documents"][0],
                response["metadatas"][0],
                response["distances"][0],
                strict=True,
            ):
                original_chunk_id = metadata.get("original_chunk_id")
                if not original_chunk_id:
                    raise VectorIndexNotFoundError(
                        "The packaged semantic index uses an incompatible whole-chunk format."
                    )
                original_chunk_id = str(original_chunk_id)
                numeric_distance = float(distance)
                current = grouped.get(original_chunk_id)
                if current is None or numeric_distance < current[3]:
                    grouped[original_chunk_id] = (
                        window_id,
                        window_text,
                        metadata,
                        numeric_distance,
                    )
            if len(grouped) >= top_k or request_count == available:
                break
            request_count = min(available, request_count * 2)

    ranked = sorted(grouped.items(), key=lambda item: item[1][3])[:top_k]
    results: list[SemanticSearchResult] = []
    for original_chunk_id, (window_id, window_text, metadata, distance) in ranked:
        doc_id = str(metadata["doc_id"])
        results.append(
            SemanticSearchResult(
                chunk_id=original_chunk_id,
                doc_id=doc_id,
                title=titles.get(doc_id, doc_id),
                page=str(metadata["page"]),
                source_url=str(metadata["source_url"]),
                chunk_text=original_chunks.get(original_chunk_id, window_text),
                embedding_window_id=window_id,
                window_text=window_text,
                text_snippet=make_snippet(window_text, query),
                distance=distance,
                similarity=1.0 - distance,
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
            f"{result.chunk_id} | "
            f"similarity {result.similarity:.4f}\n"
            f"   {result.text_snippet}\n"
            f"   {result.source_url}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
